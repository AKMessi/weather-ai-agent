# telegram_webhook.py
from flask import Flask, request
import os
from my_agent_tools import get_today_weather_tool, summarize_weather_tool, send_telegram_tool
from langchain.agents import initialize_agent, AgentType
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from datetime import datetime


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

# Weather trigger route
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
        print(f"❌ Error: {e}")
        return f"❌ Error: {e}", 500

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
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
