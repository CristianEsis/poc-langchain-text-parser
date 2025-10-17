# llm.py
from langchain_ollama import OllamaLLM
llm = OllamaLLM(model="gemma:2b")  # Assicurarsi che il modello sia disponibile

def question_answer(domanda: str) -> str:
    """
    Funzione che invia una domanda al modello Ollama e restituisce la risposta.
    """
    response = llm.invoke(domanda)
    print(response)
    return response
    