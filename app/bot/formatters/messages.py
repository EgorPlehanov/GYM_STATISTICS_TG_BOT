import re


def split_message(msg: str, *, with_photo: bool) -> list[str]:
    """Разделяет текст на части с учетом лимитов Telegram Bot API.

    Args:
        msg: исходный текст сообщения.
        with_photo: признак, что первая часть будет отправлена подписью к файлу
            или фотографии. Для caption лимит меньше, чем для обычного сообщения.

    Returns:
        Список частей, каждая из которых укладывается в лимит Telegram.
    """
    parts = []
    while msg:
        # Определение максимальной длины сообщения исходя из
        # `with_photo` и является ли это первой итерацией
        # (фото отправляется только с первым сообщением).
        if parts:
            max_msg_length = 4096
        else:
            if with_photo:
                max_msg_length = 1024
            else:
                max_msg_length = 4096

        if len(msg) <= max_msg_length:
            # Длина сообщения вписывается в максимально допустимую.
            parts.append(msg)
            break
        else:
            part = msg[:max_msg_length]
            first_ln = part.rfind('\n')

            if first_ln != -1:
                new_part = part[:first_ln]
                parts.append(new_part)
                msg = msg[first_ln + 1:]
            else:
                first_space = part.rfind(' ')

                if first_space != -1:
                    new_part = part[:first_space]
                    parts.append(new_part)
                    msg = msg[first_space + 1:]
                else:
                    parts.append(part)
                    msg = msg[max_msg_length:]
    return parts


def close_tags(
    html: str,
    open_tags: list[str] | None = None,
) -> tuple[str, list[str]]:
    """Сохраняет корректность HTML-тегов после разбиения сообщения.

    Telegram может не принять часть сообщения, если HTML-тег был открыт в одной
    части текста, а закрыт уже в другой. Функция закрывает незавершенные теги в
    текущем фрагменте и возвращает список тегов, которые нужно открыть в
    следующем фрагменте.

    Args:
        html: часть сообщения с Telegram HTML-разметкой.
        open_tags: теги, которые были открыты в предыдущей части сообщения и
            должны быть добавлены в начало текущей части.

    Returns:
        Кортеж из исправленного HTML-фрагмента и списка тегов для следующей
        части сообщения.
    """
    tag_pattern = re.compile(r'<(/?)(\w+)([^>]*)>')
    open_stack = []
    close_queue = []
    close_open_tags = []

    for tag in tag_pattern.finditer(html):
        is_closing_tag = tag.group(1) == '/'
        tag_name = tag.group(2)
        tag_atr = tag.group(3)

        if not is_closing_tag:
            open_stack.insert(0, tag_name)
            close_open_tags.append(f"<{tag_name}{tag_atr}>")

        elif open_stack and open_stack[0] == tag_name:
            open_stack.pop(0)

        else:
            close_queue.append(tag_name)

    for tag_name in open_stack:
        html += '</' + tag_name + '>'

    if open_tags:
        html = "".join(open_tags) + html
    else:
        for tag_name in close_queue:
            html = '<' + tag_name + '>' + html

    return html, close_open_tags[-len(open_stack):]


def split_message_with_tags(
    text: str,
    with_photo: bool = False,
) -> list[str]:
    """Разделяет Telegram HTML-сообщение на части с сохранением валидной разметки.

    Args:
        text: исходный текст сообщения с Telegram HTML-разметкой.
        with_photo: признак, что первая часть будет отправлена как caption.

    Returns:
        Список частей сообщения, безопасных для последовательной отправки.
    """
    result = split_message(msg=text, with_photo=with_photo)

    result_parts = []
    open_tags = None
    for part in result:
        text, open_tags = close_tags(part, open_tags)
        result_parts.append(text)

    return result_parts

