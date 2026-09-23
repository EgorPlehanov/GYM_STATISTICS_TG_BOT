"""Проверки тестовых Rich HTML сообщений редиректа тренировки."""

from html.parser import HTMLParser
from types import SimpleNamespace
from unittest.mock import AsyncMock

from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import SendRichMessage
from aiogram.types import InputRichMessage

from app.bot.formatters.training_previews import RichFormat, build_training_previews
from app.bot.handlers import main_admin


class RedirectTargetsApiClient:
    """Заглушка internal API-клиента для команды макетов редиректа."""

    def __init__(self, redirect_group_ids: list[int]) -> None:
        self.get_redirect_group_ids = AsyncMock(return_value=redirect_group_ids)

    async def __aenter__(self) -> "RedirectTargetsApiClient":
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None


class BalancedHtmlParser(HTMLParser):
    """Ловит незакрытые теги в HTML-макетах."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        assert self.stack.pop() == tag


def test_previews_cover_redirect_rich_html_variants() -> None:
    previews = build_training_previews()

    assert len(previews) == 8
    assert all(preview.rich_format == RichFormat.HTML for preview in previews)
    assert all("Редирект" in preview.title for preview in previews)

    for preview in previews:
        assert len(preview.text) < 4096
        assert "<h4>" in preview.text
        assert "<h2>" not in preview.text
        assert "<h3>" not in preview.text
        assert "<h5>" not in preview.text
        assert 'href="tg://user?id=' in preview.text
        assert preview.text.index('href="tg://user?id=') < preview.text.index(" · ")
        assert (
            "<table bordered striped compact>" in preview.text
            or "<ul>" in preview.text
            or "<ol>" in preview.text
        )
        assert "<footer>" in preview.text

    assert any("<blockquote>" in preview.text for preview in previews)
    assert any("<h4>" in preview.text for preview in previews)
    assert any("<aside>" in preview.text for preview in previews)
    assert any("<details>" in preview.text for preview in previews)
    assert any("<mark>" in preview.text for preview in previews)
    assert any("<ul>" in preview.text for preview in previews)
    assert any("<ol>" in preview.text for preview in previews)
    assert any("<sup>↑</sup>" in preview.text for preview in previews)
    assert any("<sub>↓</sub>" in preview.text for preview in previews)
    assert sum("<cite><a href=" in preview.text for preview in previews) == 2
    assert any(
        "<footer>2 упражнения · 5 подходов · @egor_plehanov</footer>" in preview.text
        for preview in previews
    )
    assert any(
        "<details><summary>Плечо немного тянет на жиме...</summary>"
        "Поэтому снизила вес и работала без рывков. @egor_plehanov</details>" in preview.text
        for preview in previews
    )
    assert sum(
        preview.text.index("</table>") < preview.text.index("<blockquote>")
        for preview in previews
        if "</table>" in preview.text and "<blockquote>" in preview.text
    ) == 1
    assert sum(
        preview.text.index("</table>") < preview.text.index("<details>")
        for preview in previews
        if "<details>" in preview.text
    ) == 1

    for preview in previews:
        parser = BalancedHtmlParser()
        parser.feed(preview.text)
        parser.close()
        assert not parser.stack


async def test_training_designs_sends_each_message_to_each_redirect_group(monkeypatch) -> None:
    api_client = RedirectTargetsApiClient(redirect_group_ids=[-1001, -1002])
    monkeypatch.setattr(main_admin, "BotApiClient", lambda: api_client)
    message = SimpleNamespace(
        answer=AsyncMock(),
        bot=SimpleNamespace(send_rich_message=AsyncMock()),
        chat=SimpleNamespace(id=123),
        from_user=SimpleNamespace(id=409218520),
    )

    await main_admin.training_designs(message)

    assert message.answer.await_count == 0
    api_client.get_redirect_group_ids.assert_awaited_once_with(409218520)
    assert message.bot.send_rich_message.await_count == 16
    for call in message.bot.send_rich_message.await_args_list:
        assert call.kwargs["chat_id"] in {-1001, -1002}
        rich_message = call.kwargs["rich_message"]
        assert isinstance(rich_message, InputRichMessage)
        assert rich_message.html is not None
        assert rich_message.markdown is None


async def test_training_designs_notifies_when_redirect_is_not_configured(monkeypatch) -> None:
    api_client = RedirectTargetsApiClient(redirect_group_ids=[])
    monkeypatch.setattr(main_admin, "BotApiClient", lambda: api_client)
    message = SimpleNamespace(
        answer=AsyncMock(),
        bot=SimpleNamespace(send_rich_message=AsyncMock()),
        chat=SimpleNamespace(id=123),
        from_user=SimpleNamespace(id=409218520),
    )

    await main_admin.training_designs(message)

    message.bot.send_rich_message.assert_not_awaited()
    message.answer.assert_awaited_once_with("⚠️ Нет групп с включенным редиректом.")


async def test_rich_api_failure_does_not_hide_other_examples(monkeypatch) -> None:
    method = SendRichMessage(
        chat_id=123,
        rich_message=InputRichMessage(html="<h2>Тест</h2>"),
    )
    api_client = RedirectTargetsApiClient(redirect_group_ids=[-1001])
    monkeypatch.setattr(main_admin, "BotApiClient", lambda: api_client)
    message = SimpleNamespace(
        answer=AsyncMock(),
        bot=SimpleNamespace(
            send_rich_message=AsyncMock(
                side_effect=TelegramBadRequest(method=method, message="unsupported method")
            )
        ),
        chat=SimpleNamespace(id=123),
        from_user=SimpleNamespace(id=409218520),
    )

    await main_admin.training_designs(message)

    assert message.bot.send_rich_message.await_count == 8
    assert message.answer.await_count == 8
    assert any(
        "Rich Message не отправлено" in call.kwargs["text"]
        for call in message.answer.await_args_list
    )
