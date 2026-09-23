"""Тестовые сообщения тренировки для разных режимов форматирования Telegram."""

from dataclasses import dataclass
from enum import Enum

from aiogram.enums import ParseMode


class RichFormat(str, Enum):
    """Синтаксис отдельного метода Bot API sendRichMessage."""

    HTML = "html"
    MARKDOWN = "markdown"


@dataclass(frozen=True, slots=True)
class TrainingPreview:
    """Одно сообщение с вымышленными данными и явным режимом отправки."""

    title: str
    text: str
    parse_mode: ParseMode | None = None
    rich_format: RichFormat | None = None


def build_training_previews() -> tuple[TrainingPreview, ...]:
    """Сравнивает три ParseMode и настоящие Rich Messages на сценариях тренировки."""
    return (
        TrainingPreview(
            "Черновик · HTML",
            "🧪 <b>HTML · черновик</b>\n"
            "<i>21.09.2026 · верх тела</i>\n\n"
            "<b>Жим лёжа</b>\n"
            "<blockquote>1 · 60 кг × 10\n2 · 65 кг × 8\n3 · 65 кг × 8</blockquote>\n"
            "<b>Тяга гантели</b>\n"
            "<blockquote>1 · 24 кг × 12\n2 · 24 кг × 10</blockquote>\n"
            "<u>5 подходов</u> · добавить ещё или завершить?",
            parse_mode=ParseMode.HTML,
        ),
        TrainingPreview(
            "Черновик · MarkdownV2",
            "🧪 *MarkdownV2 · черновик*\n"
            "_21\\.09\\.2026 · верх тела_\n\n"
            "*Жим лёжа*\n"
            ">1 · 60 кг × 10\n>2 · 65 кг × 8\n>3 · 65 кг × 8\n"
            "*Тяга гантели*\n"
            ">1 · 24 кг × 12\n>2 · 24 кг × 10\n"
            "__5 подходов__ · добавить ещё или завершить?",
            parse_mode=ParseMode.MARKDOWN_V2,
        ),
        TrainingPreview(
            "Черновик · Markdown",
            "🧪 *Markdown · черновик*\n"
            "_21.09.2026 · верх тела_\n\n"
            "*Жим лёжа*\n"
            "`1 · 60 кг × 10`\n`2 · 65 кг × 8`\n`3 · 65 кг × 8`\n"
            "*Тяга гантели*\n"
            "`1 · 24 кг × 12`\n`2 · 24 кг × 10`\n"
            "5 подходов · добавить ещё или завершить?",
            parse_mode=ParseMode.MARKDOWN,
        ),
        TrainingPreview(
            "Редирект · HTML",
            "🧪 <b>HTML · результат для группы</b>\n"
            "<b>Маша &lt;Тест&gt; &amp; Co</b> · 21.09.2026\n\n"
            "<b>Жим лёжа</b>\n"
            "<blockquote>60×10 · 65×8 × 2</blockquote>\n"
            "<b>Тяга гантели</b>\n"
            "<blockquote>24×12 · 24×10</blockquote>\n"
            "<i>2 упражнения · 5 подходов</i>",
            parse_mode=ParseMode.HTML,
        ),
        TrainingPreview(
            "Редирект · MarkdownV2",
            "🧪 *MarkdownV2 · результат для группы*\n"
            "*Маша <Тест\\> & Co* · 21\\.09\\.2026\n\n"
            "*Жим лёжа*\n"
            ">60×10 · 65×8 × 2\n"
            "*Тяга гантели*\n"
            ">24×12 · 24×10\n"
            "_2 упражнения · 5 подходов_",
            parse_mode=ParseMode.MARKDOWN_V2,
        ),
        TrainingPreview(
            "Редирект · Markdown",
            "🧪 *Markdown · результат для группы*\n"
            "*Маша <Тест> & Co* · 21.09.2026\n\n"
            "*Жим лёжа*\n"
            "`60×10 · 65×8 × 2`\n"
            "*Тяга гантели*\n"
            "`24×12 · 24×10`\n"
            "_2 упражнения · 5 подходов_",
            parse_mode=ParseMode.MARKDOWN,
        ),
        TrainingPreview(
            "Черновик · Rich Markdown · большая тренировка",
            "# 🧪 Rich Markdown · черновик\n\n"
            "23.09.2026 · **Ноги и спина**\n\n"
            "| Упражнение | Подходы | Последний |\n"
            "|:--|--:|--:|\n"
            "| Приседания | 4 | 90 кг × 6 |\n"
            "| Румынская тяга | 4 | 80 кг × 8 |\n"
            "| Выпады | 3 | 20 кг × 10 |\n"
            "| Планка | 4 | 45 сек |\n\n"
            "- [x] Выбрана дата\n"
            "- [x] Добавлены упражнения\n"
            "- [ ] Завершить тренировку\n\n"
            "<details><summary>Все подходы приседаний</summary>"
            "60×10 · 80×8 · 90×6 · 90×6</details>",
            rich_format=RichFormat.MARKDOWN,
        ),
        TrainingPreview(
            "Черновик · Rich HTML · правка подхода",
            "<h2>🧪 Rich HTML · правка черновика</h2>"
            "<p>22.09.2026 · <mark>Подход 2 изменён</mark></p>"
            "<table bordered striped compact>"
            "<caption>Приседания со штангой</caption>"
            "<tr><th>№</th><th>Вес</th><th>Повторы</th></tr>"
            "<tr><td>1</td><td>80 кг</td><td>8</td></tr>"
            "<tr><td>2</td><td><s>85</s> → <b>82,5 кг</b></td><td><b>8</b></td></tr>"
            "<tr><td>3</td><td>85 кг</td><td>6</td></tr>"
            "</table>"
            "<details><summary>Комментарий к тренировке</summary>"
            "Плечо тянет на жиме &lt;осторожно&gt;, без рывков &amp; рекордов"
            "</details>"
            "<footer>Проверьте изменения перед сохранением</footer>",
            rich_format=RichFormat.HTML,
        ),
        TrainingPreview(
            "Редирект · Rich Markdown · лесенка весов",
            "# 🧪 Rich Markdown · результат\n\n"
            "**Ирина** · 23.09.2026\n\n"
            "| Упражнение | Разминка | Рабочие подходы |\n"
            "|:--|:--|:--|\n"
            "| Становая тяга | 40×10 | 60×8 → 70×6 → 75×4 |\n"
            "| Жим гантелей | 14×12 | 16×10 → 16×9 |\n\n"
            "> Плечо тянет на жиме, без рывков и рекордов.\n\n"
            "---\n"
            "**Итого:** 2 упражнения · 6 подходов",
            rich_format=RichFormat.MARKDOWN,
        ),
        TrainingPreview(
            "Редирект · Rich HTML · без веса",
            "<h2>🧪 Rich HTML · результат</h2>"
            "<p><b>Алексей</b> · 22.09.2026 · собственный вес</p>"
            "<table bordered striped compact>"
            "<caption>Повторы по подходам</caption>"
            "<tr><th>Упражнение</th><th>1</th><th>2</th><th>3</th></tr>"
            "<tr><td>Подтягивания</td><td>10</td><td>8</td><td>7</td></tr>"
            "<tr><td>Отжимания</td><td>20</td><td>18</td><td>16</td></tr>"
            "<tr><td>Планка, сек</td><td>60</td><td>45</td><td>—</td></tr>"
            "</table>"
            "<aside>Лёгкая тренировка после дороги.</aside>"
            "<footer>3 упражнения · 8 подходов</footer>",
            rich_format=RichFormat.HTML,
        ),
    )
