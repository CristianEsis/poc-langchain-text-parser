import re
from datetime import datetime, timedelta
from .API_weather import WeatherAPI
from .prompts import PromptManager

class WeatherAssistant:
    def __init__(self, api_key):
        self.prompts = PromptManager()
        self.weather_client = WeatherAPI(api_key)
        self.modo_meteo = False
        self.ultima_città = None
        self.ultima_data = None

    def _parse_extraction(self, text):
        città_match = re.search(r"Città:\s*(.+)", text)
        data_match = re.search(r"Intervallo date:\s*(.+)", text)
        città = città_match.group(1).strip().lower() if città_match else None
        intervallo = data_match.group(1).strip() if data_match else None

        oggi = datetime.now().strftime("%Y-%m-%d")
        if intervallo and "domani" in intervallo.lower():
            data = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            data = oggi
        return città, data

    def handle_message(self, user_input):
        if any(w in user_input.lower() for w in ["meteo", "piove", "tempo", "previsioni"]):
            self.modo_meteo = True
            print("Modalità meteo ON\n")

        if not self.modo_meteo:
            print("Chat generale (meteo OFF)\n")
            return

        msg = self.prompts.extract_chain.invoke({"text": user_input})
        print(msg)

        città, data = self._parse_extraction(msg)
        if not città or città == "non specificata":
            print("Nessuna città specificata.\n")
            return

        result = self.weather_client.get_all_data_for_city(città)
        if not result:
            print("Dati meteo non trovati.\n")
            return

        nlp_response = self.prompts.nlp_chain.invoke({
            "città": città.capitalize(),
            "periodo": data,
            "meteo": result['openweathermap'] or result['openmeteo']
        })

        print(f"{nlp_response}\n")
