import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import os
import re

class ContinentClassifier:
    """Classificatore ML per determinare il continente da una richiesta testuale"""
    
    def __init__(self, dataset_path="CityCountryContinent.xlsx"):
        self.dataset_path = dataset_path
        self.model_path = "continent_classifier.pkl"
        self.vectorizer_path = "tfidf_vectorizer.pkl"
        self.cities_df = None
        self.model = None
        self.vectorizer = None
        
    def load_dataset(self):
        """Carica il dataset delle città"""
        if not os.path.exists(self.dataset_path):
            raise FileNotFoundError(f"Dataset non trovato: {self.dataset_path}")
        
        self.cities_df = pd.read_excel(self.dataset_path)
        print(f"Dataset caricato con {len(self.cities_df)} città")
    
    def create_training_data(self):
        """Crea dati di addestramento per il classificatore"""
        if self.cities_df is None:
            self.load_dataset()
        
        # Rimuovi righe con valori mancanti
        df = self.cities_df.dropna(subset=['City', 'Continent'])
        
        training_data = []
        
        # Crea diverse varianti di richieste per ogni città
        for _, row in df.iterrows():
            city = row['City']
            continent = row['Continent']
            
            templates = [
                f"Che tempo fa a {city}?",
                f"Meteo di {city} oggi",
                f"Previsioni per {city} domani",
                f"Come sarà il clima a {city}?",
                f"Temperatura attuale a {city}",
                f"Vento e umidità a {city}",
                f"Che tempo ci sarà a {city} questo weekend?",
                f"Meteo {city} per la prossima settimana",
                f"Condizioni atmosferiche a {city}",
                f"Informazioni meteo per {city}"
            ]
            
            for template in templates:
                training_data.append({
                    'text': template,
                    'continent': continent
                })
        
        return pd.DataFrame(training_data)
    
    def train_model(self):
        """Addestra il modello di classificazione"""
        df = self.create_training_data()
        print(f"Creato dataset di addestramento con {len(df)} esempi")
        
        # Dividi il dataset
        X_train, X_test, y_train, y_test = train_test_split(
            df['text'], df['continent'], test_size=0.2, random_state=42
        )
        
        # Crea e addestra il vettorizzatore TF-IDF
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            stop_words='english'
        )
        
        X_train_vec = self.vectorizer.fit_transform(X_train)
        X_test_vec = self.vectorizer.transform(X_test)
        
        # Crea e addestra il classificatore
        self.model = RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            class_weight='balanced',
            n_jobs=-1
        )
        
        self.model.fit(X_train_vec, y_train)
        
        # Valuta il modello
        y_pred = self.model.predict(X_test_vec)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"Accuratezza del modello: {accuracy:.4f}")
        print("\nReport di classificazione:")
        print(classification_report(y_test, y_pred))
        
        # Salva il modello e il vettorizzatore
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.vectorizer, self.vectorizer_path)
        print(f"Modello salvato in: {self.model_path}")
        print(f"Vettorizzatore salvato in: {self.vectorizer_path}")
    
    def load_model(self):
        """Carica il modello e il vettorizzatore salvati"""
        if not os.path.exists(self.model_path) or not os.path.exists(self.vectorizer_path):
            print("Modello o vettorizzatore non trovati. Addestrare prima il modello.")
            return False
        
        self.model = joblib.load(self.model_path)
        self.vectorizer = joblib.load(self.vectorizer_path)
        print("Modello e vettorizzatore caricati con successo")
        return True
    
    def predict_continent(self, text):
        """Predice il continente per una richiesta testuale"""
        if self.model is None or self.vectorizer is None:
            if not self.load_model():
                return "Europe"  # Fallback
        
        # Prepara il testo
        X_vec = self.vectorizer.transform([text])
        
        # Predici il continente
        prediction = self.model.predict(X_vec)[0]
        return prediction

if __name__ == "__main__":
    classifier = ContinentClassifier()
    classifier.train_model()
    
    # Test del modello
    test_requests = [
        "Che tempo fa a Tokyo?",
        "Meteo Roma oggi",
        "Previsioni per New York domani",
        "Come sarà il clima al Cairo?",
        "Temperatura attuale a Sydney"
    ]
    
    print("\nTest del modello:")
    for req in test_requests:
        continent = classifier.predict_continent(req)
        print(f"Richiesta: '{req}' -> Continente previsto: {continent}")
