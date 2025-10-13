from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


app = FastAPI(
    title="My FastAPI App",
    description="Un progetto FastAPI minimale, pronto per crescere.",
    version="0.1.0")


class User(BaseModel):
    id: int
    email: str
    name: str
    
users = {}

initial_users = [
    User(id="1", email="walter.white@heisenberg.com", name="Walter White"),
    User(id="2", email="jesse.pinkman@cooklab.com", name="Jesse Pinkman"),
    User(id="3", email="saul.goodman@lawfirm.com", name="Saul Goodman")]

@app.post("/users")
def create_user(user: User):
    if user.id is users:
        raise HTTPException(status_code=400, detail="User already exists")
    
    users[user.id] = user
    return {"message": "User created successfully", "user": user}