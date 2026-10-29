import asyncio
import urllib.parse
import webbrowser
from telethon import TelegramClient, events, functions, types

API_ID = 2040
API_HASH = 'b18441a1ff607e10a989891a5462e627'

TARGET_CHAT = -1002401885759
INITIAL_TARGET_USER = '@Ken_tuxa'

# Глобальные настройки
state = {
    'active': True,
    # Режимы: 'normal' (повтор), 'sponge' (ЗаБоРчИк), 'reverse' (наоборот), 'react_only' (только реакции)
    'mode': 'normal',
    'reaction': '🤡',        # Эмодзи для реакции
    'anti_edit': True,       # Отслеживание редактирования сообщений
    'target_id': None,
    'target_name': ''
}

message_cache = {}


def transform_text(text: str, mode: str) -> str:
    if not text:
        return ''
    if mode == 'sponge':
        return ''.join(c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(text))
    elif mode == 'reverse':
        return text[::-1]
    return text


async def main():
    client = TelegramClient(
        'my_session',
        API_ID,
        API_HASH,
        device_model='AyuGram Desktop',
        system_version='Windows 11 x64',
        app_version='7.2.9 x64',
        lang_code='en',
        system_lang_code='en-US'
    )

    await client.connect()

    if not await client.is_user_authorized():
        qr_login = await client.qr_login()
        encoded_url = urllib.parse.quote(qr_login.url)
        web_qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={encoded_url}"
        webbrowser.open(web_qr_url)
        try:
            await qr_login.wait()
        except Exception as e:
            if 'SessionPasswordNeededError' in str(type(e)):
                password = input('Введите ваш облачный пароль (2FA): ')
                await client.sign_in(password=password)
            else:
                raise e

    chat_entity = await client.get_entity(TARGET_CHAT)
    user_entity = await client.get_entity(INITIAL_TARGET_USER)

    state['target_id'] = user_entity.id
    state['target_name'] = f"@{user_entity.username}" if user_entity.username else user_entity.first_name

    print(f"Бот запущен! Цель: {state['target_name']} (ID: {state['target_id']})")
    print("Доступные команды (писать в любой чат или Избранное):")
    print("  .on / .off                                — включить/выключить бота")
    print("  .mode normal|sponge|reverse|react_only    — сменить режим работы")
    print("  .react 🤡                                 — сменить эмодзи реакции")
    print("  .target @username (или реплаем)           — сменить цель на лету")

    # 1. ОБРАБОТЧИК НОВЫХ СООБЩЕНИЙ ЦЕЛИ
    @client.on(events.NewMessage(chats=chat_entity.id))
    async def fast_repeater(event):
        if not state['active'] or event.sender_id != state['target_id']:
            return

        # Ставим мгновенную реакцию во всех режимах
        if state['reaction']:
            try:
                await client(functions.messages.SendReactionRequest(
                    peer=event.chat_id,
                    msg_id=event.message.id,
                    reaction=[types.ReactionEmoji(emoticon=state['reaction'])]
                ))
            except Exception:
                pass

        # Если включен режим «только реакции», дальше ничего не отправляем
        if state['mode'] == 'react_only':
            return

        # Сохраняем оригинал текста в кэш для анти-редактирования
        if event.message.text:
            message_cache[event.message.id] = event.message.text

        prefix = f"user {state['target_name']} said:"
        modified_text = transform_text(event.message.text, state['mode'])

        # Отправляем дубликат сообщения
        if event.message.media:
            caption = f"{prefix} {modified_text}" if modified_text else prefix
            await client.send_file(
                entity=event.chat_id,
                file=event.message.media,
                caption=caption,
                reply_to=event.message.id
            )
        elif event.message.text:
            await client.send_message(
                entity=event.chat_id,
                message=f"{prefix} {modified_text}",
                reply_to=event.message.id
            )

    # 2. АНТИ-РЕДАКТИРОВАНИЕ (отключено в режиме react_only)
    @client.on(events.MessageEdited(chats=chat_entity.id))
    async def anti_edit_handler(event):
        if (not state['active']
                or not state['anti_edit']
                or state['mode'] == 'react_only'
                or event.sender_id != state['target_id']):
            return

        old_text = message_cache.get(event.message.id)
        new_text = event.message.text

        if old_text and new_text and old_text != new_text:
            message_cache[event.message.id] = new_text
            await client.send_message(
                entity=event.chat_id,
                message=f"{state['target_name']} edit\n"
                        f"before editing: «{old_text}»",
                reply_to=event.message.id
            )

    # 3. КОМАНДЫ УПРАВЛЕНИЯ С ВАШЕГО АККАУНТА
    @client.on(events.NewMessage(outgoing=True))
    async def command_handler(event):
        text = event.raw_text.strip()

        if text == '.off':
            state['active'] = False
            await event.edit('**skript stopped**')
        elif text == '.on':
            state['active'] = True
            await event.edit(f"**skript active** target: {state['target_name']} | mode: `{state['mode']}`")
        elif text.startswith('.mode '):
            new_mode = text.split(' ', 1)[1].strip()
            if new_mode in ('normal', 'sponge', 'reverse', 'react_only'):
                state['mode'] = new_mode
                await event.edit(f"**edit mode:** `{new_mode}`")
        elif text.startswith('.react '):
            new_emoji = text.split(' ', 1)[1].strip()
            state['reaction'] = new_emoji
            await event.edit(f"**reaction edited:** {new_emoji}")
        elif text.startswith('.target'):
            parts = text.split(' ', 1)
            if event.is_reply and len(parts) == 1:
                reply_msg = await event.get_reply_message()
                target_user = await client.get_entity(reply_msg.sender_id)
            elif len(parts) > 1:
                target_user = await client.get_entity(parts[1].strip())
            else:
                return

            state['target_id'] = target_user.id
            state['target_name'] = f"@{target_user.username}" if target_user.username else target_user.first_name
            await event.edit(f"**target acquired:** {state['target_name']} (ID: `{state['target_id']}`)")

    await client.run_until_disconnected()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\nПрограмма остановлена.')