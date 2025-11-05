from Models_Manager.models import City, UserAuth
from fastapi import HTTPException
from Management_Functions.Managment_functions import error_manager
from DatabaseJSON.database import read_db,update_db

def add_city(user: dict, city_name: str, weather_data: dict = None):
    """Aggiunge o aggiorna una città nel profilo utente autenticato.
       Mantiene massimo 5 città recenti (rimuove la più vecchia se necessario)."""
    db = read_db()

    city_name = city_name.strip()
    for prefix in ["a ", "ad ", "in ", "da ", "di ", "la ", "il "]:
        if city_name.lower().startswith(prefix):
            city_name = city_name[len(prefix):]
            break
    city_name = city_name.capitalize()

    for u in db:
        if u["email"] == user["email"]:
            if "cities" not in u or not isinstance(u["cities"], dict):
                u["cities"] = {}

            if city_name.lower() in u["cities"]:
                u["cities"][city_name.lower()] = weather_data or {}
            else:
                if len(u["cities"]) >= 5:
                    oldest_city = next(iter(u["cities"])) 
                    u["cities"].pop(oldest_city)

                u["cities"][city_name.lower()] = weather_data or {}

            update_db(db)

            return {
                "message": f"Città '{city_name}' aggiunta o aggiornata con successo.",
                "city": u["cities"][city_name.lower()]
            }

    return {"msg": "Utente non trovato nel database"}
def list_of_city(auth: UserAuth):
    db = read_db()
    for u in db:
        if u["email"] == auth.email and u["password"] == auth.password:
            if u.get("check_login", False):
                return {
                    "message": f"Città salvate per l'utente {u['name']}",
                    "city": u["cities"]
                }
            else:
                raise HTTPException(status_code=401, detail="Utente non loggato. Effettua il login prima di accedere ai dati.")

    raise HTTPException(status_code=404, detail="Utente non trovato")
