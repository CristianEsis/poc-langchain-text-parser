from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

# Variabile globale per memorizzare gli utenti
users_db = [
    {"id": 1, "email": "mario@example.com", "name": "Mario Rossi"},
    {"id": 2, "email": "luigi@example.com", "name": "Luigi Verdi"}
]

# Modello utente
class User(BaseModel):
    id: Optional[int] = None
    email: str
    name: str

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

# DELETE - Cancella un utente
@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    for i, user in enumerate(users_db):
        if user["id"] == user_id:
            deleted_user = users_db.pop(i)
            return {"message": "Utente eliminato", "user": deleted_user}
# READ - Ottieni tutti gli utenti
@app.get("/users", response_model=List[User])
def read_users():
    return users_db

@app.get("/users/{user_id}", response_model=User)
def read_user(user_id: int):
    for user in users_db:
        if user["id"] == user_id:
            return user
    raise HTTPException(status_code=404, detail="Utente non trovato")

@app.post("/users/create_user")
def create_user(user: User):
    for utente in users_db:
        if utente["id"] == user.id:
            raise HTTPException(status_code=400, detail="L'ID utente esiste già")
    users_db.append(user.model_dump())
    return user

@app.put("/users/{user_id}")
def update_user(user_id: int, updated_user: User):
    for user in users_db:
        if user["id"] == user_id:
            user.update(updated_user.dict(exclude_unset=True))
            return {"msg": f"Utente con id {user_id} aggiornato con successo!", "user": user}
    raise HTTPException(status_code=404, detail=f"Utente con id {user_id} non trovato.")
