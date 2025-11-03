import json
from datetime import datetime
from typing import Optional
from langchain_core.language_models import BaseLanguageModel

from models import WeatherRequest
from weather_api import WeatherAPI
from weather_parser import WeatherRequestParser
from response_generator import NaturalLanguageResponseGenerator

class WeatherService:
    """Servizio orchestratore per gestire richieste meteo end-to-end"""    

    def __init__(self, api_key: str, llm: BaseLanguageModel):
        """
        Inizializza il servizio meteo
        
        Args:
            api_key: Chiave API per OpenWeatherMap
            llm: Modello di linguaggio per parsing e generazione risposte
        """
        self.weather_api = WeatherAPI(api_key)
        self.parser = WeatherRequestParser(llm)
        self.response_generator = NaturalLanguageResponseGenerator(llm)
    
    def process_request(self, user_input: str) -> str:
        """
        Processa una richiesta meteo dall'input utente alla risposta finale
        
        Args:
            user_input: La richiesta dell'utente in linguaggio naturale
            
        Returns:
            La risposta finale formattata in linguaggio naturale
        """

        # 1. Parse della richiesta
        print("\n=== FASE 1: PARSING RICHIESTA ===")
        print(f"[DEBUG] Richiesta utente originale: {user_input}")
        
        parsed_request = self.parser.parse(user_input)
        
        if not parsed_request:
            return "Mi dispiace, non sono riuscito a comprendere la tua richiesta. Puoi riformularla?"
        
        # Mostra info sulla richiesta parsata
        self._print_parsed_info(parsed_request)

        # Pre-check per domande fuori contesto
        NON_METEO_KEYWORDS = [
            'ricetta', 'pasta', 'cibo', 'cucinare', 'ingredienti',
            'barzelletta', 'scherzo', 'storia', 'politica', 
            'sport', 'calcio', 'mondiale', 'partita',
            'come si fa', 'preparare'
        ]
        
        METEO_KEYWORDS = ['meteo', 'tempo', 'temperatura', 'clima', 'previsioni', 'pioggia', 'sole', 'vento']
        
        user_input_lower = user_input.lower()
        if any(keyword in user_input_lower for keyword in NON_METEO_KEYWORDS):
            # Controlla se contiene anche parole meteo
            if not any(keyword in user_input_lower for keyword in METEO_KEYWORDS):
                return "Mi dispiace, posso rispondere solo a domande relative al meteo, come temperatura, umidità, previsioni atmosferiche, qualità dell'aria, ecc. La tua richiesta sembra essere fuori dal mio ambito di competenza."

        # 2. Validazione
        if not parsed_request.valid:
            missing = ', '.join(parsed_request.missing_parameters)
            return (
                f"Non è stato possibile elaborare la richiesta perché manca "
                f"la seguente informazione: {missing}. Per favore, fornisci la città."
            )
        
        # 3. Chiamata API
        print("\n=== FASE 2: CHIAMATA API ===")
        print(f"[DEBUG] Chiamata API per città: {parsed_request.city}")
        api_data = self.weather_api.get_all_data_for_city(parsed_request.city)
        
        if not api_data:
            return f"Mi dispiace, non sono riuscito a recuperare i dati meteo per {parsed_request.city}."
        
        # 4. Salvataggio dati (opzionale)
        self._save_data(parsed_request.city, api_data)
        
        # 5. Generazione risposta
        print("\n=== FASE 3: GENERAZIONE RISPOSTA ===")
        final_response = self.response_generator.generate(
            user_input, 
            parsed_request, 
            api_data
        )
        
        return final_response
    
    def _print_parsed_info(self, parsed_request: WeatherRequest):
        """Stampa informazioni sulla richiesta parsata"""
        print("--- Risultato del Parsing ---")
        print(f"Richiesta valida: {parsed_request.valid}")
        
        if not parsed_request.valid:
            print(f"Parametri mancanti: {parsed_request.missing_parameters}")
        
        if parsed_request.city:
            print(f"Città: {parsed_request.city}")
        
        if parsed_request.metrics:
            print(f"Metriche richieste: {parsed_request.metrics}")
        
        if parsed_request.date_range:
            print(f"Intervallo date: dal {parsed_request.date_range.from_date} "
                  f"al {parsed_request.date_range.to}")
    
    def _save_data(self, city: str, api_data: dict):
        """Salva i dati API in un file JSON"""
        filename = f"weather_data_{city}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(api_data, f, indent=2, ensure_ascii=False)
        print(f"Dati salvati in: {filename}")
