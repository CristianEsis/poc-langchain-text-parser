import pandas as pd
import numpy as np
import re
import requests
import json
import os
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WeatherService:
    """Servizio meteo con dispatching basato su continenti, utilizzando OpenWeatherMap API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.dataset_path = "CityCountryContinent.xlsx"
        self.cities_df = None
    
        # Carica il dataset
        self.load_cities_dataset()
    
        # USA SOLO L'API REALE DI OPENWEATHERMAP
        self.weather_api_url = "https://api.openweathermap.org/data/2.5/weather"
    
        # Parametri per ogni continente (solo per localizzazione)
        self.continent_params = {
        "Asia": {"lang": "zh", "units": "metric"},
        "Africa": {"lang": "fr", "units": "metric"},
        "North America": {"lang": "en", "units": "imperial"},
        "South America": {"lang": "es", "units": "metric"},
        "Europe": {"lang": "de", "units": "metric"},
        "Oceania": {"lang": "en", "units": "metric"},
        "Seven seas (open ocean)": {"lang": "en", "units": "metric"}
    }
    def load_cities_dataset(self):
        """Carica il dataset delle città dal file Excel"""
        try:
            if os.path.exists(self.dataset_path):
                self.cities_df = pd.read_excel(self.dataset_path)
                logger.info(f"Dataset caricato con successo. Numero di città: {len(self.cities_df)}")
            else:
                logger.error(f"File dataset non trovato: {self.dataset_path}")
                self.cities_df = pd.DataFrame(columns=['City', 'Country', 'Continent'])
        except Exception as e:
            logger.error(f"Errore nel caricamento del dataset: {e}")
            self.cities_df = pd.DataFrame(columns=['City', 'Country', 'Continent'])
    
    def extract_city(self, request_text: str) -> str:
        request_text = request_text.lower().strip()
        
        # Cerca pattern comuni per città
        patterns = [
            r"tempo\s+a\s+([a-z\s]+)",
            r"meteo\s+([a-z\s]+)",
            r"a\s+([a-z\s]+)",
            r"([a-z\s]+)\?",
            r"([a-z\s]+)\s+tempo",
            r"([a-z\s]+)\s+meteo"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, request_text)
            if match:
                city_candidate = match.group(1).strip().title()
                # Verifica se la città esiste nel dataset
                if self.cities_df is not None:
                    matches = self.cities_df[self.cities_df['City'].str.lower() == city_candidate.lower()]
                    if not matches.empty:
                        return matches.iloc[0]['City']
        
        # Fallback per città comuni
        common_cities = ["Tokyo", "Roma", "New York", "Londra", "Parigi", "Berlino", "Sydney", "Rio de Janeiro", "Cairo"]
        for city in common_cities:
            if city.lower() in request_text:
                return city
        
        return common_cities  # Fallback predefinito
        
    def get_continent_for_city(self, city_name: str) -> str:
        """Determina il continente per una città data usando il dataset"""
        if self.cities_df is None or self.cities_df.empty:
            return "Europe"  # Fallback
        
        # Cerca corrispondenza esatta
        exact_match = self.cities_df[self.cities_df['City'].str.lower() == city_name.lower()]
        if not exact_match.empty:
            return exact_match.iloc[0]['Continent']
        
        # Cerca corrispondenza parziale
        partial_match = self.cities_df[self.cities_df['City'].str.contains(city_name, case=False)]
        if not partial_match.empty:
            return partial_match.iloc[0]['Continent']
        
        # Fallback per città comuni
        common_cities = {
            "Roma": "Europe",
            "Milano": "Europe",
            "New York": "North America",
            "Tokyo": "Asia",
            "Londra": "Europe",
            "Parigi": "Europe",
            "Berlino": "Europe",
            "Sydney": "Oceania",
            "Rio de Janeiro": "South America",
            "Cairo": "Africa"
        }
        
        return common_cities.get(city_name, "Europe")
    
    def get_weather_data(self, city: str, continent: str) -> Dict[str, Any]:
        """Recupera i dati meteo da OpenWeatherMap API per una città specifica"""
        try:
            # Usa sempre lo stesso endpoint API
            api_url = self.weather_api_url
            
            # Ottieni i parametri per il continente
            params = self.continent_params.get(continent, self.continent_params["Europe"])
            
            # Aggiungi parametri specifici per la chiamata
            params.update({
                "q": city,
                "appid": self.api_key,
                "units": params.get("units", "metric")  # Mantieni le unità specifiche per continente
            })
            
            logger.info(f"Chiamata API OpenWeatherMap: {api_url} con parametri {params}")
            response = requests.get(api_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Dati meteo ricevuti per {city}")
            
            # Estrai i dati rilevanti con gestione errori
            weather_data = {
                "temperature": data["main"].get("temp", "N/A"),
                "feels_like": data["main"].get("feels_like", "N/A"),
                "humidity": data["main"].get("humidity", "N/A"),
                "pressure": data["main"].get("pressure", "N/A"),
                "wind_speed": data["wind"].get("speed", "N/A"),
                "wind_direction": data["wind"].get("deg", "N/A"),
                "conditions": data["weather"][0].get("description", "N/A"),
                "icon": data["weather"][0].get("icon", "N/A"),
                "country": data["sys"].get("country", "N/A"),
                "sunrise": datetime.fromtimestamp(data["sys"].get("sunrise", 0)).strftime("%H:%M") if data["sys"].get("sunrise") else "N/A",
                "sunset": datetime.fromtimestamp(data["sys"].get("sunset", 0)).strftime("%H:%M") if data["sys"].get("sunset") else "N/A",
                "source_api": "OpenWeatherMap",
                "continent": continent,
                "city": city
            }
            
            return weather_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Errore nella chiamata API OpenWeatherMap: {e}")
            return {
                "error": "Errore nella chiamata API meteo",
                "message": str(e),
                "source_api": "OpenWeatherMap",
                "continent": continent,
                "city": city
            }
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"Errore nell'elaborazione della risposta API: {e}")
            return {
                "error": "Errore nell'elaborazione dei dati meteo",
                "message": str(e),
                "source_api": "OpenWeatherMap",
                "continent": continent,
                "city": city
            }
    def process_request(self, user_request: str) -> Dict[str, Any]:
        """Processa una richiesta utente e restituisce i dati meteo"""
        start_time = datetime.now()
        
        # 1. Estrai la città dalla richiesta
        city = self.extract_city(user_request)
        logger.info(f"Città estratta: {city}")
        
        # 2. Determina il continente
        continent = self.get_continent_for_city(city)
        logger.info(f"Continente determinato: {continent}")
        
        # 3. Ottieni dati meteo dall'API corretta
        weather_data = self.get_weather_data(city, continent)
        
        # 4. Costruisci la risposta
        response = {
            "richiesta_originale": user_request,
            "citta": city,
            "continente": continent,
            "dati_meteo": weather_data,
            "servizio_utilizzato": self.continent_apis[continent],
            "parametri_utilizzati": self.continent_params[continent],
            "tempo_elaborazione_ms": (datetime.now() - start_time).total_seconds() * 1000,
            "timestamp": datetime.now().isoformat()
        }
        
        return response

# Modelli Pydantic per FastAPI
class WeatherRequest(BaseModel):
    richiesta: str

class WeatherResponse(BaseModel):
    richiesta_originale: str
    citta: str
    continente: str
    dati_meteo: Dict[str, Any]
    servizio_utilizzato: str
    parametri_utilizzati: Dict[str, Any]
    tempo_elaborazione_ms: float
    timestamp: str

# Configurazione FastAPI
app = FastAPI(
    title="Weather Dispatching API",
    description="API con sistema di dispatching per continenti che utilizza OpenWeatherMap",
    version="1.0.0"
)

# Carica la chiave API da variabile d'ambiente o usa un valore di default
API_KEY = os.getenv("OPENWEATHER_API_KEY", "your_openweather_api_key_here")

# Inizializza il servizio meteo
weather_service = WeatherService(API_KEY)

@app.post("/weather", response_model=WeatherResponse, summary="Ottieni informazioni meteo con dispatching per continenti")
async def get_weather(request: WeatherRequest):
    """
    Endpoint per richiedere informazioni meteo.
    
    Il sistema:
    1. Estrae la città dalla richiesta in linguaggio naturale
    2. Determina il continente della città
    3. Effettua la chiamata all'API di OpenWeatherMap appropriata per quel continente
    4. Restituisce i dati meteo formattati
    
    Esempio di richiesta:
    {
        "richiesta": "Che tempo fa a Tokyo?"
    }
    """
    try:
        if not request.richiesta.strip():
            raise HTTPException(status_code=400, detail="La richiesta non può essere vuota")
        
        return weather_service.process_request(request.richiesta)
        
    except Exception as e:
        logger.error(f"Errore nell'elaborazione della richiesta: {e}")
        raise HTTPException(status_code=500, detail=f"Errore interno del server: {str(e)}")

@app.get("/health")
async def health_check():
    """Verifica lo stato del servizio"""
    return {
        "status": "ok",
        "service": "Weather Dispatching API",
        "dataset_loaded": weather_service.cities_df is not None and not weather_service.cities_df.empty,
        "api_key_configured": bool(API_KEY and API_KEY != "your_openweather_api_key_here")
    }

@app.get("/continents")
async def get_continents():
    """Restituisce la lista dei continenti supportati"""
    return {
        "continents": list(weather_service.continent_apis.keys()),
        "api_endpoints": weather_service.continent_apis
    }

@app.get("/city/{city_name}")
async def get_city_info(city_name: str):
    """Restituisce informazioni su una città specifica dal dataset"""
    if weather_service.cities_df is None or weather_service.cities_df.empty:
        raise HTTPException(status_code=503, detail="Dataset delle città non disponibile")
    
    matches = weather_service.cities_df[weather_service.cities_df['City'].str.lower() == city_name.lower()]
    
    if matches.empty:
        raise HTTPException(status_code=404, detail=f"Città '{city_name}' non trovata nel dataset")
    
    city_info = matches.iloc[0].to_dict()
    return {
        "city": city_info['City'],
        "country": city_info['Country'],
        "continent": city_info['Continent'],
        "latitude": city_info.get('Latitude', None),
        "longitude": city_info.get('Longitude', None)
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Avvio del server FastAPI...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
