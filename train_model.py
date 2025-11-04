"""
Script per l'addestramento iniziale del modello di classificazione continentale.
Eseguire questo script una volta prima di avviare le API.
"""

from continent_classifier import ContinentClassifier
import argparse
import os

def main():
    parser = argparse.ArgumentParser(description='Addestra il modello di classificazione continentale')
    parser.add_argument('--dataset', type=str, default='CityCountryContinent.xlsx', 
                        help='Percorso del file dataset Excel')
    parser.add_argument('--force', action='store_true', help='Forza il riaddestramento anche se il modello esiste')
    args = parser.parse_args()
    
    print("🚀 Avvio addestramento modello di classificazione continentale")
    print("=" * 60)
    
    # Imposta il percorso del dataset
    if os.path.exists(args.dataset):
        os.makedirs('data', exist_ok=True)
        import shutil
        shutil.copy(args.dataset, 'data/city_dataset.xlsx')
        print(f"✅ Dataset copiato in: data/city_dataset.xlsx")
    else:
        print(f"❌ Errore: File dataset non trovato: {args.dataset}")
        print("   Assicurati che il file Excel sia nella directory corrente.")
        return
    
    # Crea il classificatore ed addestra il modello
    classifier = ContinentClassifier()
    
    # Forza il riaddestramento se richiesto
    if args.force and os.path.exists(classifier.model_path):
        print(f"🗑️  Eliminazione modello esistente: {classifier.model_path}")
        os.remove(classifier.model_path)
    
    # Addestra il modello
    print("\n🔧 Addestramento del modello in corso...")
    results = classifier.train_model()
    
    # Mostra risultati finali
    print("\n📊 RISULTATI FINALI:")
    print("-" * 50)
    print(f"Accuratezza del modello: {results['accuracy']:.4f}")
    
    # Test rapido
    print("\n🔍 TEST RAPIDO CON ESEMPI:")
    test_requests = [
        "Che tempo fa a Tokyo?",
        "Meteo Roma oggi",
        "Previsioni per New York domani",
        "Come sarà il clima al Cairo?",
        "Temperatura attuale a Sydney"
    ]
    
    for req in test_requests:
        continent, city = classifier.predict_continent(req)
        weather_data = classifier.simulate_weather_service(continent, city)
        print(f"\n  Richiesta: '{req}'")
        print(f"  Città: {city}")
        print(f"  Continente: {continent}")
        print(f"  Risposta: {weather_data['human_description']}")
        print("-" * 30)

if __name__ == "__main__":
    main()
