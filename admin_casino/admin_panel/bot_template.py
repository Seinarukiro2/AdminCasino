from telethon import TelegramClient, events, Button
import os

api_id = '7248451'
api_hash = 'db9b16eff233ee8dfd7c218138cb2e10'
bot_token = '{bot_token}'

client = TelegramClient('bot_session', api_id, api_hash).start(bot_token=bot_token)

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    welcome_message = "{welcome_message}"

    buttons = [[Button.url("Start game", "{button_url}")]]
    
    await client.send_message(event.chat_id, welcome_message, buttons=buttons)

client.run_until_disconnected()
