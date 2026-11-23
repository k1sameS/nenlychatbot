import asyncio
import json
import os
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ChatType

# --- НАСТРОЙКИ ---
BOT_TOKEN = "9116954783:AAEMLXT4MkRfG-PbsN8_YI1gDk7fs1vqprM"
NICKS_FILE = "nicks.json"

# --- ЛОГИРОВАНИЕ ---
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Глобальная переменная для хранения ников
memory_nicks = {}

def load_nicks():
    global memory_nicks
    if os.path.exists(NICKS_FILE):
        try:
            with open(NICKS_FILE, "r", encoding="utf-8") as f:
                memory_nicks = json.load(f)
        except Exception as e:
            logging.error(f"Ошибка чтения файла: {e}")
    return memory_nicks

def save_nicks(data):
    global memory_nicks
    memory_nicks = data
    try:
        with open(NICKS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Ошибка записи файла: {e}.")

# Загружаем при старте
load_nicks()

# --- КОМАНДА /snick ---
@dp.message(Command("snick"))
async def cmd_snick(message: Message):
    if message.chat.type == ChatType.PRIVATE:
        return await message.reply("❌ Команда работает только в группах.")

    text = message.text or ""
    clean_text = text.replace("/snick", "").strip()
    
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
        args = clean_text.split(maxsplit=1)
        if len(args) < 2:
            error_text = (
                "❌ Необходимо указать никнейм.\n\n"
                "Пример: `/snick id1 Дуров`.\n\n"
                "Либо прикрепите сообщение человека, которому хотите дать никнейм и укажите его: `/snick Дуров`.\n\n"
                "Для выдачи ника `/snick *Юз типа котору надо выдать ник* *Ник*`"
            )
            return await message.reply(error_text, parse_mode="Markdown")
        
        target_id = args[0]
        target_name = args[0]
        new_nick = args[1].strip()

    if len(new_nick) > 32:
        return await message.reply("❌ Ник слишком длинный (макс. 32 символа).")

    # Пытаемся установить визуально (титул)
    try:
        user_id_for_api = int(target_id) if target_id.isdigit() else target_id
        await bot.set_chat_administrator_custom_title(
            chat_id=message.chat.id,
            user_id=user_id_for_api,
            custom_title=new_nick
        )
    except Exception as e:
        logging.warning(f"Не удалось установить титул (ошибка TG): {e}")

    # Сохраняем в базу
    nicks = load_nicks()
    nicks[str(target_id)] = {
        "name": target_name,
        "nick": new_nick
    }
    save_nicks(nicks)

    # Делаем имена кликабельными через tg://user?id=
    admin_id = message.from_user.id
    admin_name = message.from_user.first_name or message.from_user.username or "Админ"
    
    # Если цель - это ID (цифры), делаем кликабельной, если @username - оставляем как есть
    if target_id.isdigit():
        target_name_html = f'<a href="tg://user?id={target_id}">{target_name}</a>'
    else:
        target_name_html = target_name

    final_msg = f'<a href="tg://user?id={admin_id}">{admin_name}</a> установил никнейм {target_name_html}: <b>{new_nick}</b>'
    
    await message.reply(final_msg, parse_mode="HTML")

# --- КОМАНДА /nlist ---
@dp.message(Command("nlist"))
async def cmd_nlist(message: Message):
    nicks = memory_nicks
    
    if not nicks:
        return await message.reply("📭 Список ников пуст.")

    msg_text = "📋 <b>Список установленных ников:</b>\n\n"
    count = 1
    
    for target_id, data in nicks.items():
        name = data.get("name", "Пользователь")
        nick = data.get("nick", "—")
        
        # Делаем имя кликабельным, если это ID
        if target_id.isdigit():
            name_html = f'<a href="tg://user?id={target_id}">{name}</a>'
        else:
            name_html = name
            
        msg_text += f"{count}. {name_html} — <b>{nick}</b>\n"
        count += 1

        # Если сообщение слишком длинное, отправляем частями
        if len(msg_text) > 3500:
            await message.reply(msg_text, parse_mode="HTML")
            msg_text = ""
            count = 1 # Сбрасываем нумерацию для следующего сообщения (или можно продолжить, если хотите)

    if msg_text:
        await message.reply(msg_text, parse_mode="HTML")

# --- ЗАПУСК ---
async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
