from langchain_ollama import ChatOllama
from weather_service import WeatherService

def main():
    """Funzione principale dell'applicazione"""
    
    # Configurazione
    API_KEY = '2300cb7362ef7560c3e75c5b6aa48b2c'  # Inserisci la tua chiave API qui
    
    # Inizializza il modello LLM
    print("Inizializzazione del modello LLM...")
    llm = ChatOllama(model="gemma:2b", temperature=0.1)
    
    # Inizializza il servizio meteo
    print("Inizializzazione del servizio meteo...\n")
    weather_service = WeatherService(API_KEY, llm)
    
    # Loop principale
    print("=== ASSISTENTE METEO ===")
    print("Scrivi 'esci' per terminare\n")
    
    while True:
        # Richiedi input all'utente
        user_input = input("Inserisci la tua richiesta meteo: ").strip()
        
        # Controlla se l'utente vuole uscire
        if user_input.lower() in ['esci', 'exit', 'quit', 'q']:
            print("Arrivederci!")
            break
        
        if not user_input:
            print("Per favore, inserisci una richiesta valida.\n")
            continue
        
        # Processa la richiesta
        try:
            response = weather_service.process_request(user_input)
            print("\n" + "="*60)
            print("RISPOSTA:")
            print("="*60)
            print(response)
            print("="*60 + "\n")
        except Exception as e:
            print(f"\n[ERRORE] Si è verificato un errore: {e}\n")

if __name__ == "__main__":
    main()
