from typing import Optional
from pydantic import ValidationError
from langchain_core.prompts import PromptTemplate
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser

from models import WeatherRequest

class WeatherRequestParser:
    """Parser per richieste meteo in linguaggio naturale usando LLM"""

    def __init__(self, llm: BaseLanguageModel):
        self.llm = llm
        self.json_parser = JsonOutputParser(pydantic_object=WeatherRequest)
        self.prompt = self._create_prompt()

    def _create_prompt(self) -> PromptTemplate:
        """Crea il prompt template per il parsing"""
        template = """
Sei un esperto assistente per richieste meteorologiche. Il tuo compito è estrarre informazioni strutturate da una richiesta di testo in linguaggio naturale.

Analizza attentamente la richiesta fornita e identifica:
- La citta' richiesta (city). Deve essere una stringa.
- Le metriche meteorologiche specificate (metrics), ad esempio temperatura, umidita', pressione, velocita' del vento, qualita' dell'aria. Questo campo deve essere una **lista di stringhe** (es. ["temperature", "humidity"]).
- L'intervallo di date richiesto (date_range), se specificato, in formato ISO 8601 (YYYY-MM-DD). Questo campo deve essere un **oggetto con due chiavi**: "from_date" e "to" (es. {"from_date": "2023-04-01", "to": "2023-04-02"}).

Se un elemento non e' esplicitamente menzionato, imposta il campo appropriato a null o a un valore di default ragionevole.

Richiesta utente: {user_request}

Risposta (solo il JSON, senza altri testi o Markdown, seguendo rigorosamente lo schema definito):
{
  "city": "Nome della città",
  "metrics": ["metrica1", "metrica2"],
  "date_range": {
    "from_date": "YYYY-MM-DD",
    "to": "YYYY-MM-DD"
  },
  "valid": true,
  "missing_parameters": []
}
"""
        return PromptTemplate(
            template=template,
            input_variables=["user_request"]
        )

    def parse(self, user_input: str) -> Optional[WeatherRequest]:
        """
        Parse una richiesta utente in linguaggio naturale

        Args:
            user_input: La richiesta dell'utente in testo libero

        Returns:
            Un oggetto WeatherRequest o None in caso di errore
        """
        try:
            # Formatta il prompt
            print(user_input)
            
            final_prompt = self.prompt.format_prompt(user_request=user_input)
            print(f"[DEBUG] Prompt inviato all'LLM (Parsing):\n{final_prompt}\n")
            # Invoca l'LLM
            messages = [HumanMessage(content=final_prompt)]
            llm_output = self.llm.invoke(messages).content
            print(f"[DEBUG] Output LLM (Parsing):\n{llm_output}\n") # Questa stampa mostra cosa risponde l'LLM

            # Parse l'output JSON
            parsed_dict = self.json_parser.parse(llm_output)
            print(f"[DEBUG] Dizionario parsato:\n{parsed_dict}\n")

            # Valida e aggiorna i campi
            valid = True
            missing_params = []

            if not parsed_dict.get("city"):
                valid = False
                missing_params.append("city")

            # Aggiorna il dizionario
            parsed_dict["valid"] = valid
            parsed_dict["missing_parameters"] = missing_params

            # Crea l'oggetto WeatherRequest dal dizionario
            weather_request = WeatherRequest(**parsed_dict)
            print(f"[DEBUG] Oggetto WeatherRequest Pydantic:\n{weather_request}\n")

            return weather_request

        except ValidationError as ve:
            print(f"[ERROR] Errore di validazione Pydantic: {ve}")
            return None
        except Exception as e:
            print(f"[ERROR] Errore durante il parsing: {e}")
            import traceback
            traceback.print_exc()
            return None
