from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, messages_from_dict
import json
import os
from json.decoder import JSONDecodeError

class LangChainJsonHistory(BaseChatMessageHistory):
    """Adattatore per salvare la cronologia nel file JSON dell'utente."""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.file_path = f"cronologia_utente_{self.user_id}.json"

    def _load_history(self) -> list:
        """Carica l'intera cronologia dal file JSON."""
        if not os.path.exists(self.file_path):
            return []
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except JSONDecodeError:
            # File vuoto o corrotto, restituisce lista vuota
            return []

    def _save_history(self, history_data: list):
        """Salva la cronologia completa nel file JSON."""
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(history_data, f, indent=4, ensure_ascii=False)

    @property
    def messages(self) -> list[BaseMessage]:
        """Metodo richiesto: converte la cronologia del tuo formato nel formato LangChain."""
        loaded_data = self._load_history()
        
        # Converte il tuo formato [{"domanda": domanda, "risposta": risposta}] 
        # nel formato LangChain [HumanMessage, AIMessage, ...]
        messages = []
        for entry in loaded_data:
            messages.append(HumanMessage(content=entry["domanda"]))
            messages.append(AIMessage(content=entry["risposta"]))
        
        return messages

    def add_message(self, message: BaseMessage) -> None:
        """Metodo richiesto: aggiunge un messaggio e salva."""
        loaded_data = self._load_history()
        
        # LangChain chiama questo metodo per ogni messaggio (sia Human che AI)
        
        # Se l'ultimo messaggio salvato era una "domanda", questo è una "risposta"
        if len(loaded_data) > 0 and "domanda" in loaded_data[-1] and "risposta" not in loaded_data[-1]:
            # Aggiunge la risposta all'ultima entry
            loaded_data[-1]["risposta"] = message.content
        else:
            # Nuova domanda (la risposta arriverà nella prossima chiamata)
            loaded_data.append({"domanda": message.content, "risposta": ""})
            
        self._save_history(loaded_data)
        
    def clear(self) -> None:
        """Cancella la cronologia (scrive [] nel file)."""
        self._save_history([])