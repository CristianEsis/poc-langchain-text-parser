import json
from json.decoder import JSONDecodeError
def read_db():
    try:
        with open('lista_utenti_LLM_meteo_cybercats.json', 'r', encoding='utf-8') as f:
            db = json.load(f)
            if not isinstance(db, list):
                db = []
    except (FileNotFoundError, JSONDecodeError):
        with open('lista_utenti_LLM_meteo_cybercats.json', 'w', encoding='utf-8') as f:
            json.dump([], f)
        db = []
    return db

def update_db(db):
    with open('lista_utenti_LLM_meteo_cybercats.json', 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=4, ensure_ascii=False)
