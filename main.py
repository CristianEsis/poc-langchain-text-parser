from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import json
from json.decoder import JSONDecodeError
import re
from llm import question_answer

ADMIN_EMAIL = "admin@cybercats.it"
ADMIN_PASSWORD = "admin123"
admin_logged = False 

def validation_email(email: str):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def read_db():
    try:
        with open('lista_utenti_LLM_meteo_cybercats.json', 'r', encoding='utf-8') as f:
            db = json.load(f)
            if not isinstance(db, list):
                db = []
    except (FileNotFoundError, JSONDecodeError):
        with open('lista_utenti_LLM_meteo_cybercats.json', 'w', encoding='utf-8') as f:
            json.dump([], f)
        db = []
    return db

def update_db(db):
    with open('lista_utenti_LLM_meteo_cybercats.json', 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=4, ensure_ascii=False)

class User(BaseModel):
    id: int | None = None
    name: str | None = None
    email: str | None = None
    password: str | None = None
    check_login: bool = False
    tentativi: int = 0

class UserAuth(BaseModel):
    email: str
    password: str

app = FastAPI(
    title="My FastAPI App",
    description="Un progetto FastAPI minimale, pronto per crescere.",
    version="0.1.0"
)

@app.get("/")
def read_root():
    return {"message": "Benvenuto nella mia API 🚀"}

@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/user/register", summary="Registra un nuovo utente",description="Aggiungi un id, il tuo nome,email e password per registrare il tuo account",tags=["Utenti"])
def register_new_user(user: User):
    db = read_db()

    if user.tentativi != 0:
        raise HTTPException(status_code=400, detail="Non puoi impostare il valore dei tentativi manualmente")
    if user.check_login is not False:
        raise HTTPException(status_code=400, detail="Non puoi impostare il valore del login manualmente")
    if not user.password:
        raise HTTPException(status_code=400, detail="Password vuota")
    if not validation_email(user.email):
        raise HTTPException(status_code=400, detail="Email non valida")

    for u in db:
        if u["id"] == user.id:
            raise HTTPException(status_code=400, detail="L'ID utente esiste già")

    db.append(user.model_dump())
    update_db(db)
    return {"detail": "Utente registrato con successo", "utente": user.model_dump()}

@app.post("/user/login",summary="Si accede all'account creato",description="Aggiungi email e password per accedere all'account", tags=["Utenti"])
def login_user(user: User):
    global admin_logged
    db = read_db()

    if user.email == ADMIN_EMAIL and user.password == ADMIN_PASSWORD:
        admin_logged = True
        return {"msg": "Login admin effettuato con successo!"}
    
    for u in db:
        if u["email"] == user.email:
            if u["tentativi"] >= 5:
                raise HTTPException(status_code=403, detail="Troppi tentativi falliti, accesso bloccato")

            if u["password"] == user.password:
                u["check_login"] = True
                u["tentativi"] = 0
                update_db(db)
                return {"msg": f"Login effettuato con successo! Benvenuto {u['name']}"}

            u["tentativi"] += 1
            remaining = 5 - u["tentativi"]
            update_db(db)
            raise HTTPException(status_code=401, detail=f"Credenziali errate. Tentativi rimasti: {remaining}")

    raise HTTPException(status_code=401, detail="Email non registrata")

@app.get("/users", summary="Elenca le tue informazioni personali",tags=["Utenti"])
def read_users():
    db = read_db()
    global admin_logged

    if admin_logged:
        return {"msg": "Accesso admin", "utenti": db}

    for u in db:
        if u.get("check_login", False):
            return {
                "id": u["id"],
                "name": u["name"],
                "email": u["email"]
            }

    raise HTTPException(status_code=401, detail="Nessun utente loggato. Effettua il login prima di accedere ai dati.",tags=["Utenti"])

@app.put("/users/{user_id}", summary="Aggiorna i tuoi dati",description="Inserisci l'id e i tuoi dati(email e password per confermare che sia tu) e poi inserire le informazioni da aggiornare",tags=["Utenti"])
def update_user(user_id: int, auth: UserAuth, updated_user: User):
    db = read_db()
    for user in db:
        if user["id"] == user_id:
            if user["email"] != auth.email or user["password"] != auth.password:
                raise HTTPException(status_code=401, detail="Credenziali non valide per aggiornamento")
            updated_data = updated_user.model_dump(exclude_unset=True)

            if "email" in updated_data:
                if not validation_email(updated_data["email"]):
                    raise HTTPException(status_code=400, detail="Nuova email non valida")

            if "check_login" in updated_data or "tentativi" in updated_data:
                raise HTTPException(status_code=400, detail="Non puoi modificare manualmente questi campi")

            user.update(updated_data)
            update_db(db)
            return {"msg": f"Utente con id {user_id} aggiornato con successo!", "user": user}

    raise HTTPException(status_code=404, detail=f"Utente con id {user_id} non trovato.")

@app.delete("/users/{user_id}", summary="Cancella un tuo account",description="Inserisci l'id e i tuoi dati(email e password per confermare che sia tu) per avviare la fase di cancellazione dell'acount",tags=["Utenti"])
def delete_user(user_id: int, auth: UserAuth):
    db = read_db()
    for user in db:
        if user["id"] == user_id:
            if user["email"] != auth.email or user["password"] != auth.password:
                raise HTTPException(status_code=401, detail="Credenziali non valide per cancellazione")
            db.remove(user)
            update_db(db)
            return {"detail": f"Utente con id {user_id} cancellato con successo"}
    raise HTTPException(status_code=404, detail="Utente non trovato")

@app.post("/ask")
def ask_domanda(payload: dict):
    domanda = payload.get("domanda", "")
    if not domanda:
        return {"error": "Nessuna domanda fornita"}
    risposta = question_answer(domanda)
    return {"domanda": domanda, "risposta": risposta}
