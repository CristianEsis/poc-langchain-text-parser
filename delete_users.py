from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
app = FastAPI()
users_db = []
    
# DELETE - Cancella un utente
@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    for i, user in enumerate(users_db):
        if user["id"] == user_id:
            deleted_user = users_db.pop(i)
            return {"message": "Utente eliminato", "user": deleted_user}
    raise HTTPException(status_code=404, detail="Utente non trovato")
