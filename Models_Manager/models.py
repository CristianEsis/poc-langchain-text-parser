from pydantic import BaseModel
import json
from typing import Any
#from typing import ClassVar
#from langchain_core.chat_history import InMemoryChatMessageHistory da rivedere

ADMIN_EMAIL = "admin@cybercats.it"
ADMIN_PASSWORD = "admin123"
admin_logged = False 

class User(BaseModel):
    id: int | None = None
    name: str | None = None
    email: str | None = None
    password: str | None = None
    check_login: bool = False
    tentativi: int = 0  
    #chat_history: ClassVar[InMemoryChatMessageHistory] = InMemoryChatMessageHistory() da rivedere

class City(BaseModel):
    city_name: dict[str, Any]

class UserAuth(BaseModel):
    email: str
    password: str