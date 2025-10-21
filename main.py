from whether_bot.API_weather import WeatherAPI
from whether_bot.prompts import PromptManager
from whether_bot.assistant import WeatherAssistant


if __name__ == "__main__":
    print("Type 'exit' to quit.")
    assistant = WeatherAssistant(api_key="2300cb7362ef7560c3e75c5b6aa48b2c")

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break
        assistant.handle_message(user_input)
