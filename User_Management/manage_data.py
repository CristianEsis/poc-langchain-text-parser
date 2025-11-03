from Models_Manager.models import User, UserAuth, ADMIN_EMAIL, ADMIN_PASSWORD, admin_logged
from fastapi import HTTPException
from DatabaseJSON.database import read_db,update_db
from Management_Functions.Managment_functions import  validation_email

def read_user(auth: UserAuth):
    db = read_db()
    global admin_logged

    if auth.email == ADMIN_EMAIL and auth.password == ADMIN_PASSWORD:
        admin_logged = True
        return {"msg": "Accesso admin", "utenti": db}

    for u in db:
        if u["email"] == auth.email and u["password"] == auth.password:
            if u.get("check_login", False):
                return {
                    "id": u["id"],
                    "name": u["name"],
                    "email": u["email"],
                    "city": u.get("city", [])
                }
            else:
                raise HTTPException(status_code=401, detail="Utente non loggato. Effettua il login prima di accedere ai dati.")

    raise HTTPException(status_code=404, detail="Utente non trovato")

def update_user(user_id: int, auth: UserAuth, updated_user: User):
    db = read_db()

    found_user = None
    for user in db:
        if user["id"] == user_id and user["email"] == updated_user.email:
            found_user = user
            break

    if not found_user:
        raise HTTPException(status_code=404, detail=f"Utente con id {user_id} non trovato oppure email errata.")

    if found_user["email"] != auth.email or found_user["password"] != auth.password:
        raise HTTPException(status_code=401, detail="Credenziali non valide per aggiornamento")

    updated_data = updated_user.model_dump(exclude_unset=True)

    if "email" in updated_data and not validation_email(updated_data["email"]):
        raise HTTPException(status_code=400, detail="Nuova email non valida")

    if "id" in updated_data and updated_data["id"] != user_id:
        for user in db:
            if user["id"] == updated_data["id"]:
                raise HTTPException(status_code=400, detail="ID già esistente")

    if "check_login" in updated_data or "tentativi" in updated_data:
        raise HTTPException(status_code=400, detail="Non puoi modificare manualmente questi campi(tentativi o check_login)")

    found_user.update(updated_data)
    update_db(db)
    return {"msg": f"Utente con id {user_id}({updated_user['name']}) aggiornato con successo!", "user": found_user}

def delete_user(user_id: int, auth: UserAuth):
    db = read_db()
    for user in db:
        if user["id"] == user_id:
            if user["email"] != auth.email or user["password"] != auth.password:
                raise HTTPException(status_code=401, detail = "Credenziali non valide per cancellazione")
            db.remove(user)
            update_db(db)
            return {"detail": f"Utente con id {user_id}({user['name']}) cancellato con successo"}
    raise HTTPException(status_code = 404, detail = "Utente non trovato")
