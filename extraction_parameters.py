import requests
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ValidationError
from langchain_core.prompts import PromptTemplate
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser # <-- Nuovo parser per JSON

# --- Definizione del Modello Pydantic per la Richiesta Meteo ---
class DateRange(BaseModel):
    from_date: str = Field(description="Data di inizio dell'intervallo in formato YYYY-MM-DD")
    to: str = Field(description="Data di fine dell'intervallo in formato YYYY-MM-DD")

class WeatherRequest(BaseModel):
    city: Optional[str] = Field(None, description="Nome della città per cui si richiedono i dati meteo.")
    metrics: List[str] = Field(default=["temperature"], description="Elenco delle metriche meteo richieste, ad esempio 'temperature', 'humidity', 'pressure', 'wind_speed', 'air_quality'.")
    date_range: Optional[DateRange] = Field(None, description="Intervallo di date richiesto per i dati.")
    valid: bool = Field(True, description="Indica se la richiesta è valida dopo il parsing.")
    missing_parameters: List[str] = Field(default_factory=list, description="Lista di parametri obbligatori mancanti.")

# --- Creazione del Prompt per l'LLM (Parsing) ---
# In v1, spesso si usa un prompt che chiede esplicitamente un output JSON.
parsing_prompt_template = """
Sei un esperto assistente per richieste meteorologiche. Il tuo compito è estrarre informazioni strutturate da una richiesta di testo in linguaggio naturale.

Analizza attentamente la richiesta fornita e identifica:
- La citta' richiesta (city).
- Le metriche meteorologiche specificate (metrics), ad esempio temperatura, umidita', pressione, velocita' del vento, qualita' dell'aria.
- L'intervallo di date richiesto (date_range), se specificato, in formato ISO 8601 (YYYY-MM-DD).

Se un elemento non e' esplicitamente menzionato, imposta il campo appropriato a null o a un valore di default ragionevole.

Richiesta utente: {user_request}

Risposta (solo il JSON, senza altri testi o Markdown, seguendo rigorosamente lo schema definito):
"""

# --- Inizializzazione del Parser per JSON ---
# Usa JsonOutputParser con il modello Pydantic
json_parser = JsonOutputParser(pydantic_object=WeatherRequest)

# Crea il prompt usando il parser
parsing_prompt = PromptTemplate(
    template=parsing_prompt_template,
    input_variables=["user_request"],
    # partial_variables={"format_instructions": json_parser.get_format_instructions()} # <-- Rimosso, non necessario qui
)

# --- Creazione del Prompt per la Risposta Finale in Linguaggio Naturale ---
natural_language_prompt_template = """
Sei un assistente meteorologico che fornisce risposte chiare e utili.

Ecco i dati meteo grezzi ottenuti per la citta' '{city}':
{api_response_json}

La richiesta originale dell'utente era: "{original_request}"

Formatta questi dati in una risposta completa, scorrevole e in linguaggio naturale, rispondendo specificamente alla richiesta dell'utente. Usa un linguaggio chiaro e conciso. Se la richiesta chiedeva specifiche metriche (come temperatura, umidita'), concentrati su quelle. Se chiedeva un intervallo di date, riassumi le condizioni per quel periodo.
"""

nl_prompt = PromptTemplate(
    template=natural_language_prompt_template,
    input_variables=["city", "api_response_json", "original_request"]
)

