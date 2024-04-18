import traceback
from aiogram import Bot, Router, F, html
from aiogram.types import (
    ErrorEvent,
    BufferedInputFile,
    Message,
    ChatBoostRemoved,
    ChatBoostUpdated,
    ChatJoinRequest,
    ChatMemberUpdated,
    ChosenInlineResult,
    InlineQuery,
    MessageReactionCountUpdated,
    MessageReactionUpdated,
    Poll,
    PollAnswer,
    PreCheckoutQuery,
    ShippingQuery,
    CallbackQuery
)

import traceback
from io import BytesIO

from config_reader import config



router = Router()



# @router.error(ExceptionTypeFilter(MyCustomException), F.update.message.as_("message"))
# async def handle_my_custom_exception(event: ErrorEvent, message: Message):
#     # do something with error
#     await message.answer("Oops, something went wrong!")



@router.error()
async def error_handler(event: ErrorEvent):
    """
    Обработчик всех ошибок
    """
    # obj = None
    # match event.update.event_type:
    #     case "message":
    #         obj: Message = event.update.message
    #     case "edited_message":
    #         obj: Message = event.update.edited_message
    #     case "channel_post":
    #         obj: Message = event.update.channel_post
    #     case "edited_channel_post":
    #         obj: Message = event.update.edited_channel_post
    #     case "inline_query":
    #         obj: InlineQuery = event.update.inline_query
    #     case "chosen_inline_result":
    #         obj: ChosenInlineResult = event.update.chosen_inline_result
    #     case "callback_query":
    #         obj: CallbackQuery = event.update.callback_query
    #     case "shipping_query":
    #         obj: ShippingQuery = event.update.shipping_query
    #     case "pre_checkout_query":
    #         obj: PreCheckoutQuery = event.update.pre_checkout_query
    #     case "poll":
    #         obj: Poll = event.update.poll
    #     case "poll_answer":
    #         obj: PollAnswer = event.update.poll_answer
    #     case "my_chat_member":
    #         obj: ChatMemberUpdated = event.update.my_chat_member
    #     case "chat_member":
    #         obj: ChatMemberUpdated = event.update.chat_member
    #     case "chat_join_request":
    #         obj: ChatJoinRequest = event.update.chat_join_request
    #     case "message_reaction":
    #         obj: MessageReactionUpdated = event.update.message_reaction
    #     case "message_reaction_count":
    #         obj: MessageReactionCountUpdated = event.update.message_reaction_count
    #     case "chat_boost":
    #         obj: ChatBoostUpdated = event.update.chat_boost
    #     case "removed_chat_boost":
    #         obj: ChatBoostRemoved = event.update.removed_chat_boost

    obj_by_event_type = {
        "message":event.update.message,
        "edited_message":event.update.edited_message,
        "channel_post":event.update.channel_post,
        "edited_channel_post":event.update.edited_channel_post,
        "inline_query":event.update.inline_query,
        "chosen_inline_result":event.update.chosen_inline_result,
        "callback_query":event.update.callback_query,
        "shipping_query":event.update.shipping_query,
        "pre_checkout_query": event.update.pre_checkout_query,
        "poll": event.update.poll,
        "poll_answer": event.update.poll_answer,
        "my_chat_member": event.update.my_chat_member,
        "chat_member": event.update.chat_member,
        "chat_join_request": event.update.chat_join_request,
        "message_reaction": event.update.message_reaction,
        "message_reaction_count": event.update.message_reaction_count,
        "chat_boost": event.update.chat_boost,
        "removed_chat_boost": event.update.removed_chat_boost,
    }
    obj = obj_by_event_type.get(event.update.event_type)

    bot: Bot = obj.bot
    if bot is not None:
        if obj.chat.id == config.MAIN_ADMIN_ID.get_secret_value():
            await bot.send_message(
                chat_id = obj.chat.id,
                text=(
                    f"❗ При обрабтке события {event.update.event_type} произошла ошибка :\n\n"
                    f"{event.exception}\n\n"
                    f"❗ Пожалуйста сделайте скриншот и опишите администратору контекст в котором произошла ошибка"
                )
            )

        exception_text = (
                f"{html.bold('Произошла при обрабтке события:')}\n"
                f"{html.blockquote(html.quote(event.update.event_type))}\n"
                f"{html.bold('Тип ошибки:')}\n"
                f"{html.blockquote(html.code(html.quote(str(type(event.exception)))))}\n"
                f"{html.bold('Ошибка:')}\n"
                f"{html.blockquote(html.code(html.quote(str(event.exception))))}\n"
        )
        if event.exception.args:
            exception_text += (
                f"{html.bold('Аргументы:')}\n"
                f"{html.blockquote(html.code(html.quote(str(event.exception.args))))}\n"
            )

        traceback_str = traceback.format_exc()
        buffer = BytesIO()
        buffer.write(traceback_str.encode())
        buffer.seek(0)
        traceback_buffer = buffer.getvalue()

        await bot.send_document(
            chat_id = config.MAIN_ADMIN_ID.get_secret_value(),
            document = BufferedInputFile(
                file = traceback_buffer,
                filename = "traceback.txt"
            ),
            caption = (
                "❗❗❗❗❗\n"
                f"{exception_text}"
                "❗❗❗❗❗"
            )
        )