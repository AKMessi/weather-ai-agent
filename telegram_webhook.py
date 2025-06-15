# telegram_webhook.py
from flask import Flask, request
import os

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    
    if 'message' in data:
        text = data['message'].get('text', '')
        chat_id = str(data['message']['chat']['id'])

        if text.lower() == "/start":
            print(f"New user: {chat_id}")
            save_chat_id(chat_id)
            send_welcome_message(chat_id)

    return "ok", 200

def save_chat_id(chat_id):
    file_path = "chat_ids.txt"
    
    # Avoid duplicate chat IDs
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            existing = set(line.strip() for line in f)
    else:
        existing = set()
    
    if chat_id not in existing:
        with open(file_path, "a") as f:
            f.write(chat_id + "\n")
        print(f"✅ Chat ID {chat_id} added.")
    else:
        print(f"ℹ️ Chat ID {chat_id} already exists.")

def send_welcome_message(chat_id):
    import requests
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    message = "✅ You're now subscribed to daily Mumbai weather updates at 8 AM! 🌦️"

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("Error sending welcome message:", e)

if __name__ == "__main__":
    app.run(port=5000)
