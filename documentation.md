# 🌦️ Weather Dispatching API – Technical Documentation

## 📌 Overview

This project implements a **FastAPI-based weather service** that dispatches weather requests by continent, using real-time data from **OpenWeatherMap** (and optionally **Open-Meteo**). It features:

- Natural language parsing of user requests (e.g., "Che tempo fa a Roma?")
- Continent-based API parameter customization (units, language)
- City-to-continent mapping using a curated dataset (`CityCountryContinent.xlsx`)
- ML-based fallback with a trained classifier for robust city/continent detection
- User authentication and city favorites management (stored per user)
- Support for current weather, 5-day forecasts, and air quality

The system is modular, extensible, and production-ready with health checks, logging, and error handling.

---

## 🏗️ Architecture

### Main Components

| Component | Responsibility |
|----------|----------------|
| `WeatherService` | Core logic: city extraction, continent detection, OpenWeatherMap API calls |
| `ContinentClassifier` | ML model (Random Forest + TF-IDF) to predict continent from text |
| `WeatherAPI` | Unified client for OpenWeatherMap & Open-Meteo APIs |
| `NaturalLanguageResponseGenerator` | Uses an LLM to generate human-readable weather summaries |
| `User/Auth Management` | JWT-less session-based auth using email/password with login state |
| `City Favorites` | Users can store up to 5 cities with weather data |

### Data Flow (for a `/weather` request)

1. User sends natural language request (e.g., `"Meteo a Tokyo?"`)
2. FastAPI endpoint receives it via `WeatherRequest`
3. `WeatherService.extract_city()` parses the city name
4. Continent is resolved via:
   - Excel dataset lookup → fallback to hardcoded map → fallback to ML classifier
5. OpenWeatherMap is called with continent-specific params (`units`, `lang`)
6. Response is enriched and returned in structured + natural language format

---

## 🧩 Core Modules

### 1. `WeatherService`

**Responsibilities**:
- Load `CityCountryContinent.xlsx` into a pandas DataFrame
- Parse city names from Italian (and multilingual) natural language
- Determine continent for any city
- Fetch real-time weather from OpenWeatherMap

**Key Methods**:
- `extract_city(request_text: str) → str`
- `get_continent_for_city(city_name: str) → str`
- `get_weather_data(city: str, continent: str) → Dict`
- `process_request(user_request: str) → Dict`

**Continent Parameters** (`continent_params`):

| Continent | Units | Language |
|----------|--------|----------|
| Asia | metric | zh |
| Africa | metric | fr |
| North America | imperial | en |
| South America | metric | es |
| Europe | metric | de |
| Oceania | metric | en |
| Seven seas | metric | en |

> ⚠️ Note: Language affects weather description translation (if supported by OpenWeatherMap).

---

### 2. `ContinentClassifier` (ML Module)

**Purpose**: Predict continent from raw user text when dataset lookup fails.

- **Model**: `RandomForestClassifier`
- **Vectorizer**: `TfidfVectorizer` (n-grams 1–2, max 5000 features)
- **Training Data**: Synthetic queries generated from city list (e.g., `"Che tempo fa a {city}?"`)
- **Saved Artifacts**: `continent_classifier.pkl`, `tfidf_vectorizer.pkl`

**Usage**:
```python
classifier = ContinentClassifier()
continent, city = classifier.predict_continent("Previsioni per Sydney?")
```

---

### 3. `WeatherAPI` (Multi-Source Client)

Fetches data from:
- **OpenWeatherMap**: current weather, 5-day forecast, air pollution, geocoding
- **Open-Meteo**: current weather (as backup)

**Key Methods**:
- `get_coordinates(city_name)`
- `get_current_weather_owm(lat, lon)`
- `get_forecast_5d_own(lat, lon)`
- `get_air_quality_owm(lat, lon)`
- `get_all_data_for_city(city_name)` → returns merged data

---

### 4. `NaturalLanguageResponseGenerator`

Uses an **LLM** (LangChain-compatible) to convert structured weather data into fluent Italian responses.

**Prompt Template Includes**:
- City name
- Original user request
- Full API response (with aggregated stats if available)
- GMT+1 timezone context

> 📝 *Requires an LLM instance (e.g., ChatOpenAI) to be injected at runtime.*

---

## 🌐 API Endpoints (FastAPI)

### 🔹 `POST /weather`
**Request**:
```json
{ "richiesta": "Che tempo fa a Roma?" }
```

