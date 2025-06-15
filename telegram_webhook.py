from flask import Flask, request
import os
from weather_tools import get_today_weather_tool, summarize_weather_tool, send_telegram_tool
from langchain.agents import initialize_agent, AgentType
from langchain_google_genai import ChatGoogleGenerativeAI
from datetime import datetime
import requests
import gdown
from drive_helper import authenticate, read_chat_ids_file, write_chat_ids_file

def download_credentials():
    credentials_path = "credentials.json"
    if not os.path.exists(credentials_path):
        # Google Drive file ID extracted from the shared link
        file_id = "1yL-ZL6fcUUWQNHtXk0GMx-5MLs0Mzykx"
        url = f"https://drive.google.com/uc?id={file_id}"
        print("⬇️ Downloading credentials.json from Google Drive...")
        gdown.download(url, credentials_path, quiet=False)


chat_ids = set()

# Load chat IDs into memory once on startup
def load_chat_ids():
    file_path = "chat_ids.txt"
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            for line in f:
                chat_ids.add(line.strip())

load_chat_ids()


app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json(force=True)  # force=True helps avoid bad content-type issues
        print("✅ Webhook hit")
        print("📦 Raw data received:", data)

        if not data:
            print("❌ No data received.")
            return "no data", 400

        if 'message' in data:
            print("📩 Message content:", data['message'])
            chat_id = str(data['message']['chat']['id'])
            text = data['message'].get('text', '')
            print(f"👤 Chat ID: {chat_id}, Message: {text}")

            if text.lower() == "/start":
                save_chat_id(chat_id)
                send_welcome_message(chat_id)

        return "ok", 200

    except Exception as e:
        import traceback
        print("❌ Webhook crashed with error:")
        traceback.print_exc()  # This will show the full error with line number
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
    drive = authenticate()
    chat_ids, file_id = read_chat_ids_file(drive)
    if chat_id not in chat_ids:
        chat_ids.add(chat_id)
        write_chat_ids_file(drive, chat_ids, file_id)
        print(f"✅ Chat ID {chat_id} added to Google Drive.")
    else:
        print(f"ℹ️ Chat ID {chat_id} already exists.")


def send_welcome_message(chat_id):
    token = os.getenv("TELEGRAM_TOKEN")
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
    download_credentials()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
