from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import json
from json.decoder import JSONDecodeError
import re
from llm import question_answer

class User(BaseModel):
    id: int | None = None
    name: str | None = None
    email: str | None = None
    password: str | None = None
    check_login: bool = False
    tentativi: int = 0
    cronologia: list = []
    

def crea_cronologia(utente: User):
    with open("cronologia_utente_{self.id}.json", "w", encoding="utf-8") as f:
        json.dump([], f, indent=4, ensure_ascii=False)
        utente.cronologia = f

def aggiungi_cronologia(utente: User, domanda: str, risposta: str):
    if utente.cronologia == []:
        crea_cronologia(utente)

    try:
        with open(f"cronologia_utente_{utente.id}.json", "r", encoding="utf-8") as f:
            cronologia = json.load(f)
            if not isinstance(cronologia, list):
                cronologia = []
    except (FileNotFoundError, JSONDecodeError):
        crea_cronologia(utente)
        cronologia = []
    
    cronologia.append({"domanda": domanda, "risposta": risposta})

    with open(f"cronologia_utente_{utente.id}.json", "w", encoding="utf-8") as f:
        json.dump(cronologia, f, indent=4, ensure_ascii=False)
        utente.cronologia = cronologia


        
        
        

        

