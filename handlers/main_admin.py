from aiogram import Router, F, html
from aiogram.types import Message, PhotoSize, BufferedInputFile
from aiogram.filters import Command, CommandObject

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict

from filters.main_admin import MainAdminFilter
from db.database import async_session_factory
from middlewares import DBSessionMiddleware
from .main_admin_units import *
from utils.plotly_table import get_plotly_table_bytes



router = Router()
router.message.filter(MainAdminFilter())
router.message.middleware(DBSessionMiddleware(async_session_factory))



@router.message(Command("admincmd"))
async def admin_cmd(message: Message):
    await message.answer(
        text=(
            "/check_db_connection - проверить подключение к базе данных\n"
            "/db_monitoring - мониторинг базы данных\n"
        )
    )



@router.message(F.photo[-1].as_("photo"))
async def save_image(message: Message, photo: PhotoSize):
    await message.answer(
        f"photo.file_id:\n{photo.file_id}\n\n"
        f"photo.file_unique_id:\n{photo.file_unique_id}",
    )



@router.message(Command("check_db_connection"))
async def check_db_connection(message: Message):
    try:
        async with async_session_factory() as session:
            result = await session.execute(text("SELECT 1"))
            await message.answer(
                text=(
                    "✅ Подключение к базе данных прошло успешно!\n\n"
                )
            )
    except Exception as e:
        await message.answer(
            text=f"❌ Ошибка подключения к базе данных: {str(e)}"
        )



@router.message(Command("db_monitoring"))
async def db_monitoring(message: Message, command: CommandObject, session: AsyncSession):
    """
    Функции мониторинга базы данных
    """
    filename = None
    if command.args is not None:
        args = command.args.split()
        filename = args[0]
        args = args[1:] 

    file_datas: Dict[str, FileData] = get_db_monitoring_sql_queries(current_filename=filename)

    if filename is None:
        commands_list = [
            html.blockquote(f"🔧 {html.bold(file_data.name)}\n" + 
            html.code(f"/db_monitoring {file_name}"))
            for file_name, file_data in file_datas.items()
        ]
        commands_text = "\n".join(commands_list)
        await message.answer(
            text=(
                f"🗄️📊 {html.bold(html.underline('Комманды мониторинга базы данных:'))}\n"
                f"{commands_text}"
                f"🍕 Добавьте:\n"
                f"🔹 {html.code('disc')} - чтобы получить описание\n"
                f"🔹 {html.code('sql')} - чтобы получить запрос\n"
            )
        )
        
    else:
        result_text = f"🔧 {html.underline(html.bold(file_datas[filename].name))}\n"
        if 'disc' in args:
            result_text += f"{html.blockquote(file_datas[filename].comment)}\n"
        if 'sql' in args:
            result_text += f"{html.pre_language(html.quote(file_datas[filename].query), 'sql')}\n"
        result_text += (
            f"{html.blockquote(html.code(f'/db_monitoring {filename}'))}\n"
            f"🗄️📊 {html.italic('Список всех комманд мониторинга /db_monitoring')}"
        )
        
        result_query = await session.execute(text(file_datas[filename].query))
        table_photo_buffer = get_plotly_table_bytes(result_query)

        await message.answer_photo(
            photo = BufferedInputFile(
                file = table_photo_buffer,
                filename = f"{file_datas[filename].comment.split('.')[0]}.png"
            ),
            caption = result_text
        )