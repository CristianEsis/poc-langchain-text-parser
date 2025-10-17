# main.py
from fastapi import FastAPI
from llm import question_answer

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "API LLM con Ollama e Langchain"}

@app.post("/ask")
def ask_domanda(payload: dict):
    domanda = payload.get("domanda", "")
    if not domanda:
        return {"error": "Nessuna domanda fornita"}
    risposta = question_answer(domanda)
    return {"domanda": domanda, "risposta": risposta}
