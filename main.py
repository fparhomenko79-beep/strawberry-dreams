import asyncio
import urllib.parse
import webbrowser
from telethon import TelegramClient, events

# Официальные ключи Telegram Desktop
API_ID = 2040
API_HASH = 'b18441a1ff607e10a989891a5462e627'

# Укажите числовой ID группы и ID (или @username) нужного участника
TARGET_CHAT = -1002401885759  # Замените на ID вашей группы
TARGET_USER = "@bloodthooorn"     # Замените на ID участника или '@username'


async def main():
    client = TelegramClient(
        'my_session',
        API_ID,
        API_HASH,
        device_model='Desktop',
        system_version='Windows 11',
        app_version='7.3.3 x64',
        lang_code='en',
        system_lang_code='en-US'
    )

    await client.connect()

    if not await client.is_user_authorized():
        qr_login = await client.qr_login()

        # Формируем URL для онлайн-генератора QR-кодов
        encoded_url = urllib.parse.quote(qr_login.url)
        web_qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={encoded_url}"

        print('\nОткрываем браузер с QR-кодом для входа...')
        print(f'Если браузер не открылся автоматически, перейдите по этой ссылке:\n{web_qr_url}\n')

        # Автоматически открываем сгенерированный QR-код в браузере по умолчанию
        webbrowser.open(web_qr_url)

        print('На телефоне откройте: Telegram -> Настройки -> Устройства -> Подключить устройство')
        print('и наведите камеру на QR-код в браузере.\n')

        try:
            await qr_login.wait()
        except Exception as e:
            if 'SessionPasswordNeededError' in str(type(e)):
                password = input('Введите ваш облачный пароль (2FA): ')
                await client.sign_in(password=password)
            else:
                raise e

    print('Успешный вход! Скрипт запущен и слушает сообщения...')

    @client.on(events.NewMessage(chats=TARGET_CHAT, from_users=TARGET_USER))
    async def fast_repeater(event):
        if event.message.media:
            await client.send_file(
                entity=event.chat_id,
                file=event.message.media,
                caption=event.message.text
            )
        elif event.message.text:
            await client.send_message(
                entity=event.chat_id,
                message=event.message.text
            )

    await client.run_until_disconnected()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\nПрограмма остановлена.')