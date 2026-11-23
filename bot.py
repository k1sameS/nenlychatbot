import asyncio
import os
import json
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ChatType

# Берем токен из секретов GitHub
BOT_TOKEN = os.environ.get("BOT_TOKEN")
NICKS_FILE = "nicks.json"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def load_nicks():
    if os.path.exists(NICKS_FILE):
        try:
            with open(NICKS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_nicks(data):
    with open(NICKS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@dp.message(Command("snick"))
async def cmd_snick(message: Message):
    if message.chat.type == ChatType.PRIVATE:
        return await message.reply("❌ Команда работает только в группах.")

    text = message.text or ""
    clean_text = text.replace("/snick", "").strip()
    args = clean_text.split(maxsplit=1)

    target_id = None
    target_name = ""
    new_nick = ""

    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
        target_id = str(target_user.id)
        target_name = target_user.first_name or target_user.username or "Пользователь"
        if not clean_text:
            return await message.reply("❌ Необходимо указать никнейм.\nПример: `/snick Дуров`", parse_mode="Markdown")
        new_nick = clean_text
    else:
        if len(args) < 2:
            return await message.reply("❌ Необходимо указать никнейм.\n\nПример: `/snick id1 Дуров`.\n\nЛибо прикрепите сообщение человека: `/snick Дуров`.")
        target_id = args[0]
        target_name = args[0]
        new_nick = args[1].strip()

    if len(new_nick) > 16:
        return await message.reply("❌ Ник слишком длинный. Telegram разрешает максимум 16 символов.")

    try:
        user_id_for_api = int(target_id) if target_id.isdigit() else target_id
        await bot.set_chat_administrator_custom_title(
            chat_id=message.chat.id,
            user_id=user_id_for_api,
            custom_title=new_nick
        )
    except Exception:
        pass # Игнорируем, если не получилось поставить визуально

    nicks = load_nicks()
    nicks[str(target_id)] = {"name": target_name, "nick": new_nick}
    save_nicks(nicks)

    admin_name = message.from_user.first_name or "Админ"
    if target_id.isdigit():
        target_name_html = f'<a href="tg://user?id={target_id}">{target_name}</a>'
    else:
        target_name_html = target_name

    final_msg = f'<a href="tg://user?id={message.from_user.id}">{admin_name}</a> установил никнейм {target_name_html}: <b>{new_nick}</b>'
    await message.reply(final_msg, parse_mode="HTML")

@dp.message(Command("nlist"))
async def cmd_nlist(message: Message):
    nicks = load_nicks()
    if not nicks:
        return await message.reply("📭 Список ников пуст.")

    msg = "📋 <b>Список установленных ников:</b>\n\n"
    count = 1
    for target_id, data in nicks.items():
        name = data.get("name", "Пользователь")
        nick = data.get("nick", "—")
        
        if target_id.isdigit():
            name_html = f'<a href="tg://user?id={target_id}">{name}</a>'
        else:
            name_html = name
            
        msg += f"{count}. {name_html} - {nick}\n"
        count += 1

        if len(msg) > 3500:
            await message.reply(msg, parse_mode="HTML")
            msg = ""

    if msg:
        await message.reply(msg, parse_mode="HTML")

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
