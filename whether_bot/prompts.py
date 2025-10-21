from langchain.prompts import ChatPromptTemplate
from langchain_community.chat_models import Ollama
from langchain.chains import LLMChain

class PromptManager:
    def __init__(self, model_name="gemma:2b"):
        self.model = Ollama(model=model_name)
        self.extract_chain = self._create_extract_chain()
        self.nlp_chain = self._create_nlp_chain()

    def _create_extract_chain(self):
        template = """Sei un assistente per l'analisi di richieste meteo.
Estrai la Città e l'Intervallo date dalla seguente richiesta utente.
Input: {text}"""
        prompt = ChatPromptTemplate.from_template(template)
        return LLMChain(llm=self.model, prompt=prompt)

    def _create_nlp_chain(self):
        template = """Sei un assistente meteorologico
Risposta:"""
        prompt = ChatPromptTemplate.from_template(template)
        return LLMChain(llm=self.model, prompt=prompt)
