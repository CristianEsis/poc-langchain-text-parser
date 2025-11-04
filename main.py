from fastapi import FastAPI, HTTPException
from Management_Functions.Managment_functions import error_manager
from Models_Manager.models import User, UserAuth
from User_Management.login import login_user, register_new_user,perform_logout
from User_Management.manage_data import read_user, update_user, delete_user
from CitiesManager.Cities import add_city, list_of_city
#from langchain_core.chat_history import InMemoryChatMessageHistory da rivedere
from llm import question_answer
from main_weather import main
from langchain_ollama import ChatOllama
from weather_service import WeatherService
from datetime import datetime
from continent_classifier import ContinentClassifier
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import time


app = FastAPI(
    title="My FastAPI App",
    description="Un progetto FastAPI minimale, pronto per crescere.",
    version="0.1.0"
)
# Carica il classificatore all'avvio
classifier = ContinentClassifier()
classifier.load_model()
print("Classificatore continentale caricato e pronto")

class WeatherRequest(BaseModel):
    richiesta: str

class DispatchResponse(BaseModel):
    richiesta_originale: str
    continente_rilevato: str
    citta: str
    servizio_destinazione: str
    dati_meteo: Dict[str, Any]
    tempo_elaborazione_ms: float
    timestamp: str

@app.get("/")
def read_root():
    return {"message": "Benvenuto nella mia API 🚀, questa è la root. Per la documentazione relativa al programma, visita http://127.0.0.1:8000/docs"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/user/register", summary = "Registra un nuovo utente", description = "Aggiungi un id, il tuo nome,email e password per registrare il tuo account", tags = ["Utenti"])
def register_user_retrieve(user: User):
    try:
        return register_new_user(user)
    except Exception as e:
        return error_manager(e)

@app.post("/user/login",summary="Si accede all'account creato", description="Aggiungi email e password per accedere all'account", tags=["Utenti"])
def login_user_retrive(user: User):
    try:    
        return login_user(user)
    except Exception as e:
        return error_manager(e)
    
@app.post("/user/logout", summary="Logout utente", description="Chiude la sessione dell'utente loggato e resetta lo stato", tags=["Utenti"])
def logout_user(auth: UserAuth):
    try:    
        return perform_logout(auth)
    except Exception as e:
        return error_manager(e)
    
@app.post("/user", summary = "Elenca le tue informazioni personali", tags = ["Utenti"])
def read_user_retrieve(auth: UserAuth):
    try:
        return read_user(auth)
    except Exception as e:
        return error_manager(e)

@app.put("/users/{user_id}", summary = "Aggiorna i tuoi dati", description = "Inserisci l'id e i tuoi dati(email e password per confermare che sia tu) e poi inserire le informazioni da aggiornare", tags = ["Utenti"])
def update_user_retrieve(user_id: int, auth: UserAuth, updated_user: User):
    try:
        return update_user(user_id, auth, updated_user)
    except Exception as e:
        return error_manager(e)

@app.delete("/users/{user_id}", summary = "Cancella un tuo account", description = "Inserisci l'id e i tuoi dati(email e password per confermare che sia tu) per avviare la fase di cancellazione dell'acount", tags = ["Utenti"])
def delete_user_retrieve(user_id: int,  auth: UserAuth):
    try:
        return delete_user(user_id, auth)
    except Exception as e:
        return error_manager(e)

@app.post("/city/add", summary = 'Aggiungi le città di cui vuoi sapere le informazioni(max 5)', description='Questa funzionalità permette di aggiungere massimo 5 città, nel caso si aggiungessero piu città il programma rimuoverà la tua ultima città aggiunta\n{"email": "la tua email", "password": "la tua password", "city_name": "la città che vuoi aggiungere"}\n RICORDATI DI ESSERE LOGGATO', tags=["Città"])
def add_city_retrieve(user_data: dict):
    try:
        return add_city(user_data)
    except Exception as e:
        return error_manager(e)

@app.get("/city/list",summary = "Ti elencherà le 5 città cercate", description="Questa funzionalità permette di elencarti le prime 5 città cercate", tags=["Città"])
def list_of_city_retrieve(auth: UserAuth):
    try:
        return list_of_city(auth)
    except Exception as e:
        return error_manager(e)

@app.post("/ask")
def ask_domanda(payload: dict):
    domanda = payload.get("domanda", "")
    if not domanda:
        return {"error": "Nessuna domanda fornita"}
    risposta = question_answer(domanda)
    return {"domanda": domanda, "risposta": risposta}

def clean_response(text: str) -> str:
    """Pulisce la risposta da caratteri di escape"""
    # Sostituisci \\n con spazi
    text = text.replace('\\n', ' ')
    # Rimuovi spazi multipli
    import re
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

@app.post("/weather", response_model=DispatchResponse, summary="Richiedi informazioni meteo con dispatching intelligente")
async def get_weather(request: WeatherRequest):
    """Endpoint per richiedere informazioni meteo con dispatching automatico per continente"""
    
    start_time = time.time()
    
    try:
        # 1. Classifica il continente e estrai la città usando il modello ML
        continente, citta = classifier.predict_continent(request.richiesta)
        
        # 2. Dispatching al servizio appropriato (simulato)
        weather_data = classifier.simulate_weather_service(continente, citta, request.richiesta)
        
        # 3. Calcola il tempo di elaborazione
        processing_time = (time.time() - start_time) * 1000  # in millisecondi
        
        # 4. Costruisci la risposta
        response = DispatchResponse(
            richiesta_originale=request.richiesta,
            continente_rilevato=continente,
            citta=citta,
            servizio_destinazione=weather_data["service_url"],
            dati_meteo=weather_data,
            tempo_elaborazione_ms=round(processing_time, 2),
            timestamp=datetime.now().isoformat()
        )
        
        return response
        
    except Exception as e:
        error_time = (time.time() - start_time) * 1000
        error_details = {
            "error": str(e),
            "message": "Errore durante l'elaborazione della richiesta meteo",
            "timestamp": datetime.now().isoformat(),
            "processing_time_ms": round(error_time, 2)
        }
        
        # Stampa l'errore dettagliato nel log del server
        print(f"[ERROR] {str(e)}")
        print(f"[ERROR DETAILS] {error_details}")
        
        raise HTTPException(
            status_code=500,
            detail=error_details
        )

@app.get("/model/status", summary="Stato del modello di classificazione")
def get_model_status():
    """Restituisce informazioni sul modello di classificazione caricato"""
    
    if classifier.model is None:
        return {
            "status": "not_loaded",
            "message": "Modello non caricato. Eseguire l'addestramento prima.",
            "model_path": classifier.model_path,
            "dataset_path": classifier.dataset_path
        }
    
    return {
        "status": "ready",
        "model_type": "Random Forest Classifier",
        "dataset_info": {
            "source": "CityCountryContinent.xlsx",
            "cities_count": len(classifier.cities_df) if classifier.cities_df is not None else 0,
            "continents_covered": classifier.cities_df['Continent'].unique().tolist() if classifier.cities_df is not None else []
        },
        "last_trained": datetime.fromtimestamp(os.path.getmtime(classifier.model_path)).isoformat() if os.path.exists(classifier.model_path) else "N/A",
        "model_path": classifier.model_path
    }

@app.get("/")
def read_root():
    return {"message": "🌤️ Benvenuto nel sistema di Dispatching Meteo basato su Machine Learning!"}

@app.get("/health")
def health_check():
    model_status = "ready" if classifier.model is not None else "not_ready"
    return {"status": "ok", "classifier_status": model_status}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
