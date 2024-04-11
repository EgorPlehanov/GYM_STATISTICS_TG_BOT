from pyrogram import Client

from config_reader import config



async def get_chat_members(chat_id):
    """
    Возвращает список id участников чата
    """
    app = Client(
        name      = config.TG_BOT_USERNAME,
        # api_id    = api_id, 
        # api_hash  = api_hash, 
        bot_token = config.TG_BOT_TOKEN.get_secret_value(),
        in_memory = True,
    )

    await app.start()

    chat_members = []
    async for member in app.get_chat_members(chat_id):
        print(member)
        chat_members = chat_members.append(member.user.id)

    await app.stop()
    return chat_members