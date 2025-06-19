import requests
import os
from dotenv import load_dotenv
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, function_tool
from agents.run import RunConfig, ModelSettings
import streamlit as st
import asyncio

# 🔐 Load environment variables
load_dotenv()

API_KEY = os.getenv("api_key")  # For Gemini
weather_api_key = os.getenv("weather_api_key")  # For weatherapi.com

# 🔍 Validate API keys
if not API_KEY or not weather_api_key:
    raise ValueError("Missing API keys. Set 'api_key' and 'weather_api_key' in your .env file.")


st.set_page_config(page_title="🌤️ AI Powered Weather Assistant", page_icon="🌍", layout="centered")

# 🌐 OpenAI-compatible Gemini client
External_client = AsyncOpenAI(
    api_key=API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

# 🧠 Model setup
model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=External_client
)

# ⚙️ RunConfig with tool usage required
config = RunConfig(
    model=model,
    model_provider=External_client,
    tracing_disabled=True,
    model_settings=ModelSettings(tool_choice="required")
)

# 🌤️ Tool: Get weather using WeatherAPI.com
@function_tool
def get_weather(city: str) -> str:
    """
    Fetches real-time weather info for a city using WeatherAPI.com
    """

    url = f"https://api.weatherapi.com/v1/current.json?key={weather_api_key}&q={city}"
    response = requests.get(url)
    data = response.json()

    if response.status_code != 200 or "current" not in data:
        return f"❌ Couldn't find weather data for {city}. Please check the city name."

    temp = data['current']['temp_c']
    feels_like = data['current']['feelslike_c']
    description = data['current']['condition']['text']
    location = data['location']['name']

    return (
        f"🌍 Location: {location}\n"
        f"🌡️ Temperature: {temp}°C (Feels like {feels_like}°C)\n"
        f"☁️ Condition: {description}"
    )

# 🧠 Weather Agent
agent = Agent(
    name="Weather Assistant",
    instructions="You are a weather assistant. Answer weather questions using the get_weather tool.",
    tools=[get_weather],
    model=model
)

# # 🚀 Main Runner
# async def main():
#     result = await Runner.run(agent, "What's the weather in karachi?", run_config=config)
#     print("\n🤖 Agent Response:\n", result.final_output)

# # ✅ Run with asyncio
# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())



st.title("🌤️ Weather Assistant")
st.markdown("Get **real-time weather updates** for your city instantly.")
# 🔧 Custom CSS 
st.markdown("""
    <style>
        body, .stApp {
            background-color: #0ABAB5;
            color: white;
        }
        input, textarea {
            background-color: #1a1a1a !important;
            color: white !important;
        }
        .stButton>button {
            background-color: #444 !important;
            color: white !important;
        }
        .stTextInput>div>div>input {
            background-color: #222 !important;
            color: white !important;
        }
    </style>
""", unsafe_allow_html=True)

# UI Input
city = st.text_input("Enter city name", placeholder="e.g., Lahore")

# Run on Button Click
if st.button("🔍 Ask AI for Weather") and city:
    with st.spinner("🤖 Thinking..."):
        async def run_agent():
            result = await Runner.run(agent, f"What's the weather in {city}?", run_config=config)
            return result.final_output

        final_output = asyncio.run(run_agent())
        st.success("✅ Here's what the AI Assistant found:")
        st.markdown(final_output)
