import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
from sklearn.pipeline import Pipeline
import joblib
import os
import re
from typing import Dict, Any
import requests
from datetime import datetime

class ContinentClassifier:
    """Classificatore per determinare il continente basato su richieste meteo"""
    
    def __init__(self, api_key: str = "2300cb7362ef7560c3e75c5b6aa48b2c"):
        self.api_key = api_key
        self.model = None
        self.vectorizer = None
        self.dataset_path = "data/city_dataset.xlsx"
        self.model_path = "models/continent_classifier.pkl"
        self.cities_df = None
        
        # Carica il dataset delle città
        if os.path.exists(self.dataset_path):
            self.load_cities_dataset()
        
        # Carica il modello se esiste
        if os.path.exists(self.model_path):
            self.load_model()
    
    def load_cities_dataset(self):
        """Carica il dataset delle città dal file Excel"""
        try:
            self.cities_df = pd.read_excel(self.dataset_path)
            print(f"Dataset caricato con successo. Numero di città: {len(self.cities_df)}")
        except Exception as e:
            print(f"Errore nel caricamento del dataset: {e}")
            self.cities_df = None
    
    def create_training_dataset(self) -> pd.DataFrame:
        """Crea un dataset di addestramento basato sulle città nel dataset"""
        if self.cities_df is None:
            raise ValueError("Dataset delle città non caricato")
        
        dataset = []
        continenti = self.cities_df['Continent'].unique()
        
        for _, row in self.cities_df.iterrows():
            city = row['City']
            continent = row['Continent']
            country = row['Country']
            
            # Genera diverse varianti di richieste per la stessa città
            templates = [
                f"Che tempo fa a {city}?",
                f"Meteo {city} oggi",
                f"Previsioni meteorologiche per {city}",
                f"Com'è il clima a {city}?",
                f"Temperatura attuale a {city}",
                f"Umidità e vento a {city}",
                f"Che tempo ci sarà domani a {city}?",
                f"Previsioni per il weekend a {city}",
                f"Condizioni meteo a {city} questa settimana",
                f"Informazioni meteo dettagliate per {city}",
                f"Come sarà il tempo a {city} dopodomani?",
                f"Quanti gradi ci sono a {city}?",
                f"Pioggia prevista a {city}?",
                f"Meteo in {country} a {city}",
                f"Servizio meteorologico per {city}"
            ]
            
            for template in templates:
                dataset.append({
                    "request_text": template,
                    "city": city,
                    "country": country,
                    "continent": continent
                })
        
        return pd.DataFrame(dataset)
    
    def train_model(self) -> Dict[str, float]:
        """Addestra il modello di classificazione sui dati"""
        if self.cities_df is None:
            self.load_cities_dataset()
        
        # Crea il dataset di addestramento
        df = self.create_training_dataset()
        
        # Dividi il dataset in training e test
        X_train, X_test, y_train, y_test = train_test_split(
            df['request_text'], df['continent'], test_size=0.2, random_state=42
        )
        
        # Crea la pipeline con TF-IDF e Random Forest
        self.model = Pipeline([
            ('vectorizer', TfidfVectorizer(
                max_features=5000,
                ngram_range=(1, 2),
                stop_words='english'
            )),
            ('classifier', RandomForestClassifier(
                n_estimators=200, 
                random_state=42, 
                class_weight='balanced',
                n_jobs=-1
            ))
        ])
        
        # Addestra il modello
        print("Addestramento del modello in corso...")
        self.model.fit(X_train, y_train)
        
        # Valuta il modello
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"\n{'='*60}")
        print(f"ACCURATEZZA DEL MODELLO: {accuracy:.4f}")
        print(f"{'='*60}")
        print("\nReport di classificazione per continente:")
        print(classification_report(y_test, y_pred))
        
        # Salva il modello
        self.save_model()
        
        return {"accuracy": accuracy}
    
    def save_model(self):
        """Salva il modello addestrato"""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(self.model, self.model_path)
        print(f"Modello salvato in: {self.model_path}")
    
    def load_model(self):
        """Carica il modello salvato"""
        if not os.path.exists(self.model_path):
            print("Modello non trovato. Addestrare prima il modello.")
            return False
        
        self.model = joblib.load(self.model_path)
        print(f"Modello caricato da: {self.model_path}")
        return True
    
    def predict_continent(self, request_text: str) -> str:
        """Predice il continente per una richiesta meteo"""
        if self.model is None and not self.load_model():
            raise ValueError("Modello non caricato e impossibile da caricare")
        
        # Estrai la città dalla richiesta
        city = self.extract_city(request_text)
        
        # Usa il modello per predire il continente
        prediction = self.model.predict([request_text])[0]
        return prediction, city
    
    def extract_city(self, request_text: str) -> str:
        """Estrae il nome della città da una richiesta in linguaggio naturale"""
        # Estrai potenziali nomi di città usando regex
        city_match = re.search(r"(?:a|in|di|presso|vicino a)\s+([A-Za-zÀ-ÿ\s]+?)(?:\?|,|\.|$)", request_text.lower())
        
        if city_match:
            city_candidate = city_match.group(1).strip().capitalize()
            
            # Verifica se la città è nel nostro dataset
            if self.cities_df is not None:
                # Cerca corrispondenze approssimative
                matches = self.cities_df[self.cities_df['City'].str.lower() == city_candidate.lower()]
                if not matches.empty:
                    return matches.iloc[0]['City']
            
            return city_candidate
        
        # Se non trova una città esplicita, prova a trovare parole che potrebbero essere nomi di città
        words = re.findall(r'[A-Z][a-z]+', request_text)
        if words:
            for word in words:
                if len(word) > 3:  # Filtra parole troppo corte
                    if self.cities_df is not None:
                        matches = self.cities_df[self.cities_df['City'].str.lower() == word.lower()]
                        if not matches.empty:
                            return matches.iloc[0]['City']
            return words[0]  # Ritorna la prima parola che inizia con maiuscola
        
        return "Roma"  # Valore di default
    
    def simulate_weather_service(self, continent: str, city: str, request_text: str = "") -> Dict[str, Any]:
        """Simula la chiamata al servizio meteo specifico per continente"""
        
        # Mappa dei servizi per continente
        services = {
            "Asia": "https://asia-weather-service.example.com/api",
            "Africa": "https://africa-weather-service.example.com/api",
            "North America": "https://north-america-weather-service.example.com/api",
            "South America": "https://south-america-weather-service.example.com/api",
            "Europe": "https://europe-weather-service.example.com/api",
            "Oceania": "https://oceania-weather-service.example.com/api",
            "Seven seas (open ocean)": "https://ocean-weather-service.example.com/api"
        }
        
        # Simula risposte realistiche per ogni continente
        weather_responses = {
            "Asia": {
                "temperature": np.random.uniform(25, 35),
                "humidity": np.random.uniform(70, 90),
                "conditions": "Caldo e umido",
                "source": "Asian Meteorological Agency"
            },
            "Africa": {
                "temperature": np.random.uniform(28, 40),
                "humidity": np.random.uniform(40, 70),
                "conditions": "Caldo e secco",
                "source": "African Climate Service"
            },
            "North America": {
                "temperature": np.random.uniform(15, 30),
                "humidity": np.random.uniform(50, 80),
                "conditions": "Variabile",
                "source": "North American Weather Network"
            },
            "South America": {
                "temperature": np.random.uniform(22, 32),
                "humidity": np.random.uniform(60, 85),
                "conditions": "Tropicale",
                "source": "South American Meteorological Service"
            },
            "Europe": {
                "temperature": np.random.uniform(10, 25),
                "humidity": np.random.uniform(55, 75),
                "conditions": "Temperato",
                "source": "European Weather Service"
            },
            "Oceania": {
                "temperature": np.random.uniform(18, 28),
                "humidity": np.random.uniform(65, 85),
                "conditions": "Mite",
                "source": "Oceanic Weather Bureau"
            },
            "Seven seas (open ocean)": {
                "temperature": np.random.uniform(15, 25),
                "humidity": np.random.uniform(75, 95),
                "conditions": "Marittimo",
                "source": "Marine Weather Service"
            }
        }
        
        # Simula un ritardo di elaborazione diverso per ogni continente
        delays = {
            "Asia": 0.15,
            "Africa": 0.25,
            "North America": 0.1,
            "South America": 0.2,
            "Europe": 0.05,
            "Oceania": 0.3,
            "Seven seas (open ocean)": 0.4
        }
        
        import time
        time.sleep(delays.get(continent, 0.2))
        
        # Ottieni la risposta simulata
        response = weather_responses.get(continent, weather_responses["Europe"])
        
        # Formatta i valori
        response["temperature"] = round(response["temperature"], 1)
        response["humidity"] = round(response["humidity"], 0)
        
        # Aggiungi metadati
        response["continent"] = continent
        response["city"] = city
        response["service_url"] = services.get(continent, services["Europe"])
        response["service_response_time_ms"] = round(delays.get(continent, 0.2) * 1000, 1)
        response["timestamp"] = datetime.now().isoformat()
        
        # Genera una descrizione naturale
        response["human_description"] = (
            f"A {city} ({continent}) ci sono {response['temperature']}°C "
            f"con condizioni {response['conditions'].lower()}. "
            f"Umidità: {int(response['humidity'])}%."
        )
        
        return response

