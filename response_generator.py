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

Ecco i dati meteo per la città '{city}':
{api_response_json}

La richiesta originale dell'utente era: "{original_request}"

ISTRUZIONI IMPORTANTI:
1. Tutti gli orari sono in formato GMT+1 (fuso orario italiano)
2. Se sono disponibili le statistiche aggregate (period_statistics), UTILIZZALE come dati principali:
   - Menziona la temperatura MEDIA, minima e massima per il periodo richiesto
   - Indica chiaramente che si tratta di dati medi/previsti per il periodo specificato
3. Se l'utente ha chiesto un periodo specifico (mattino, pomeriggio, sera, notte), menzionalo nella risposta
4. Se l'utente ha chiesto una data specifica o un intervallo, fai riferimento a quel periodo
5. Fornisci una risposta completa ma concisa, concentrandoti sulle metriche richieste
6. NON elencare tutte le previsioni orarie, usa le statistiche aggregate
7. Se disponibili, menziona anche umidità e pressione medie

Esempio di risposta corretta:
"A Milano questa mattina (GMT+1) la temperatura media sarà di 15.2°C, con minime di 13.5°C e massime di 17.1°C. L'umidità media si attesterà intorno al 65% e la pressione a 1015 hPa."

Formatta ora la tua risposta in linguaggio naturale, chiaro e professionale:
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
            api_data: I dati grezzi dall'API meteo (con statistiche aggregate)
            
        Returns:
            Una stringa con la risposta formattata in linguaggio naturale
        """
        try:
            city = parsed_request.city or "Sconosciuta"
            
            # Prepara i dati per l'LLM, evidenziando le statistiche se disponibili
            data_for_llm = api_data.copy()
            
            # Se ci sono statistiche, mettile in evidenza
            if 'period_statistics' in data_for_llm:
                stats = data_for_llm['period_statistics']
                print(f"[DEBUG] Usando statistiche aggregate: {stats}")
            
            api_response_json_str = json.dumps(data_for_llm, indent=2, ensure_ascii=False)

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