# --- Classe WeatherAPI (mantenuta come fornita) ---
class WeatherAPI:
    def __init__(self, openweather_api_key):
        self.OPENWEATHER_API_KEY = openweather_api_key
        self.OWM_CURRENT_URL = "http://api.openweathermap.org/data/2.5/weather"
        self.OWN_FORECAST_URL = "http://api.openweathermap.org/data/2.5/forecast"
        self.OWM_AIR_POLLUTION_URL = "http://api.openweathermap.org/data/2.5/air_pollution"
        self.OWM_GEO_URL = "http://api.openweathermap.org/geo/1.0/direct"
        self.OPEN_METEO_CURRENT_URL = "https://api.open-meteo.com/v1/forecast"

    def get_coordinates(self, city_name):
        params = {
            'q': city_name,
            'limit': 1,
            'appid': self.OPENWEATHER_API_KEY
        }
        print(f"[DEBUG] chiamata geocoding per {city_name}")
        response = requests.get(self.OWM_GEO_URL, params=params)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                lat = data[0]['lat']
                lon = data[0]['lon']
                print(f"[DEBUG] coordinate trovate: lat ={lat}, lon= {lon}")
                return lat, lon
            else:
                print(f"[ERROR] nessuna coordinata trovata per {city_name}")
        else:
            print(f"[ERROR] errore geocoding: {response.status_code} - {response.text}")
        return None, None

    def get_current_weather_owm(self, lat, lon):
        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.OPENWEATHER_API_KEY,
            'units': 'metric'
        }
        response = requests.get(self.OWM_CURRENT_URL, params=params)
        if response.status_code == 200:
            print("[DEBUG] Meteo Attuale OWM ok!")
            return response.json()
        else:
            print(f"Errore nella richiesta meteo OpenWeatherMap: {response.status_code} - {response.text}")
            return None

    def get_forecast_5d_own(self, lat, lon):
        params={
            'lat': lat,
            'lon':lon,
            'appid': self.OPENWEATHER_API_KEY,
            'units':'metric'
        }
        print(f"[DEBUG] Chiamata previsioni 5 giorni OWM")
        response = requests.get(self.OWN_FORECAST_URL, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Errore OWM Forecast: {response.status_code} - {response.text}")
            return None
        
    def get_air_quality_owm(self, lat, lon):
        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.OPENWEATHER_API_KEY
        }
        response = requests.get(self.OWM_AIR_POLLUTION_URL, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Errore nella richiesta qualita' aria: {response.status_code} - {response.text}")
            return None

    def get_current_weather_openmeteo(self, lat, lon):
        params = {
            'latitude': lat,
            'longitude': lon,
            'current_weather': True,
            'timezone': 'auto'
        }
        response = requests.get(self.OPEN_METEO_CURRENT_URL, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Errore nella richiesta Open-Meteo: {response.status_code} - {response.text}")
            return None

    def get_all_data_for_city(self, city_name):
        lat, lon = self.get_coordinates(city_name)
        if not lat or not lon:
            print(f"Coordinate non trovate per {city_name}")
            return None

        weather_owm = self.get_current_weather_owm(lat, lon)
        air_owm = self.get_air_quality_owm(lat, lon)
        forecast_own = self.get_forecast_5d_own(lat, lon)
        parsed_owm = self._parse_owm_data(weather_owm, air_owm)
        parsed_forecast = self._parse_forecast_data(forecast_own)

        weather_om = self.get_current_weather_openmeteo(lat, lon)
        parsed_om = self._parse_openmeteo_data(weather_om)

        return {
            'city': city_name,
            'openweathermap_current': parsed_owm,
            'openweathermap_forecast_5d': parsed_forecast,
            'openmeteo_current': parsed_om,
            'timestamp': datetime.now().isoformat()
        }

    def _parse_owm_data(self, weather_data, air_data):
        if not weather_data:
            print("Dati meteo attuali OWM mancanti per il parsing")
            return None
        main = weather_data.get('main', {})
        wind = weather_data.get('wind', {})
        owm_parsed = {
            'temperature': main.get('temp'),
            'feels_like': main.get('feels_like'),
            'humidity': main.get('humidity'),
            'pressure': main.get('pressure'),
            'wind_speed': wind.get('speed', 0),
            'wind_direction': wind.get('deg', 0),
            'description': weather_data.get('weather', [{}])[0].get('description', 'N/A')
        }
        if air_data and 'list' in air_data and len(air_data['list']) > 0:
            components = air_data['list'][0]['components']
            aqi = air_data['list'][0]['main']['aqi']
            owm_parsed['air_quality'] = {
                'aqi': aqi,
                'co': components['co'],
                'no2': components['no2'],
                'o3': components['o3'],
                'pm2_5': components['pm2_5'],
                'pm10': components['pm10']
            }
        return owm_parsed

    def _parse_forecast_data(self, forecast_data):
        if not forecast_data or 'list' not in forecast_data:
            print("Dati previsione OWM mancanti o non validi per il parsing")
            return None
        parsed_list = []
        for item in forecast_data['list']:
            try:
                main = item['main']
                parsed_list.append({
                    'datetime': item['dt_txt'],
                    'temperature': main['temp'],
                    'feels_like': main['feels_like'],
                    'humidity': main['humidity'],
                    'pressure': main['pressure'],
                    'description': item['weather'][0]['description']
                })
            except (KeyError, IndexError) as e:
                print(f"Errore nel parsing di un elemento della previsione: {e}")
                continue
        return parsed_list

    def _parse_openmeteo_data(self, meteo_data):
        if not meteo_data:
            print("Dati Open-Meteo mancanti per il parsing")
            return None
        current = meteo_data.get('current_weather', {})
        return {
            'temperature': current.get('temperature'),
            'windspeed': current.get('windspeed'),
            'winddirection': current.get('winddirection'),
            'time': current.get('time'),
            'weathercode': current.get('weathercode')
        }


def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Dati salvati in: {filename}")

# --- Funzione per Eseguire il Parsing con LangChain v1 ---
def parse_weather_request(user_input: str, llm: BaseLanguageModel) -> Optional[WeatherRequest]:
    try:
        # Formatta il prompt
        final_prompt = parsing_prompt.format(user_request=user_input)
        print(f"[DEBUG] Prompt inviato all'LLM (Parsing):\n{final_prompt}\n")

        # Invoca l'LLM
        messages = [HumanMessage(content=final_prompt)]
        llm_output = llm.invoke(messages).content
        print(f"[DEBUG] Output LLM (Parsing):\n{llm_output}\n")

        # Parse l'output JSON usando JsonOutputParser
        # Questo parser converte automaticamente il JSON in un oggetto Pydantic
        parsed_request_obj = json_parser.parse(llm_output)
        print(f"[DEBUG] Oggetto WeatherRequest Pydantic:\n{parsed_request_obj}\n")

        # Valida e aggiorna i campi 'valid' e 'missing_parameters'
        # Questo viene fatto manualmente poiché non è parte dello schema JSON originale
        valid = True
        missing_params = []
        if not parsed_request_obj.city:
            valid = False
            missing_params.append("city")

        # Crea una nuova istanza con i campi aggiornati
        # Usiamo .dict() per ottenere un dizionario, lo modifichiamo e lo ricreiamo
        parsed_dict = parsed_request_obj.dict()
        parsed_dict["valid"] = valid
        parsed_dict["missing_parameters"] = missing_params
        updated_request_obj = WeatherRequest(**parsed_dict)

        return updated_request_obj

    except ValidationError as ve:
        print(f"[ERROR] Errore di validazione Pydantic: {ve}")
        return None
    except Exception as e:
        print(f"[ERROR] Errore durante il parsing: {e}")
        return None

# --- Funzione per Generare la Risposta Finale in Linguaggio Naturale ---
def generate_natural_language_response(original_request: str, parsed_request: WeatherRequest, api_data: Dict[str, Any], llm: BaseLanguageModel) -> str:
    try:
        city = parsed_request.city or "Sconosciuta"
        api_response_json_str = json.dumps(api_data, indent=2, ensure_ascii=False)

        final_response_prompt = nl_prompt.format(
            city=city,
            api_response_json=api_response_json_str,
            original_request=original_request
        )

        print(f"[DEBUG] Prompt inviato all'LLM (NL Response):\n{final_response_prompt}\n")

        messages = [HumanMessage(content=final_response_prompt)]
        nl_response = llm.invoke(messages).content

        print(f"[DEBUG] Risposta finale in linguaggio naturale:\n{nl_response}\n")
        return nl_response

    except Exception as e:
        print(f"[ERROR] Errore durante la generazione della risposta finale: {e}")
        return f"Mi dispiace, sono riuscito a recuperare i dati per {parsed_request.city}, ma non sono riuscito a formularli in linguaggio naturale a causa di un errore interno."

# --- Esempio di Utilizzo ---
if __name__ == "__main__":
    API_KEY = '2300cb7362ef7560c3e75c5b6aa48b2c'  # Inserisci la tua chiave API qui
    weather_client = WeatherAPI(API_KEY)

    # Chiedi all'utente di inserire la richiesta
    user_input = input("Inserisci la tua richiesta meteo: ").strip()

    # --- INIZIALIZZA IL TUO LLM QUI ---
    from langchain_community.chat_models import ChatOllama
    llm = ChatOllama(model="gemma:2b", temperature=0.1)
    
    
    if llm is None:
        print("ERRORE: LLM non inizializzato. Impossibile proseguire.")
        exit()

    # Esegui il parsing
    parsed_request = parse_weather_request(user_input, llm)

    if parsed_request:
        print("--- Risultato del Parsing ---")
        print(f"Richiesta valida: {parsed_request.valid}")
        if not parsed_request.valid:
            print(f"Parametri mancanti: {parsed_request.missing_parameters}")
        if parsed_request.city:
            print(f"Citta': {parsed_request.city}")
        if parsed_request.metrics:
            print(f"Metriche richieste: {parsed_request.metrics}")
        if parsed_request.date_range:
            print(f"Intervallo date: dal {parsed_request.date_range.from_date} al {parsed_request.date_range.to}")

        # Se la richiesta e' valida, puoi procedere con la chiamata API
        if parsed_request.valid and parsed_request.city:
            print("\n--- Chiamata API ---")
            api_result = weather_client.get_all_data_for_city(parsed_request.city)
            if api_result:
                # Salva i dati grezzi se necessario
                output_filename = f"weather_data_{parsed_request.city}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                save_to_json(api_result, output_filename)

                print("\n--- Generazione Risposta Finale ---")
                final_response = generate_natural_language_response(user_input, parsed_request, api_result, llm)
                print("\n--- Risposta Finale all'Utente ---")
                print(final_response)
            else:
                print("Nessun dato ottenuto dall'API.")
        else:
            print("\n--- Richiesta non valida o citta' mancante, impossibile chiamare l'API. ---")
            error_message = f"Non e' stato possibile elaborare la richiesta '{user_input}' perche' manca la seguente informazione: {', '.join(parsed_request.missing_parameters)}. Per favore, fornisci la citta'."
            print(f"\n--- Risposta Finale all'Utente (Errore) ---")
            print(error_message)
    else:
        print("Impossibile parsare la richiesta utente.")
