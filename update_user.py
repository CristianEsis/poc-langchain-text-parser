from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

users_db = [
    {"id": 1, "email": "mario@example.com", "name": "Mario Rossi"},
    {"id": 2, "email": "luigi@example.com", "name": "Luigi Verdi"}
]

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

#update the user
@app.put("/update_the_user")
def update_user(index: int, new_list: List[str]):
    if index < 0 or index > len(users_db):
        raise HTTPException(404, detail=f"Non esiste la lista {index}")
    users_db[index] = new_list
    return {"msg": f"Lista {index} aggiornata con successo!"}