# my_agent_tools.py

import requests
import os
from dotenv import load_dotenv
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import Tool, tool
import json


load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")
bot_token = os.getenv("TELEGRAM_TOKEN")

from datetime import datetime
import requests

def get_today_weather(city="Mumbai"):
    # Static Mumbai coordinates
    lat, lon = 19.014, 72.848
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_mean,"
        f"weathercode,windspeed_10m_max"
        f"&timezone=auto"
    )

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Extract only today's forecast (index 0)
        today = {
            "city": city,
            "timestamp": data["daily"]["time"][0],
            "temperature": data["daily"]["temperature_2m_max"][0],
            "humidity": 83,  # Static (Open-Meteo doesn’t give daily humidity)
            "precipitation_probability": data["daily"]["precipitation_probability_mean"][0],
            "wind_speed": data["daily"]["windspeed_10m_max"][0],
            "weather_code": data["daily"]["weathercode"][0],
        }

        return {"status": "success", "data": today}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}


def send_telegram_message(summary):
    """
    Send a Telegram message using the bot.
    """

    bot_token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": summary,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        return {"status": "success", "message": "Message sent"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def summarize_weather(weather_data: dict) -> str:
    """
    Uses Gemini to summarize raw weather data using human friendly language.
    """

    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key=gemini_api_key)

    prompt = f"""
    Summarize this daily weather forecast as if you are texting someone.

    - City: {weather_data['city']}
    - Time: {weather_data['timestamp']}
    - Temp: {weather_data['temperature']}°C
    - Humidity: {weather_data['humidity']}%
    - Rain chance: {weather_data['precipitation_probability']}%
    - Wind: {weather_data['wind_speed']} km/h
    - Weather code: {weather_data['weather_code']} (explain what this means)

    Keep it clear, concise and friendly. Don't omit important values. Also include what all things to consider as preventive and safety measures for today (actionable things).
    And don't keep it too short, and DONT FORGET TO KEEP IT VERY WELL FORMATTED. Keep it under 4000 characters."""
    result = llm.invoke(prompt)
    return result.content



@tool
def get_today_weather_tool(city: str = "Mumbai") -> dict:
    """Gets today's weather for a city."""
    # This handles cases where input is like "city='Mumbai'"
    if "city=" in city:
        city = city.split("city=")[-1].strip("'").strip('"')

    data = get_today_weather(city)  # Use your actual weather function here
    return data


@tool("summarize_weather_tool")
def summarize_weather_tool(tool_input) -> str:
    """Summarizes weather data."""
    import json

    try:
        # Convert stringified dict (if any) into proper dict
        if isinstance(tool_input, str):
            tool_input = json.loads(tool_input.replace("'", '"'))

        # Extract only the 'data' part if wrapped inside 'status'
        if isinstance(tool_input, dict) and "data" in tool_input:
            tool_input = tool_input["data"]

        return summarize_weather(tool_input)

    except Exception as e:
        return f"Error summarizing: {e}"


def get_all_chat_ids():
    try:
        with open("chat_ids.txt", "r") as f:
            return list(set(line.strip() for line in f if line.strip()))
    except FileNotFoundError:
        return []

@tool
def send_telegram_tool(summary: str) -> str:
    """Sends the weather summary to all Telegram users from chat_ids.txt on Google Drive."""
    try:
        chat_ids = get_all_chat_ids()

        token = os.environ["TELEGRAM_TOKEN"]
        if not token:
            return "❌ TELEGRAM_BOT_TOKEN not found."

        for chat_id in chat_ids:
            try:
                response = requests.post(
                    f"https://api.telegram.org/bot{bot_token}/sendMessage",
                    data={"chat_id": chat_id, "text": summary}
                )
                print(f"✅ Sent to {chat_id}, status: {response.status_code}")
            except Exception as e:
                print(f"❌ Failed to send to {chat_id}: {e}")

        return f"✅ Sent summary to {len(chat_ids)} chat(s)"

    except Exception as e:
        return f"❌ Failed to authenticate/send: {e}"