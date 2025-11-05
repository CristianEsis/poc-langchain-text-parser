from typing import Optional
from datetime import datetime, timedelta
from pydantic import ValidationError
from langchain_core.prompts import PromptTemplate
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser
import re
from models import WeatherRequest

class WeatherRequestParser:
    """Parser per richieste meteo in linguaggio naturale usando LLM"""
    
    def __init__(self, llm: BaseLanguageModel):
        self.llm = llm
        self.json_parser = JsonOutputParser(pydantic_object=WeatherRequest)
        self.prompt = self._create_prompt()
    
    def _create_prompt(self) -> PromptTemplate:
        """Crea il prompt template per il parsing"""
        template = """
Sei un esperto assistente per richieste meteorologiche. Il tuo compito è estrarre informazioni strutturate da una richiesta di testo in linguaggio naturale.

DATA CORRENTE: {current_date}

SCHEMA JSON RICHIESTO:
{{
    "city": "nome_citta",
    "metrics": ["temperature", "humidity", "pressure", "wind_speed", "air_quality"],
    "date_range": {{"from_date": "YYYY-MM-DD", "to": "YYYY-MM-DD"}} oppure null,
    "time_of_day": "morning" | "afternoon" | "evening" | "night" | null,
    "valid": true,
    "missing_parameters": []
}}

REGOLE IMPORTANTI:
- "city": stringa con il nome della città (obbligatorio)
- "metrics": SEMPRE una lista di stringhe, anche se una sola metrica. Valori possibili: "temperature", "humidity", "pressure", "wind_speed", "air_quality"
- "date_range": se specificato, deve essere un oggetto con "from_date" e "to", altrimenti null
- "time_of_day": periodo della giornata richiesto (morning=mattino, afternoon=pomeriggio, evening=sera, night=notte), null se non specificato
- Se non ci sono metriche specificate, usa: ["temperature"]
- Se non c'è intervallo di date, usa: null
- ⚠️ SE LA RICHIESTA NON È RIGUARDO AL METEO (es. cucina, sport, etc.): 
  • imposta `"valid": false`
  • aggiungi `"out_of_context"` a `missing_parameters`
  • NON tentare di estrarre dati meteo

REGOLE IMPORTANTI:
- "city": stringa con il nome della città (obbligatorio)
- "metrics": SEMPRE una lista di stringhe, anche se una sola metrica. Valori possibili: "temperature", "humidity", "pressure", "wind_speed", "air_quality"
- "date_range": se specificato, deve essere un oggetto con "from_date" e "to", altrimenti null
- "time_of_day": periodo della giornata richiesto (morning=mattino, afternoon=pomeriggio, evening=sera, night=notte), null se non specificato
- Se non ci sono metriche specificate, usa: ["temperature"]
- Se non c'è intervallo di date, usa: null

INTERPRETAZIONE TEMPORALE:
- "oggi" → from_date e to = data corrente
- "domani" → from_date e to = data corrente + 1 giorno
- "dopodomani" → from_date e to = data corrente + 2 giorni
- "questa settimana" → from_date = data corrente, to = data corrente + 7 giorni
- "mattino/mattina" → time_of_day: "morning"
- "pomeriggio" → time_of_day: "afternoon"
- "sera" → time_of_day: "evening"
- "notte" → time_of_day: "night"

ESEMPI:

Richiesta: "Che tempo fa a Roma?"
Risposta:
{{
    "city": "Roma",
    "metrics": ["temperature"],
    "date_range": null,
    "time_of_day": null,
    "valid": true,
    "missing_parameters": []
}}

Richiesta: "Temperatura a Milano oggi al mattino"
Risposta:
{{
    "city": "Milano",
    "metrics": ["temperature"],
    "date_range": {{"from_date": "{current_date}", "to": "{current_date}"}},
    "time_of_day": "morning",
    "valid": true,
    "missing_parameters": []
}}

Richiesta: "Come sarà il tempo domani a Napoli?"
Risposta:
{{
    "city": "Napoli",
    "metrics": ["temperature"],
    "date_range": {{"from_date": "{tomorrow_date}", "to": "{tomorrow_date}"}},
    "time_of_day": null,
    "valid": true,
    "missing_parameters": []
}}

Richiesta: "Umidità e vento a Torino stasera"
Risposta:
{{
    "city": "Torino",
    "metrics": ["humidity", "wind_speed"],
    "date_range": {{"from_date": "{current_date}", "to": "{current_date}"}},
    "time_of_day": "evening",
    "valid": true,
    "missing_parameters": []
}}

ORA ANALIZZA QUESTA RICHIESTA:
Richiesta utente: {user_request}

Risposta (SOLO IL JSON, senza testo aggiuntivo, markdown o spiegazioni):
"""
        return PromptTemplate(
            template=template,
            input_variables=["user_request", "current_date", "tomorrow_date"]
        )
    def parse(self, user_input: str) -> Optional[WeatherRequest]:
        """
        Parse una richiesta utente in linguaggio naturale
        
        Args:
            user_input: La richiesta dell'utente in testo libero
            
        Returns:
            Un oggetto WeatherRequest o None in caso di errore
        """
        try:
            # Calcola le date per il prompt
            current_date = datetime.now().strftime("%Y-%m-%d")
            tomorrow_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            
            # Formatta il prompt
            final_prompt = self.prompt.format(
                user_request=user_input,
                current_date=current_date,
                tomorrow_date=tomorrow_date
            )
            print(f"[DEBUG] Prompt inviato all'LLM (Parsing):\n{final_prompt}\n")

            # Invoca l'LLM
            messages = [HumanMessage(content=final_prompt)]
            llm_output = self.llm.invoke(messages).content
            print(f"[DEBUG] Output LLM (Parsing):\n{llm_output}\n")

            # Parse l'output JSON
            parsed_dict = self.json_parser.parse(llm_output)
            print(f"[DEBUG] Dizionario parsato:\n{parsed_dict}\n")

            # PRIMO CONTROLLO: Verifica se la richiesta è fuori contesto
            if "out_of_context" in parsed_dict.get("missing_parameters", []):
                print(f"[WARNING] Richiesta fuori contesto meteorologico: {user_input}")
                return None

            # VALIDAZIONE E CORREZIONE DEI TIPI
            # 1. Assicurati che metrics sia una lista
            if "metrics" not in parsed_dict or not parsed_dict["metrics"]:
                parsed_dict["metrics"] = ["temperature"]
            elif isinstance(parsed_dict["metrics"], str):
                parsed_dict["metrics"] = [parsed_dict["metrics"]]
            elif isinstance(parsed_dict["metrics"], dict):
                parsed_dict["metrics"] = list(parsed_dict["metrics"].keys())
            elif not isinstance(parsed_dict["metrics"], list):
                parsed_dict["metrics"] = ["temperature"]

            # 2. Gestisci date_range
            if "date_range" in parsed_dict:
                if parsed_dict["date_range"] is None:
                    pass
                elif isinstance(parsed_dict["date_range"], str):
                    # Prova a estrarre le date da una stringa formattata male
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2}).*?(\d{4}-\d{2}-\d{2})', parsed_dict["date_range"])
                    if date_match:
                        parsed_dict["date_range"] = {
                            "from_date": date_match.group(1),
                            "to": date_match.group(2)
                        }
                    else:
                        parsed_dict["date_range"] = None
                elif not isinstance(parsed_dict["date_range"], dict):
                    parsed_dict["date_range"] = None
            else:
                parsed_dict["date_range"] = None

            # 3. Valida time_of_day
            valid_times = ["morning", "afternoon", "evening", "night"]
            if "time_of_day" in parsed_dict:
                if parsed_dict["time_of_day"] not in valid_times and parsed_dict["time_of_day"] is not None:
                    parsed_dict["time_of_day"] = None
            else:
                parsed_dict["time_of_day"] = None

            # 4. Valida la città
            if "city" not in parsed_dict or not parsed_dict["city"]:
                # Prova a estrarre la città manualmente come fallback
                user_input_lower = user_input.lower()
                city_match = re.search(r"(?:a|in|di|presso|vicino a)\s+([A-Za-zÀ-ÿ\s]+?)(?:\s+(?:oggi|domani|dopodomani|mattina|pomeriggio|sera|notte|$))", user_input_lower)
                
                if city_match:
                    parsed_dict["city"] = city_match.group(1).strip().capitalize()
                    print(f"[DEBUG] Città estratta manualmente: {parsed_dict['city']}")
                else:
                    parsed_dict["city"] = None

            # Estrazione aggiuntiva di time_of_day (se non è stato trovato nel parsing iniziale)
            if parsed_dict["time_of_day"] is None:
                user_input_lower = user_input.lower()
                time_match = re.search(r"(?:alle|verso le|ore)\s*(\d{1,2})", user_input_lower)
                if time_match:
                    hour = int(time_match.group(1))
                    if 5 <= hour <= 11:
                        parsed_dict["time_of_day"] = "morning"
                    elif 12 <= hour <= 17:
                        parsed_dict["time_of_day"] = "afternoon"
                    else:
                        parsed_dict["time_of_day"] = "evening"
                elif any(x in user_input_lower for x in ["mattina", "stamattina"]):
                    parsed_dict["time_of_day"] = "morning"
                elif any(x in user_input_lower for x in ["pomeriggio", "oggi pomeriggio"]):
                    parsed_dict["time_of_day"] = "afternoon"
                elif any(x in user_input_lower for x in ["sera", "stasera", "notte"]):
                    parsed_dict["time_of_day"] = "evening"

            # Estrazione aggiuntiva di metrics (se non è stato trovato nel parsing iniziale)
            if not parsed_dict["metrics"]:
                user_input_lower = user_input.lower()
                metrics = []
                if "temperatura" in user_input_lower or "caldo" in user_input_lower or "freddo" in user_input_lower:
                    metrics.append("temperature")
                if "umidità" in user_input_lower:
                    metrics.append("humidity")  
                if "pressione" in user_input_lower:
                    metrics.append("pressure")
                if "vento" in user_input_lower:
                    metrics.append("wind_speed")
                if "qualità dell'aria" in user_input_lower:
                    metrics.append("air_quality")
                
                if metrics:
                    parsed_dict["metrics"] = metrics
                else:
                    parsed_dict["metrics"] = ["temperature"]

            # Verifica finale della validità
            parsed_dict["valid"] = bool(parsed_dict.get("city"))
            if not parsed_dict["valid"]:
                parsed_dict["missing_parameters"] = parsed_dict.get("missing_parameters", []) + ["city"]

            # Crea l'oggetto WeatherRequest dal dizionario
            weather_request = WeatherRequest(**parsed_dict)
            print(f"[DEBUG] Oggetto WeatherRequest Pydantic:\n{weather_request}\n")
            return weather_request

        except ValidationError as ve:
            print(f"[ERROR] Errore di validazione Pydantic: {ve}")
            return None
        except Exception as e:
            print(f"[ERROR] Errore durante il parsing: {e}")
            return None