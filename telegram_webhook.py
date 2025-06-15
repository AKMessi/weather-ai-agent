from flask import Flask, request
import os
from my_agent_tools import get_today_weather_tool, summarize_weather_tool, send_telegram_tool
from langchain.agents import initialize_agent, AgentType
from langchain_google_genai import ChatGoogleGenerativeAI
from datetime import datetime
import requests

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        print("🌐 Webhook received raw payload:", data)

        if not data:
            print("❌ No data received.")
            return "no data", 400

        if 'message' in data:
            print("📩 Message content:", data['message'])
            chat_id = str(data['message']['chat']['id'])
            text = data['message'].get('text', '')
            print(f"👤 From chat_id {chat_id}, user said: {text}")

            if text.lower() == "/start":
                save_chat_id(chat_id)
                send_welcome_message(chat_id)

        return "ok", 200

    except Exception as e:
        print("❌ Webhook crashed with error:", e)
        return f"Error: {e}", 500


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

        print(f"🌤️ Triggered manually at {datetime.now()}")
        agent.invoke("Get today's weather for Mumbai, summarize it nicely and send it to Telegram.")
        return "✅ Weather sent to Telegram", 200

    except Exception as e:
        print(f"❌ Error in weather agent: {e}")
        return f"❌ Error: {e}", 500


def save_chat_id(chat_id):
    file_path = "chat_ids.txt"

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
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN is missing from environment variables.")
        return

    message = "✅ You're now subscribed to daily Mumbai weather updates at 8 AM! 🌦️"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }

    try:
        response = requests.post(url, data=payload)
        print("📤 Telegram response:", response.status_code, response.text)
    except Exception as e:
        print("❌ Error sending welcome message:", e)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
