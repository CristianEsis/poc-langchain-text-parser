import json
from typing import Dict, Any
from langchain_core.prompts import PromptTemplate
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import HumanMessage

from models import WeatherRequest

class NaturalLanguageResponseGenerator:
    """Generatore di risposte in linguaggio naturale dai dati meteo"""
    
    def __init__(self, llm: BaseLanguageModel):
        self.llm = llm
        self.prompt = self._create_prompt()
    
    def _create_prompt(self) -> PromptTemplate:
        """Crea il prompt template per la generazione della risposta"""
        template = """
Sei un assistente meteorologico che fornisce risposte chiare e utili.

Ecco i dati meteo grezzi ottenuti per la citta' '{city}':
{api_response_json}

La richiesta originale dell'utente era: "{original_request}"

Formatta questi dati in una risposta completa, scorrevole e in linguaggio naturale, rispondendo specificamente alla richiesta dell'utente. Usa un linguaggio chiaro e conciso. Se la richiesta chiedeva specifiche metriche (come temperatura, umidita'), concentrati su quelle. Se chiedeva un intervallo di date, riassumi le condizioni per quel periodo.
"""
        return PromptTemplate(
            template=template,
            input_variables=["city", "api_response_json", "original_request"]
        )
    
    def generate(
        self, 
        original_request: str, 
        parsed_request: WeatherRequest, 
        api_data: Dict[str, Any]
    ) -> str:
        """
        Genera una risposta in linguaggio naturale
        
        Args:
            original_request: La richiesta originale dell'utente
            parsed_request: L'oggetto WeatherRequest parsato
            api_data: I dati grezzi dall'API meteo
            
        Returns:
            Una stringa con la risposta formattata in linguaggio naturale
        """
        try:
            city = parsed_request.city or "Sconosciuta"
            api_response_json_str = json.dumps(api_data, indent=2, ensure_ascii=False)

            final_response_prompt = self.prompt.format(
                city=city,
                api_response_json=api_response_json_str,
                original_request=original_request
            )

            print(f"[DEBUG] Prompt inviato all'LLM (NL Response):\n{final_response_prompt}\n")

            messages = [HumanMessage(content=final_response_prompt)]
            nl_response = self.llm.invoke(messages).content

            print(f"[DEBUG] Risposta finale in linguaggio naturale:\n{nl_response}\n")
            return nl_response

        except Exception as e:
            print(f"[ERROR] Errore durante la generazione della risposta finale: {e}")
            return (
                f"Mi dispiace, sono riuscito a recuperare i dati per {parsed_request.city}, "
                f"ma non sono riuscito a formularli in linguaggio naturale a causa di un errore interno."
            )
        