# Script principale per addestramento e test
if __name__ == "__main__":
    print("🚀 Sistema di Dispatching Meteo basato su ML")
    print("=" * 60)
    
    # Inizializza il classificatore
    classifier = ContinentClassifier()
    
    # Addestra il modello
    print("\n🔧 Addestramento del modello di classificazione...")
    results = classifier.train_model()
    
    # Test con alcuni esempi
    print("\n🔍 Test del modello con richieste di esempio:")
    test_requests = [
        "Che tempo fa a Tokyo?",
        "Meteo Roma oggi",
        "Previsioni per New York domani",
        "Come sarà il clima a Sydney?",
        "Temperatura attuale al Cairo",
        "Previsioni meteo per Rio de Janeiro",
        "Che tempo fa a Vancouver?"
    ]
    
    print("\n" + "=" * 60)
    for req in test_requests:
        continent, city = classifier.predict_continent(req)
        weather_data = classifier.simulate_weather_service(continent, city)
        
        print(f"\nRichiesta: '{req}'")
        print(f"Città estratta: {city}")
        print(f"Continente predetto: {continent}")
        print(f"Descrizione: {weather_data['human_description']}")
        print("-" * 40)
    
    print("\n✅ Addestramento completato! Il modello è pronto per l'uso.")
    print(f"📁 Percorso modello: {classifier.model_path}")
