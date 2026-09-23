"""Проверки тестовых сообщений с ParseMode и Rich Messages."""

from collections import Counter
from html.parser import HTMLParser
from types import SimpleNamespace
from unittest.mock import AsyncMock

from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import SendRichMessage
from aiogram.types import InputRichMessage

from app.bot.formatters.training_previews import RichFormat, build_training_previews
from app.bot.handlers.main_admin import training_designs


class BalancedHtmlParser(HTMLParser):
    """Ловит незакрытые теги в HTML-макетах."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        assert self.stack.pop() == tag


def test_previews_cover_three_parse_modes_and_actual_rich_tables() -> None:
    previews = build_training_previews()

    assert len(previews) == 10
    assert Counter(p.parse_mode for p in previews if p.parse_mode) == {
        ParseMode.HTML: 2,
        ParseMode.MARKDOWN_V2: 2,
        ParseMode.MARKDOWN: 2,
    }
    assert Counter(p.rich_format for p in previews if p.rich_format) == {
        RichFormat.HTML: 2,
        RichFormat.MARKDOWN: 2,
    }
    assert sum("Черновик" in p.title for p in previews) == 5
    assert sum("Редирект" in p.title for p in previews) == 5

    for preview in previews:
        assert (preview.parse_mode is None) != (preview.rich_format is None)
        assert len(preview.text) < 4096

    rich_html = [p.text for p in previews if p.rich_format == RichFormat.HTML]
    assert all("<table bordered striped compact>" in text for text in rich_html)
    assert any("<details>" in text for text in rich_html)
    assert all("| Упражнение |" in p.text for p in previews if p.rich_format == RichFormat.MARKDOWN)
    assert "&lt;осторожно&gt;" in rich_html[0]
    assert "&lt;Тест&gt;" in previews[3].text

    for preview in previews:
        if preview.parse_mode == ParseMode.HTML or preview.rich_format == RichFormat.HTML:
            parser = BalancedHtmlParser()
            parser.feed(preview.text)
            parser.close()
            assert not parser.stack


async def test_training_designs_sends_each_message_through_its_own_api() -> None:
    message = SimpleNamespace(
        answer=AsyncMock(),
        bot=SimpleNamespace(send_rich_message=AsyncMock()),
        chat=SimpleNamespace(id=123),
    )

    await training_designs(message)

    assert message.answer.await_count == 6
    assert message.bot.send_rich_message.await_count == 4
    assert Counter(call.kwargs["parse_mode"] for call in message.answer.await_args_list) == {
        ParseMode.HTML: 2,
        ParseMode.MARKDOWN_V2: 2,
        ParseMode.MARKDOWN: 2,
    }
    for call in message.bot.send_rich_message.await_args_list:
        assert call.kwargs["chat_id"] == 123
        rich_message = call.kwargs["rich_message"]
        assert isinstance(rich_message, InputRichMessage)
        assert (rich_message.html is None) != (rich_message.markdown is None)


async def test_rich_api_failure_does_not_hide_other_examples() -> None:
    method = SendRichMessage(
        chat_id=123,
        rich_message=InputRichMessage(html="<h2>Тест</h2>"),
    )
    message = SimpleNamespace(
        answer=AsyncMock(),
        bot=SimpleNamespace(
            send_rich_message=AsyncMock(
                side_effect=TelegramBadRequest(method=method, message="unsupported method")
            )
        ),
        chat=SimpleNamespace(id=123),
    )

    await training_designs(message)

    assert message.bot.send_rich_message.await_count == 4
    assert message.answer.await_count == 10
    assert any(
        "Rich Message не отправлено" in call.kwargs["text"]
        for call in message.answer.await_args_list
    )
