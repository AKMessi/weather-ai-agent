from langchain.agents import initialize_agent, AgentType
from langchain_google_genai import ChatGoogleGenerativeAI
from my_agent_tools import get_today_weather_tool, summarize_weather_tool, send_telegram_tool
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

# Initialize LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key=gemini_api_key)

# Define tools
tools = [
    get_today_weather_tool,
    summarize_weather_tool,
    send_telegram_tool
]

# Initialize agent
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# Agent execution function with error handling
def run_weather_to_telegram():
    try:
        print(f"🌦️ Running weather agent at {datetime.now()}")
        agent.invoke("Get today's weather for Mumbai, summarize it nicely and keep it very well formatted in Telegram-friendly format, and send it.")
        print("✅ Weather update sent to Telegram.")
    except Exception as e:
        print(f"❌ Error during weather agent run: {e}")

# Directly run the task (no scheduling here)
if __name__ == "__main__":
    run_weather_to_telegram()
