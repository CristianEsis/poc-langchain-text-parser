from fastapi import FastAPI, HTTPException
from Management_Functions.Managment_functions import error_manager,validation_email
from Models_Manager.models import User,City,UserAuth
from CitiesManager.Cities import save_city,load_cities
from DatabaseJSON.database import read_db,update_db
#from langchain_core.chat_history import InMemoryChatMessageHistory da rivedere
from llm import question_answer

ADMIN_EMAIL = "admin@cybercats.it"
ADMIN_PASSWORD = "admin123"
admin_logged = False 

app = FastAPI(
    title="My FastAPI App",
    description="Un progetto FastAPI minimale, pronto per crescere.",
    version="0.1.0"
)

@app.get("/")
def read_root():
    return {"message": "Benvenuto nella mia API 🚀, questa è la root. Per la documentazione relativa al programma, visita http://127.0.0.1:8000/docs"}

@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/user/register", summary = "Registra un nuovo utente", description = "Aggiungi un id, il tuo nome,email e password per registrare il tuo account", tags = ["Utenti"])
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

@app.post("/user/login",summary="Si accede all'account creato")
def login_user(user: User):
    global admin_logged

    try:
        db = read_db()

        if user.email == ADMIN_EMAIL and user.password == ADMIN_PASSWORD:
            admin_logged = True
            return {"msg": "Login admin effettuato con successo!"}

        found_user = None
        for u in db:
            if u["id"] == user.id or u["email"] == user.email:
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

    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        return error_manager(e)

@app.get("/user", summary = "Elenca le tue informazioni personali", tags = ["Utenti"])
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
                    "cities": u.get("cities", [])
                }
            else:
                raise HTTPException(status_code=401, detail="Utente non loggato. Effettua il login prima di accedere ai dati.")

    raise HTTPException(status_code=404, detail="Utente non trovato")

@app.put("/users/{user_id}", summary = "Aggiorna i tuoi dati", description = "Inserisci l'id e i tuoi dati(email e password per confermare che sia tu) e poi inserire le informazioni da aggiornare", tags = ["Utenti"])
def update_user(user_id: int, auth: UserAuth, updated_user: User):
    db = read_db()
    for user in db:
        if user["id"] == user_id:
            if user["email"] != auth.email or user["password"] != auth.password:
                raise HTTPException(status_code=401, detail="Credenziali non valide per aggiornamento")
            updated_data = updated_user.model_dump(exclude_unset=True)

            if "email" in updated_data:
                if not validation_email(updated_data["email"]):
                    raise HTTPException(status_code=400, detail="Nuova email non valida")

            if "check_login" in updated_data or "tentativi" in updated_data:
                raise HTTPException(status_code=400, detail="Non puoi modificare manualmente questi campi")

            user.update(updated_data)
            update_db(db)
            return {"msg": f"Utente con id {user_id} aggiornato con successo!", "user": user}

    raise HTTPException(status_code = 404, detail=f"Utente con id {user_id} non trovato.")

@app.delete("/users/{user_id}", summary = "Cancella un tuo account", description = "Inserisci l'id e i tuoi dati(email e password per confermare che sia tu) per avviare la fase di cancellazione dell'acount", tags = ["Utenti"])
def delete_user(user_id: int, auth: UserAuth):
    db = read_db()
    for user in db:
        if user["id"] == user_id:
            if user["email"] != auth.email or user["password"] != auth.password:
                raise HTTPException(status_code=401, detail = "Credenziali non valide per cancellazione")
            db.remove(user)
            update_db(db)
            return {"detail": f"Utente con id {user_id} cancellato con successo"}
    raise HTTPException(status_code = 404, detail = "Utente non trovato")


@app.post("/city/add", summary = "Aggiungi le città di cui vuoi sapere le informazioni(max 5)", description="Questa funzionalità permette di aggiungere massimo 5 città, nel caso si aggiungessero piu città il programma rimuoverà l'ultima città aggiunta\n{'email': 'la tua email' 'password': 'la tua password' 'city_name': 'la città che vuoi aggiungere' RICORDATI DI ESSERE LOGGATO}", tags=["Città"])
def add_city(user_data: dict):
    db = read_db()
    city_name = user_data.get("city_name")
    user_id = user_data.get("id")
    email = user_data.get("email")
    password = user_data.get("password")

    for u in db:
        if u.get("check_login", False) and u["id"] == user_id and u["email"] == email and u["password"] == password:
            city = City(city_name=city_name)
            result = save_city(user_id, city)
            cities = load_cities(user_id)
            return {
                "message": result["msg"],
                "cities": cities
            }
    return {"msg": "Non hai un account, registrati o loggati per effettuare questa operazione"}

@app.get("/city/list",summary = "Ti elencherà le 5 città cercate", description="Questa funzionalità permette di elencarti le prime 5 città cercate", tags=["Città"])
def list_of_city(auth: UserAuth):
    db = read_db()
    for u in db:
        if u["email"] == auth.email and u["password"] == auth.password:
            if u.get("check_login", False):
                return {
                    "message": f"Città salvate per l'utente {u['name']}",
                    "cities": u.get("cities", [])
                }
            else:
                raise HTTPException(status_code=401, detail="Utente non loggato. Effettua il login prima di accedere ai dati.")

    raise HTTPException(status_code=404, detail="Utente non trovato")

@app.post("/ask")
def ask_domanda(payload: dict):
    domanda = payload.get("domanda", "")
    if not domanda:
        return {"error": "Nessuna domanda fornita"}
    risposta = question_answer(domanda)
    return {"domanda": domanda, "risposta": risposta}
