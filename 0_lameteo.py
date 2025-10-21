from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM
from datetime import datetime, timedelta
import requests
import re

# ========================
#  SETUP MODELLO LLM
# ========================
model = OllamaLLM(model="gemma:2b")

# ========================
#  PROMPT 1 – Estrazione parametri
# ========================
extract_template = """Sei un assistente per l'analisi di richieste meteo in linguaggio naturale.
Data una frase in italiano, estrai chiaramente:
- Città (se specificata)
- Intervallo date o periodo (se specificato)

Rispondi nel formato:
Città: <nome città o 'non specificata'>
Intervallo date: <date o 'non specificato'>

Input: {text}
"""

extract_prompt = ChatPromptTemplate.from_template(extract_template)
extract_chain = extract_prompt | model

# ========================
#  PROMPT 2 – Formulazione NLP dell’output
# ========================
nlp_template = """Sei un assistente meteorologico.
Ti viene fornita una descrizione tecnica del meteo e i parametri estratti da un'API.
Riformula il contenuto in linguaggio naturale, chiaro e scorrevole, come se parlassi a un utente italiano.

Dati:
Città: {città}
Periodo: {periodo}
Meteo API: {meteo}

Risposta:"""

nlp_prompt = ChatPromptTemplate.from_template(nlp_template)
nlp_chain = nlp_prompt | model

# ========================
#  FUNZIONI DI SUPPORTO
# ========================
def geocode(città):
    """Ottiene le coordinate (lat, lon) da Nominatim (OpenStreetMap)."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": città, "format": "json", "limit": 1}
    headers = {"User-Agent": "MeteoAssistant/1.0"}
    
    resp = requests.get(url, params=params, headers=headers)
    if resp.status_code == 200 and resp.json():
        data = resp.json()[0]
        lat = float(data["lat"])
        lon = float(data["lon"])
        return (lat, lon)
    else:
        return None


def get_weather(lat, lon):
    """Ottiene meteo in tempo reale da Open-Meteo."""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    resp = requests.get(url)
    if resp.status_code == 200:
        data = resp.json()
        print(data)  # Per debug

        
        
        cw = data.get("current_weather", {})
        return f"Temperatura attuale: {cw.get('temperature')}°C, vento: {cw.get('windspeed')} km/h"
    else:
        return "Errore nel recupero dati meteo."

# ========================
#  LOOP PRINCIPALE
# ========================
print("Digita 'exit' per uscire completamente.")
print("Puoi chiedere il meteo o parlare di altro.")
print("Esempio: 'Che tempo fa a Milano oggi?' oppure 'Piove a Roma domani?'\n")

modo_meteo = False
ultima_città = None
ultima_data = None

while True:
    user_input = input("You: ")
    if user_input.lower() == "exit":
        print("Uscita dal programma.")
        break

    # Comando per uscire dal contesto meteo
    if any(p in user_input.lower() for p in ["cambia argomento", "esci meteo", "nuovo argomento"]):
        modo_meteo = False
        ultima_città = None
        ultima_data = None
        print("Uscito dal contesto meteo. Torniamo alla conversazione generale.\n")
        continue

    # Se l'input riguarda il meteo, entra in modalità meteo
    if not modo_meteo and any(word in user_input.lower() for word in ["meteo", "piove", "tempo", "previsioni"]):
        modo_meteo = True
        print("Entrato nel contesto meteo.\n")

    # ==================================
    #   MODALITÀ METEO
    # ==================================
    if modo_meteo:
        msg = extract_chain.invoke({"text": user_input})
        print("...Analisi estratta (Meteo ON):")
        print(msg)

        # Estrazione semplice dei parametri dal testo
        città_match = re.search(r"Città:\s*(.+)", msg)
        data_match = re.search(r"Intervallo date:\s*(.+)", msg)

        città = città_match.group(1).strip().lower() if città_match else None
        intervallo = data_match.group(1).strip() if data_match else None

        if città and città != "non specificata":
            ultima_città = città

        oggi = datetime.now().strftime("%Y-%m-%d")
        domani = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        dopodomani = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")

        if intervallo and intervallo != "non specificato":
            # correzione naturale -> date reali
            intervallo_lower = intervallo.lower()
            if "oggi" in intervallo_lower:
                ultima_data = oggi
            elif "domani" in intervallo_lower:
                ultima_data = domani
            elif "dopodomani" in intervallo_lower:
                ultima_data = dopodomani
            else:
                ultima_data = intervallo
        else:
            ultima_data = oggi  # di default


        if not ultima_città:
            print("Nessuna città specificata. Per favore, indicane una.\n")
            continue

        coords = geocode(ultima_città)
        if not coords:
            print("Non riesco a trovare le coordinate per la città indicata.\n")
            continue

        # Ottiene meteo grezzo
        weather_info = get_weather(*coords)

        # Formulazione NLP del risultato
        nlp_response = nlp_chain.invoke({
            "città": ultima_città.capitalize(),
            "periodo": ultima_data or oggi,
            "meteo": weather_info
        })

        print(f"🗣️ {nlp_response}\n")

    # ==================================
    #   MODALITÀ CHAT GENERALE
    # ==================================
    else:
        print("Modalità chat generale (Meteo OFF).")
        print("Posso rispondere su altri argomenti.\n")
        