**Response** (`WeatherResponse`):
```json
{
  "richiesta_originale": "Che tempo fa a Roma?",
  "citta": "Roma",
  "continente": "Europe",
  "dati_meteo": { ... },
  "servizio_utilizzato": "OpenWeatherMap",
  "parametri_utilizzati": { "lang": "de", "units": "metric" },
  "tempo_elaborazione_ms": 342.1,
  "timestamp": "2025-11-05T12:34:56.789"
}
```

---

### 🔹 `GET /health`
Returns service status:
```json
{
  "status": "ok",
  "service": "Weather Dispatching API",
  "dataset_loaded": true,
  "api_key_configured": true
}
```

---

### 🔹 `GET /continents`
Lists supported continents and (intended) API endpoints.

> ⚠️ **Bug Alert**: Code references `self.continent_apis` but this attribute is **not defined** in `WeatherService`. Will raise `AttributeError`.

---

### 🔹 `GET /city/{city_name}`
Returns city metadata from dataset:
```json
{
  "city": "Roma",
  "country": "Italy",
  "continent": "Europe",
  "latitude": 41.9028,
  "longitude": 12.4964
}
```

---

## 👤 User & City Management (Auth Layer)

### Models
- `User`: id, name, email, password, `check_login`, `tentativi`
- `UserAuth`: email + password for auth operations

### Endpoints (not shown in main file but implemented in modules):

| Operation | Function |
|--------|--------|
| Register | `register_new_user()` |
| Login | `login_user()` (max 5 failed attempts → lock) |
| Logout | `perform_logout()` |
| Read Profile | `read_user()` (requires login) |
| Update Profile | `update_user()` |
| Delete Account | `delete_user()` |
| Add City to Favorites | `add_city()` (max 5 cities) |
| List Saved Cities | `list_of_city()` |

> 🔐 **Security**: Plain-text passwords (not hashed) – **not suitable for production** without modification.

---

## 📂 Project Structure (Implied)

```
project/
├── CityCountryContinent.xlsx            # City → Country → Continent mapping
├── main.py                              # FastAPI app + WeatherService
├── continent_classifier.py              # ML training & inference
├── weather_api_client.py                # Multi-API client
├── nl_response_generator.py             # LLM-based response formatter
├── Models_Manager/
│   └── models.py                        # Pydantic models (User, City, etc.)
├── Management_Functions/
│   └── management_functions.py          # Auth logic, validation
├── DatabaseJSON/
│   └── database.py                      # JSON file I/O (lista_utenti_LLM_meteo_cybercats.json)
└── data/                                # (Generated) training data
```

---

## ⚙️ Setup & Configuration

### Environment Variables
```bash
export OPENWEATHER_API_KEY="your_api_key_here"
```

### Dependencies (Key Packages)
```txt
fastapi
uvicorn
pandas
numpy
scikit-learn
joblib
requests
pydantic
openpyxl
langchain-core  # if using NL generator
```

### First-Time Setup
1. Place `CityCountryContinent.xlsx` in root
2. Run ML training (optional but recommended):
   ```bash
   python train_classifier.py
   ```
3. Start server:
   ```bash
   uvicorn main:app --reload
   ```

---

## 🛑 Known Issues & Limitations

| Issue | Impact | Suggestion |
|------|--------|-----------|
| `self.continent_apis` undefined | `/continents` endpoint crashes | Define `self.continent_apis = {"Europe": "OpenWeatherMap", ...}` |
| Passwords stored in plaintext | Security risk | Add password hashing (e.g., `passlib`) |
| City extraction regex is Italian-centric | May fail on other languages | Enhance NLP or use spaCy |
| Fallback returns `common_cities` list (not string) | Type error in `extract_city` | Return first city or raise exception |
| GMT+1 hardcoded | Incorrect for non-EU users | Use timezone from geocoding |

---

## ✅ Example Usage

**Request**:
```bash
curl -X POST http://localhost:8000/weather \
  -H "Content-Type: application/json" \
  -d '{"richiesta": "Che tempo fa a Tokyo?"}'
```

**Sample Response Snippet**:
```json
{
  "citta": "Tokyo",
  "continente": "Asia",
  "dati_meteo": {
    "temperature": 18.2,
    "feels_like": 17.8,
    "humidity": 65,
    "conditions": "parzialmente nuvoloso",
    "wind_speed": 3.1,
    "country": "JP",
    "sunrise": "06:12",
    "sunset": "17:03"
  }
}
```

---

## 📜 License

*Assumed GPL3 unless specified otherwise. Not included in source.*

---

> ✨ **Maintained by**: CyberCats Team  
> 📅 **Last Updated**: November 2025

--- 