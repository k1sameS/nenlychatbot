# Получаем текст сообщения
text_lower = text.lower().strip()

# ==========================================
# КОМАНДА /snick (Выдача ника)
# ==========================================
if text_lower.startswith("/snick"):
    clean_text = text[6:].strip() # Отрезаем "/snick"
    args = clean_text.split(maxsplit=1)
    
    target_id = None
    target_name = ""
    new_nick = ""

    # Если ответом на сообщение
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
        target_id = str(target_user.id)
        target_name = target_user.first_name or target_user.username or "Пользователь"
        if not clean_text:
            bot.replyText(u, "❌ Необходимо указать никнейм.\nПример: /snick Дуров")
            return
        new_nick = clean_text
    else:
        # Если текстом
        if len(args) < 2:
            bot.replyText(u, "❌ Необходимо указать никнейм.\n\nПример: /snick @username Ник")
            return
        target_id = args[0]
        target_name = args[0]
        new_nick = args[1].strip()

    # Ограничение длины
    if len(new_nick) > 16:
        bot.replyText(u, "❌ Ник слишком длинный. Telegram разрешает максимум 16 символов.")
        return

    # Пытаемся установить визуально (титул в ТГ)
    try:
        user_id_for_api = int(target_id) if target_id.isdigit() else target_id
        bot.setChatAdministratorCustomTitle(
            chat_id=u, 
            user_id=user_id_for_api, 
            custom_title=new_nick
        )
    except Exception:
        # Если не получилось (юзер не админ), не страшно — сохраняем в список!
        pass

    # СОХРАНЕНИЕ В СПИСОК
    nicks_list = Bot.getData("nicks_list") or []
    nicks_list.append({
        "name": target_name,
        "nick": new_nick
    })
    Bot.saveData("nicks_list", nicks_list)

    # Отправляем красивое сообщение
    admin_name = user.get("first_name") or "Админ"
    if target_id.isdigit():
        target_name_html = f'<a href="tg://user?id={target_id}">{target_name}</a>'
    else:
        target_name_html = target_name

    admin_html = f'<a href="tg://user?id={u}">{admin_name}</a>'
    final_msg = f'{admin_html} установил никнейм {target_name_html}: <b>{new_nick}</b>'
    bot.replyText(u, final_msg, parseMode="HTML")
    return


# ==========================================
# КОМАНДА /nlist (Показ списка)
# ==========================================
elif text_lower == "/nlist":
    nicks_list = Bot.getData("nicks_list") or []

    if not nicks_list:
        bot.replyText(u, "📭 Список ников пуст.")
        return

    msg = "📋 <b>Список установленных ников:</b>\n\n"
    count = 1

    for item in nicks_list:
        name = item.get("name", "Пользователь")
        nick = item.get("nick", "—")
        
        # Делаем имя кликабельным, если это ID
        if name.isdigit():
            name_html = f'<a href="tg://user?id={name}">{name}</a>'
        else:
            name_html = name
            
        # Формат: 1. Имя - Ник
        msg += f"{count}. {name_html} - {nick}\n"
        count += 1

    bot.replyText(u, msg, parseMode="HTML")
    return