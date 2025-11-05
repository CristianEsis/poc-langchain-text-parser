from fastapi import FastAPI, HTTPException
from Management_Functions.Managment_functions import error_manager
from Models_Manager.models import User, UserAuth
from User_Management.login import login_user, register_new_user, perform_logout
from DatabaseJSON.database import read_db
from User_Management.manage_data import read_user, update_user, delete_user
from CitiesManager.Cities import add_city, list_of_city
#from llm import question_answer
from continent_classifier import ContinentClassifier
#from weather_service import WeatherService, WeatherRequestParser  # Importa il parser
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, Dict, Any
import time
from langchain_ollama import ChatOllama  # Assicurati di avere questa importazione
import os
from weather_parser import WeatherRequestParser

# Inizializza l'LLM per il parsing delle richieste meteo
weather_llm = ChatOllama(model="gemma:2b", temperature=0)  # Usa il modello che preferisci
weather_parser = WeatherRequestParser(weather_llm)  # Inizializza il parser


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

@app.get("/city/list",summary = "Ti elencherà le 5 città cercate", description="Questa funzionalità permette di elencarti le prime 5 città cercate", tags=["Città"])
def list_of_city_retrieve(auth: UserAuth):
    try:
        return list_of_city(auth)
    except Exception as e:
        return error_manager(e)

def clean_response(text: str) -> str:
    """Pulisce la risposta da caratteri di escape"""
    # Sostituisci \\n con spazi
    text = text.replace('\\n', ' ')
    # Rimuovi spazi multipli
    import re
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


@app.post("/weather", response_model=DispatchResponse)
async def get_weather(data: dict):
    db = read_db()
    email = data.get("email")
    password = data.get("password")
    domanda = data.get("domanda")

    # Autenticazione utente
    found_user = next((u for u in db if u["email"] == email and u["password"] == password), None)
    if not found_user:
        raise HTTPException(status_code=404, detail="Credenziali errate")

    start_time = time.time()
    try:
        print(f"[DEBUG] Parsing richiesta: {domanda}")
        parsed_request = weather_parser.parse(domanda)
        
        # Controlla se il parser ha restituito None (richiesta non meteo)
        if parsed_request is None:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Richiesta non meteo",
                    "message": "Non posso rispondere a richieste fuori dal contesto meteo. Questo servizio è dedicato esclusivamente alle previsioni meteorologiche.",
                    "richiesta_originale": domanda
                }
            )
        
        # Controlla se la richiesta è valida
        if not parsed_request.valid:
            # Se la richiesta è invalida ma non è "out_of_context", potrebbe essere un problema diverso
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Richiesta incompleta",
                    "message": "Richiesta meteo incompleta. Specificare una città.",
                    "richiesta_originale": domanda
                }
            )
        
        # Procedi con l'elaborazione della richiesta meteo valida
        # ...

    except HTTPException as he:
        raise he
    try:
        # 🔍 PRIMO CONTROLLO: Verifica se è una richiesta meteo
        parsed_request = weather_parser.parse(domanda)
        
        # Gestione richieste non meteo
        if parsed_request is None or not parsed_request.valid:
            # Estrai il motivo dalla richiesta parsata o usa un fallback
            reason = "Richiesta non valida"
            if parsed_request and "out_of_context" in parsed_request.missing_parameters:
                reason = "Richiesta fuori contesto meteorologico"
            
            error_time = (time.time() - start_time) * 1000
            error_details = {
                "error": reason,
                "message": "❌ Non posso rispondere a richieste fuori dal contesto meteo. Questo servizio è dedicato esclusivamente alle previsioni meteorologiche.",
                "richiesta_originale": domanda,
                "timestamp": datetime.now().isoformat(),
                "processing_time_ms": round(error_time, 2)
            }
            print(f"[NON-METEO] Rilevata richiesta non meteo: {domanda}")
            raise HTTPException(status_code=400, detail=error_details)

        # 🌍 Estrai città dal parsing strutturato
        citta = parsed_request.city.strip()
        if not citta:
            raise HTTPException(status_code=400, detail="Città non specificata nella richiesta")

        # Pulisci il nome della città
        prefixes = ["a ", "ad ", "in ", "da ", "di ", "la ", "il ", "a'", "ad'"]
        citta_clean = citta.lower()
        for prefix in prefixes:
            if citta_clean.startswith(prefix):
                citta_clean = citta_clean[len(prefix):].strip()
                break
        citta_clean = citta_clean.capitalize()

        # 🌐 Classifica il continente
        continente, _ = classifier.predict_continent(domanda)
        
        # 🌤️ Simula i dati meteo (sostituisci con chiamata reale a un servizio)
        weather_data = {
            "service_url": f"https://weather.service/{continente}/{citta_clean}",
            "temperature": 22.5,
            "humidity": 65,
            "description": "Soleggiato"
        }

        processing_time = (time.time() - start_time) * 1000

        # 📦 Prepara la risposta
        response = DispatchResponse(
            richiesta_originale=domanda,
            continente_rilevato=continente,
            citta=citta_clean,
            servizio_destinazione=weather_data["service_url"],
            dati_meteo=weather_data,
            tempo_elaborazione_ms=round(processing_time, 2),
            timestamp=datetime.now().isoformat()
        )

        # 💾 Salva la città nella cronologia utente
        add_city(found_user, citta_clean, weather_data)
        return response

    except HTTPException as he:
        # Rilancia gli errori HTTP già gestiti
        raise he
    except Exception as e:
        error_time = (time.time() - start_time) * 1000
        error_details = {
            "error": str(e),
            "message": "Errore durante l'elaborazione della richiesta",
            "timestamp": datetime.now().isoformat(),
            "processing_time_ms": round(error_time, 2)
        }
        print(f"[ERROR] Errore elaborazione meteo: {str(e)}")
        raise HTTPException(status_code=500, detail=error_details)
        
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
