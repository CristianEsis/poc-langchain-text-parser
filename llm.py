# llm.py
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

model_llm = OllamaLLM(model="gemma:2b")  # Assicurarsi che il modello sia disponibile

template = """Question: {question}
think step by step, and provide with an answer"""

prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model_llm


def question_answer(domanda: str) -> str:
    """
    Funzione che invia una domanda al modello Ollama e restituisce la risposta.
    """
    response = chain.invoke(domanda)
    return response
    