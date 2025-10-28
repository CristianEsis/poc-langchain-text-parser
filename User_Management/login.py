from Models_Manager.models import User, UserAuth ,ADMIN_EMAIL, ADMIN_PASSWORD, admin_logged
from fastapi import HTTPException
from DatabaseJSON.database import read_db,update_db
from Management_Functions.Managment_functions import validation_email

def register_new_user(user: User):
    if user.tentativi != 0:
        raise HTTPException(status_code = 400, detail = "Non puoi impostare il valore dei tentativi manualmente")
    if user.check_login is not False:
        raise HTTPException(status_code = 400, detail = "Non puoi impostare il valore del login manualmente")
    if not validation_email(user.email):
        raise HTTPException(status_code = 400, detail = "Email non valida")
    if not user.password:
        raise HTTPException(status_code = 400, detail = "Password vuota")
    
    db = read_db()

    for u in db:
        if u["id"] == user.id:
            raise HTTPException(status_code = 400, detail = "L'ID utente esiste già")

    db.append(user.model_dump())
    update_db(db)
    return {"detail": "Utente registrato con successo", "utente": user.model_dump()}

def login_user(user: User):
    global admin_logged

    db = read_db()

    if user.email == ADMIN_EMAIL and user.password == ADMIN_PASSWORD:
        admin_logged = True
        return {"msg": "Login admin effettuato con successo!"}

    found_user = None
    for u in db:
        if u["id"] == user.id and u["email"] == user.email:
            found_user = u
            break

    if not found_user:
        raise HTTPException(status_code=404, detail="Email o ID non registrati")

    if found_user.get("tentativi", 0) >= 5:
        raise HTTPException(status_code=403, detail="Troppi tentativi falliti, accesso bloccato")

    if found_user["password"] == user.password:
        found_user["check_login"] = True
        found_user["tentativi"] = 0
        update_db(db)
        return {"msg": f"Login effettuato con successo! Benvenuto {found_user['name']}"}
    else:
        found_user["tentativi"] = found_user.get("tentativi", 0) + 1
        remaining = 5 - found_user["tentativi"]
        update_db(db)
        raise HTTPException(status_code=401, detail=f"Credenziali errate. Tentativi rimasti: {remaining}")

def logout_user(auth: UserAuth):
    db = read_db()
    for u in db:
        if u["email"] == auth.email and u["password"] == auth.password:
            u["check_login"] = False
            u["tentativi"] = 5
            update_db(db)
            return {"msg": f"Logout effettuato per {u['name']}"}
    raise HTTPException(status_code=404, detail="Utente non trovato")