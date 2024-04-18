import re
from typing import List, Tuple



def split_message(msg: str, *, with_photo: bool) -> list[str]:
    """
    Разделяет текст на части с учетом лимитов телеграмма
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
            # Отсекаем часть сообщения максимальной длины от `msg`
            # и ищем позицию для разрыва по символу новой строки.
            part = msg[:max_msg_length]
            first_ln = part.rfind('\n')

            if first_ln != -1:
                # Нашли символ новой строки. Разрываем сообщение по нему, исключая сам символ.
                new_part = part[:first_ln]
                parts.append(new_part)
                # Обрезаем `msg` до длины новой части
                # и удаляем символ новой строки.
                msg = msg[first_ln + 1:]
            else:
                # В части сообщения не нашлось новой строки.
                # Попробуем найти хотя бы пробел для разрыва.
                first_space = part.rfind(' ')

                if first_space != -1:
                    # Нашли пробел. Разрываем сообщение по нему, исключая сам пробел.
                    new_part = part[:first_space]
                    parts.append(new_part)
                    # Обрезаем `msg` до длины новой части
                    # и удаляем пробел.
                    msg = msg[first_space + 1:]
                else:
                    # В части сообщения не нашлось подходящего места для разрыва.
                    # Просто добавляем текущую часть и обрезаем сообщение
                    # на её длину.
                    parts.append(part)
                    msg = msg[max_msg_length:]
    return parts



def close_tags(
    html: str,
    open_tags: List[str] = None
) -> Tuple[str, List[str]]:
    """
    Закрывает все открывающиеся теги
    Добавляет пропущенные открывающие теги
    """
    # Паттерн для поиска тегов с учетом атрибутов
    tag_pattern = re.compile(r'<(/?)(\w+)([^>]*)>')
    open_stack = []
    close_queue = []
    close_open_tags = []

    for tag in tag_pattern.finditer(html):
        is_closing_tag = tag.group(1) == '/'
        tag_name = tag.group(2)
        tag_atr = tag.group(3)

        if not is_closing_tag:
            # Если это открывающий тег, поместим его в стек
            open_stack.insert(0, tag_name)
            close_open_tags.append(f"<{tag_name}{tag_atr}>")

        elif open_stack and open_stack[0] == tag_name:
            # Если это закрывающий тег и последний открывающий тег в стеке соответствует текущему закрывающему тегу, удаляем его из стека
            open_stack.pop(0)
            
        else:
            # Если закрывающий тег не имеет открывающего, добавим его в очередь
            close_queue.append(tag_name)

    # Закроем все незакрытые теги
    for tag_name in open_stack:
        html += '</' + tag_name + '>'
    
    if open_tags:
        html = "".join(open_tags) + html
    else:
        # Откроем все неоткрытые теги
        for tag_name in close_queue:
            html = '<' + tag_name + '>' + html

    return html, close_open_tags[-len(open_stack):]



def split_message_with_tags(
    text: str,
    with_photo: bool = False
) -> list[str]:
    """
    Разделяет текст на части с учетом тегов.
    """
    result = split_message(msg = text, with_photo=with_photo)

    result_parts = []
    open_tags = None
    for part in result:
        text, open_tags = close_tags(part, open_tags)
        result_parts.append(text)

    return result_parts