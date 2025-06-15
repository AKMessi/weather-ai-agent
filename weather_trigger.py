# weather_trigger.py

from flask import Flask
from datetime import datetime
from langchain.agents import initialize_agent, AgentType
from langchain_google_genai import ChatGoogleGenerativeAI
from weather_tools import get_today_weather_tool, summarize_weather_tool, send_telegram_tool
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.route("/run-weather-agent", methods=["GET"])
def run_agent():
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key=os.getenv("GEMINI_API_KEY"))
        tools = [get_today_weather_tool, summarize_weather_tool, send_telegram_tool]
        agent = initialize_agent(tools=tools, llm=llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)
        
        print(f"🌦️ Running weather agent at {datetime.now()}")
        agent.invoke("Get today's weather for Mumbai, summarize it nicely and send to Telegram.")
        return "✅ Weather update sent!"
    except Exception as e:
        return f"❌ Failed: {str(e)}", 500

if __name__ == "__main__":
    app.run()
