from fastapi import FastAPI, Request
from telethon import TelegramClient, events
import asyncio
import requests
import uvicorn
from threading import Thread

from dotenv import load_dotenv
import os

load_dotenv()

# 👉 Твои данные
API_ID = int(os.getenv("API_ID", 25729674))
API_HASH = os.getenv("API_HASH", "117f8a4a693ea7bf5bca271081ba8d17")
SESSION_NAME = os.getenv("SESSION_NAME", "my_user")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "https://famezy.space/webhook-test/91afddd5-17a3-47df-ba65-f89aa8bdaf33")
PORT = int(os.getenv("PORT", 8000))

app = FastAPI()
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# Отправка входящих сообщений в n8n
@client.on(events.NewMessage(incoming=True))
async def handler(event):
    if event.is_private and not event.out:
        try:
            response = requests.post(N8N_WEBHOOK_URL, json={
                "user_id": event.sender_id,
                "text": event.raw_text
            })
            print(f"[n8n webhook response] Status: {response.status_code}, Content: {response.text}")
        except Exception as e:
            print(f"[Ошибка отправки в n8n]: {e}")

# Получение ответа от n8n и отправка его пользователю
import asyncio

def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@app.post("/reply")
async def reply(request: Request):
    try:
        if not client.is_connected():
            return {"status": "error", "message": "Telegram client not connected"}
            
        data = await request.json()
        user_id = int(data["user_id"])
        text = data["text"]
        
        # Run Telegram client operation in a new event loop
        def send_msg():
            return run_async(client.send_message(user_id, text))
            
        Thread(target=send_msg).start()
        return {"status": "ok"}
    except Exception as e:
        print(f"[Error in /reply endpoint]: {str(e)}")
        return {"status": "error", "message": str(e)}

def start_fastapi():
    uvicorn.run(app, host="0.0.0.0", port=PORT)

async def main():
    await client.start()
    print("Telegram клиент запущен.")
    Thread(target=start_fastapi, daemon=True).start()
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
