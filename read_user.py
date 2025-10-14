from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from main import User

app = FastAPI()

users_db = [
    {"id": 1, "email": "mario@example.com", "name": "Mario Rossi"},
    {"id": 2, "email": "luigi@example.com", "name": "Luigi Verdi"}
]


# READ - Ottieni tutti gli utenti
@app.get("/users", response_model=List[User])
def read_users():
    return users_db

# READ - Ottieni un utente specifico per ID
@app.get("/users/{user_id}", response_model=User)
def read_user(user_id: int):
    for user in users_db:
        if user["id"] == user_id:
            return user
    raise HTTPException(status_code=404, detail="Utente non trovato")
