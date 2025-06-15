from flask import Flask, request
import os
import requests
from weather_tools import get_today_weather_tool, summarize_weather_tool, send_telegram_tool
from langchain.agents import initialize_agent, AgentType
from langchain_google_genai import ChatGoogleGenerativeAI
from datetime import datetime

chat_ids = set()

def load_chat_ids():
    if os.path.exists("chat_ids.txt"):
        with open("chat_ids.txt", "r") as f:
            for line in f:
                chat_ids.add(line.strip())

def save_chat_id(chat_id):
    if chat_id not in chat_ids:
        chat_ids.add(chat_id)
        with open("chat_ids.txt", "a") as f:
            f.write(chat_id + "\n")
        print(f"✅ Chat ID {chat_id} added.")
    else:
        print(f"ℹ️ Chat ID {chat_id} already exists.")

def send_welcome_message(chat_id):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    message = "✅ You're now subscribed to daily Mumbai weather updates at 8 AM! 🌦️"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    requests.post(url, data=payload)

app = Flask(__name__)
load_chat_ids()

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print("📩 Webhook received:", data)

    if 'message' in data:
        chat_id = str(data['message']['chat']['id'])
        text = data['message'].get('text', '')

        if text.lower() == "/start":
            save_chat_id(chat_id)
            send_welcome_message(chat_id)

    return "ok", 200

@app.route('/run-weather-agent', methods=['GET'])
def run_weather_agent():
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            api_key=os.getenv("GEMINI_API_KEY")
        )

        tools = [
            get_today_weather_tool,
            summarize_weather_tool,
            send_telegram_tool
        ]

        agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True
        )

        print(f"🌤️ Triggered at {datetime.now()}")
        agent.invoke("Get today's weather for Mumbai, summarize it nicely and send it to Telegram.")
        return "✅ Weather sent to Telegram", 200

    except Exception as e:
        print(f"❌ Error: {e}")
        return f"❌ Error: {e}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
