from typing import Optional
from pydantic import ValidationError
from langchain_core.prompts import PromptTemplate
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser

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

SCHEMA JSON RICHIESTO:
{{
    "city": "nome_citta",
    "metrics": ["temperature", "humidity", "pressure", "wind_speed", "air_quality"],
    "date_range": {{"from_date": "YYYY-MM-DD", "to": "YYYY-MM-DD"}} oppure null,
    "valid": true,
    "missing_parameters": []
}}

REGOLE IMPORTANTI:
- "city": stringa con il nome della città (obbligatorio)
- "metrics": SEMPRE una lista di stringhe, anche se una sola metrica. Valori possibili: "temperature", "humidity", "pressure", "wind_speed", "air_quality"
- "date_range": se specificato, deve essere un oggetto con "from_date" e "to", altrimenti null
- Se non ci sono metriche specificate, usa: ["temperature"]
- Se non c'è intervallo di date, usa: null

ESEMPI:

Richiesta: "Che tempo fa a Roma?"
Risposta:
{{
    "city": "Roma",
    "metrics": ["temperature"],
    "date_range": null,
    "valid": true,
    "missing_parameters": []
}}

Richiesta: "Dimmi temperatura e umidità a Milano"
Risposta:
{{
    "city": "Milano",
    "metrics": ["temperature", "humidity"],
    "date_range": null,
    "valid": true,
    "missing_parameters": []
}}

Richiesta: "Vorrei i dati meteo di Napoli dal 1 marzo al 31 marzo 2023"
Risposta:
{{
    "city": "Napoli",
    "metrics": ["temperature"],
    "date_range": {{"from_date": "2023-03-01", "to": "2023-03-31"}},
    "valid": true,
    "missing_parameters": []
}}

Richiesta: "Qualità dell'aria e vento a Torino"
Risposta:
{{
    "city": "Torino",
    "metrics": ["air_quality", "wind_speed"],
    "date_range": null,
    "valid": true,
    "missing_parameters": []
}}

ORA ANALIZZA QUESTA RICHIESTA:
Richiesta utente: {user_request}

Risposta (SOLO IL JSON, senza testo aggiuntivo, markdown o spiegazioni):
"""
        return PromptTemplate(
            template=template,
            input_variables=["user_request"]
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
        # Formatta il prompt
            final_prompt = self.prompt.format(user_request=user_input)
            print(f"[DEBUG] Prompt inviato all'LLM (Parsing):\n{final_prompt}\n")

        # Invoca l'LLM
            messages = [HumanMessage(content=final_prompt)]
            llm_output = self.llm.invoke(messages).content
            print(f"[DEBUG] Output LLM (Parsing):\n{llm_output}\n")

        # Parse l'output JSON
            parsed_dict = self.json_parser.parse(llm_output)
            print(f"[DEBUG] Dizionario parsato:\n{parsed_dict}\n")

        # VALIDAZIONE E CORREZIONE DEI TIPI
        # 1. Assicurati che metrics sia una lista
            if "metrics" in parsed_dict:
                if isinstance(parsed_dict["metrics"], dict):
                # Se l'LLM ha restituito un dizionario, converti in lista
                    parsed_dict["metrics"] = list(parsed_dict["metrics"].keys())
                elif isinstance(parsed_dict["metrics"], str):
                # Se è una stringa, mettila in una lista
                    parsed_dict["metrics"] = [parsed_dict["metrics"]]
                elif not isinstance(parsed_dict["metrics"], list):
                # Fallback
                    parsed_dict["metrics"] = ["temperature"]
            else:
                parsed_dict["metrics"] = ["temperature"]
        
        # 2. Gestisci date_range
            if "date_range" in parsed_dict and parsed_dict["date_range"] is not None:
                if isinstance(parsed_dict["date_range"], str):
                # Se è una stringa tipo "2023-03-01-2023-03-31", parsala
                    date_str = parsed_dict["date_range"]
                    if "-" in date_str:
                        parts = date_str.split("-")
                        if len(parts) >= 6:  # YYYY-MM-DD-YYYY-MM-DD
                            from_date = f"{parts[0]}-{parts[1]}-{parts[2]}"
                            to_date = f"{parts[3]}-{parts[4]}-{parts[5]}"
                            parsed_dict["date_range"] = {
                            "from_date": from_date,
                            "to": to_date
                        }
                        else:
                            parsed_dict["date_range"] = None
                    else:
                        parsed_dict["date_range"] = None
                elif not isinstance(parsed_dict["date_range"], dict):
                    parsed_dict["date_range"] = None

        # 3. Valida e correggi la città
            if parsed_dict.get("valid", True) and "city" in parsed_dict:
                city = parsed_dict["city"]
                user_input_lower = user_input.lower()
            
            # Verifica se la città estratta è effettivamente menzionata nella richiesta
                if not city or city.lower() not in user_input_lower:
                # Cerca di estrarre la città usando parole chiave comuni
                    city_keywords = ["a", "in", "di", "presso", "a:", "in:", "città di"]
                    for keyword in city_keywords:
                        if keyword in user_input_lower:
                            parts = user_input_lower.split(keyword)
                            if len(parts) > 1:
                            # Prendi la parte dopo la keyword
                                potential_city = parts[1].strip().split()[0]
                            # Capitalizza la prima lettera
                                potential_city = potential_city.capitalize()
                            # Verifica che non sia una parola comune
                                common_words = ["il", "la", "lo", "i", "le", "gli", "che", "mi", "dica", "tempo", "fa"]
                                if potential_city.lower() not in common_words:
                                    parsed_dict["city"] = potential_city
                                    print(f"[DEBUG] Corretto città da '{city}' a '{potential_city}'")
                                    break

        # Valida e aggiorna i campi
            valid = parsed_dict.get("valid", True)
            missing_params = parsed_dict.get("missing_parameters", [])
        
        # Controlla se è fuori contesto
            if "out_of_context" in missing_params:
                valid = False
            elif not parsed_dict.get("city"):
                valid = False
                if "city" not in missing_params:
                    missing_params.append("city")

        # Aggiorna il dizionario
            parsed_dict["valid"] = valid
            parsed_dict["missing_parameters"] = missing_params
        
        # Crea l'oggetto WeatherRequest dal dizionario
            weather_request = WeatherRequest(**parsed_dict)
            print(f"[DEBUG] Oggetto WeatherRequest Pydantic:\n{weather_request}\n")

            return weather_request

        except ValidationError as ve:
            print(f"[ERROR] Errore di validazione Pydantic: {ve}")
        return None
    