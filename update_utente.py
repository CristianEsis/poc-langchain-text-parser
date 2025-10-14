from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, List, Optional

class User(BaseModel):
    id: Optional[int] = None
    email: Optional[str] = None
    name: Optional[str] = None

app = FastAPI()

list_users = []

@app.put("/update_user")
def update_list(indice: int, new_list: List[Any]):
    if indice < 0 or indice >= len(list_users):
        return {"msg": f"Non esiste la lista {indice}"}
    list_users[indice] = new_list
    return {"msg": f"Lista {indice} aggiornata con successo!"}
