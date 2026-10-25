from telethon import TelegramClient, events

API_ID = 6
API_HASH = 'eb066100c6f1400f40b77786cb15fb16'

TARGET_CHAT = -1001234567890
TARGET_USER = 987654321

client = TelegramClient(
    'my_session',
    api_id=API_ID,
    api_hash=API_HASH,
    device_model='PC',
    system_version='Windows 10',
    app_version='10.0.0'
)

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

async def main():
    await client.start()
    await client.run_until_disconnected()

if __name__ == '__main__':
    client.loop.run_until_complete(main())