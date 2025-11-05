from Models_Manager.models import City, UserAuth
from fastapi import HTTPException
from Management_Functions.Managment_functions import error_manager
from DatabaseJSON.database import read_db,update_db

def save_city(user_id: int, city: City):
    try:
        db = read_db()
        found = False

        for u in db:
            if u["id"] == user_id:
                found = True

                if "city" not in u or not isinstance(u["city"], list):
                    u["city"] = []

                existing_city = [c.lower() for c in u["city"]]
                if city.city_name.lower() in existing_city:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"La città '{city.city_name}' è già salvata per questo utente."
                    )

                #if len(u["city"]) >= 5:
                #    u["city"].pop(0)

                #u["city"].append(city.city_name)
                break

        if not found:
            raise HTTPException(status_code=404, detail="Utente non trovato")

        update_db(db)
        return {"msg": f"Città '{city.city_name}' salvata correttamente per l'utente con id {user_id}"}

    except HTTPException:
        raise
    except Exception as e:
        return error_manager(str(e))

def load_city(user_id: int) -> list[str]:
    try:
        db = read_db()
        for u in db:
            if u["id"] == user_id:
                return u.get("city", [])
        raise HTTPException(status_code=404, detail="Utente non trovato")
    except HTTPException:
        raise
    except Exception as e:
        return error_manager(str(e))

def add_city(user: dict, city_name: str, weather_data: dict = None):
    """Aggiunge o aggiorna una città nel profilo utente autenticato."""
    db = read_db()

    # 🔹 Normalizza il nome della città
    city_name = city_name.strip()
    for prefix in ["a ", "ad ", "in ", "da ", "di ", "la ", "il "]:
        if city_name.lower().startswith(prefix):
            city_name = city_name[len(prefix):]
            break
    city_name = city_name.capitalize()

    for u in db:
        if u["email"] == user["email"]:
            # Se il campo "cities" non esiste o è nel formato errato, inizializzalo
            if "cities" not in u or not isinstance(u["cities"], dict):
                u["cities"] = {}

            # 🔹 Se la città è già presente, aggiorna i dati
            if city_name.lower() in u["cities"]:
                print(f"Aggiornamento dati per la città '{city_name}'...")
            else:
                print(f"Aggiunta nuova città '{city_name}'...")

            # Sovrascrivi o aggiungi la città con i nuovi dati meteo
            u["cities"][city_name.lower()] = weather_data or {}

            # Aggiorna il database
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
