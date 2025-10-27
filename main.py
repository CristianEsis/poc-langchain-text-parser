from fastapi import FastAPI
from Management_Functions.Managment_functions import error_manager
from Models_Manager.models_esteso import User, UserAuth
from User_Management.login import login_user, register_new_user
from User_Management.manage_data import read_user, update_user, delete_user
from CitiesManager.Cities_esteso import add_city, list_of_city
#from langchain_core.chat_history import InMemoryChatMessageHistory da rivedere
from llm import question_answer

app = FastAPI(
    title="My FastAPI App",
    description="Un progetto FastAPI minimale, pronto per crescere.",
    version="0.1.0"
)

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