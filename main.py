from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
from json.decoder import JSONDecodeError
import re
from llm import question_answer

def validation_email(email: str):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Modello utente

class User(BaseModel):
    id: int | None = None
    name: str | None = None
    email: str| None = None
    password: str | None = None
    check_login: bool = False
    tentativi: int = 0

app = FastAPI(
    title="My FastAPI App",
    description="Un progetto FastAPI minimale, pronto per crescere.",
    version="0.1.0")

def read_db():
    try:
        with open('lista_utenti_LLM_meteo_cybercats.json', 'r', encoding='utf-8') as f:
            db = json.load(f)
            if not isinstance(db, list):
                db = []
    except (FileNotFoundError, JSONDecodeError):
        db = []
    return db

def update_db(db):
    with open('lista_utenti_LLM_meteo_cybercats.json', 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=4, ensure_ascii=False)


@app.get("/")
def read_root():
    return {"message": "Benvenuto nella mia API 🚀"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

# DELETE - Cancella un utente
@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    db = read_db()
    db = [utente for utente in db if utente.get("id") != user_id]
    update_db(db)
    return {"detail": "Utente cancellato dal file se esistente", "user_id": user_id}

# READ - Ottieni tutti gli utenti
@app.get("/users", response_model=List[User])
def read_users():
    db = read_db()
    return db

@app.get("/users/{user_id}", response_model=User)
def read_user(user_id: int):
    db = read_db()
    for user in db:
        if user["id"] == user_id:
            return user
    raise HTTPException(status_code=404, detail="Utente non trovato")

@app.post("/users/create_user")
def create_user(user: User):
    db = read_db()
    for utente in db:
        if utente["id"] == user.id:
            raise HTTPException(status_code=400, detail="L'ID utente esiste già")
    db.append(user.model_dump())
    update_db(db)
    return {"detail": "Utente salvato", "utente": user.model_dump()}

@app.put("/users/{user_id}")
def update_user(user_id: int, updated_user: User):
    db = read_db()
    for user in db:
        if user["id"] == user_id:
            user.update(updated_user.model_dump(exclude_unset=True))
            update_db(db)
            return {"msg": f"Utente con id {user_id} aggiornato con successo!", "user": user}
    raise HTTPException(status_code=404, detail=f"Utente con id {user_id} non trovato.")

@app.post("/ask")
def ask_domanda(payload: dict):
    domanda = payload.get("domanda", "")
    if not domanda:
        return {"error": "Nessuna domanda fornita"}
    risposta = question_answer(domanda)
    return {"domanda": domanda, "risposta": risposta}