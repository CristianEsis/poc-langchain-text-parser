from Models_Manager.models import City
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

                if "cities" not in u or not isinstance(u["cities"], list):
                    u["cities"] = []

                existing_cities = [c.lower() for c in u["cities"]]
                if city.city_name.lower() in existing_cities:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"La città '{city.city_name}' è già salvata per questo utente."
                    )

                if len(u["cities"]) >= 5:
                    u["cities"].pop(0)

                u["cities"].append(city.city_name)
                break

        if not found:
            raise HTTPException(status_code=404, detail="Utente non trovato")

        update_db(db)
        return {"msg": f"Città '{city.city_name}' salvata correttamente per l'utente con id {user_id}"}

    except HTTPException:
        raise
    except Exception as e:
        return error_manager(str(e))

def load_cities(user_id: int) -> list[str]:
    try:
        db = read_db()
        for u in db:
            if u["id"] == user_id:
                return u.get("cities", [])
        raise HTTPException(status_code=404, detail="Utente non trovato")
    except HTTPException:
        raise
    except Exception as e:
        return error_manager(str(e))
