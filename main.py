from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
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

app = FastAPI(
    title="My FastAPI App",
    description="Un progetto FastAPI minimale, pronto per crescere.",
    version="0.1.0")

@app.get("/")
def read_root():
    return {"message": "Benvenuto nella mia API 🚀"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
users_db: list[dict] = []

@app.post("/user/register")
def register_new_user(user: User):
    if user.check_login is not False:
        raise HTTPException(status_code=400, detail="Non puoi impostare il valore del login manualmente")
    if not user.password:
            raise HTTPException(status_code=400, detail="Password vuota")
    if not validation_email(user.email):
        raise HTTPException(status_code=400, detail="Email non valida")

    for u in users_db:
        if u["id"] == user.id:
            raise HTTPException(status_code=400, detail="L'ID utente esiste già")
    users_db.append(user.model_dump())
    return user

@app.post("/user/login")
def login_user(user: User):
    global tentativi 
    for u in users_db:
        if u["email"] == user.email and u["password"] == user.password:
            u["check_login"] = True
            tentativi = 0
            return {"msg": f"Login effettuato con successo! Benvenuto {u['name']}"}
    tentativi += 1
    if tentativi >= 5:
        raise HTTPException(status_code=403, detail="Troppi tentativi falliti, accesso bloccato")
    else:
        raise HTTPException(status_code=401, detail=f"Credenziali errate. Tentativi rimasti: {5 - tentativi}")


@app.post("/ask")
def ask_domanda(payload: dict):
    domanda = payload.get("domanda", "")
    if not domanda:
        return {"error": "Nessuna domanda fornita"}
    risposta = question_answer(domanda)
    return {"domanda": domanda, "risposta": risposta}
