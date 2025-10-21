import requests
import json
from datetime import datetime


class WeatherAPI:
    """
    Modulo per effettuare chiamate API a servizi meteo come OpenWeatherMap e Open-Meteo.
    Fornisce metodi per ottenere coordinate, dati meteo attuali e qualità dell'aria.
    """
    def __init__(self, openweather_api_key):
        """
        Inizializza il client API con la chiave API di OpenWeatherMap.

        :param openweather_api_key: Chiave API per OpenWeatherMap.
        """
        self.OPENWEATHER_API_KEY = openweather_api_key
        self.OWM_CURRENT_URL = "http://api.openweathermap.org/data/2.5/weather"
        self.OWM_AIR_POLLUTION_URL = "http://api.openweathermap.org/data/2.5/air_pollution"
        self.OWM_GEO_URL = "http://api.openweathermap.org/geo/1.0/direct"
        self.OPEN_METEO_CURRENT_URL = "https://api.open-meteo.com/v1/forecast"

    def get_coordinates(self, city_name):
        """
        Ottiene le coordinate (latitudine, longitudine) per un nome di città usando OpenWeatherMap.

        :param city_name: Nome della città.
        :return: Tupla (lat, lon) o (None, None) se non trovata.
        """
        params = {
            'q': city_name,
            'limit': 1,
            'appid': self.OPENWEATHER_API_KEY
        }
        response = requests.get(self.OWM_GEO_URL, params=params)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                return data[0]['lat'], data[0]['lon']
        return None, None

    def get_current_weather_owm(self, lat, lon):
        """
        Ottiene i dati meteo attuali da OpenWeatherMap.

        :param lat: Latitudine.
        :param lon: Longitudine.
        :return: Dati meteo JSON o None se errore.
        """
        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.OPENWEATHER_API_KEY,
            'units': 'metric'
        }
        response = requests.get(self.OWM_CURRENT_URL, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Errore nella richiesta meteo OpenWeatherMap: {response.status_code}")
            return None

    def get_air_quality_owm(self, lat, lon):
        """
        Ottiene i dati sulla qualità dell'aria da OpenWeatherMap.

        :param lat: Latitudine.
        :param lon: Longitudine.
        :return: Dati qualità aria JSON o None se errore.
        """
        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.OPENWEATHER_API_KEY
        }
        response = requests.get(self.OWM_AIR_POLLUTION_URL, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Errore nella richiesta qualità aria OpenWeatherMap: {response.status_code}")
            return None

    def get_current_weather_openmeteo(self, lat, lon):
        """
        Ottiene i dati meteo attuali da Open-Meteo.

        :param lat: Latitudine.
        :param lon: Longitudine.
        :return: Dati meteo JSON o None se errore.
        """
        params = {
            'latitude': lat,
            'longitude': lon,
            'current_weather': True,
            'timezone': 'auto'
        }
        response = requests.get(self.OPEN_METEO_CURRENT_URL, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Errore nella richiesta Open-Meteo: {response.status_code}")
            return None

    def get_all_data_for_city(self, city_name):
        """
        Ottiene tutti i dati per una città da entrambe le API.

        :param city_name: Nome della città.
        :return: Dizionario con tutti i dati o None se fallisce.
        """
        lat, lon = self.get_coordinates(city_name)
        if not lat or not lon:
            print(f"Coordinate non trovate per {city_name}")
            return None

        # Dati OpenWeatherMap
        weather_owm = self.get_current_weather_owm(lat, lon)
        air_owm = self.get_air_quality_owm(lat, lon)
        parsed_owm = self._parse_owm_data(weather_owm, air_owm)

        # Dati Open-Meteo
        weather_om = self.get_current_weather_openmeteo(lat, lon)
        parsed_om = self._parse_openmeteo_data(weather_om)

        return {
            'city': city_name,
            'openweathermap': parsed_owm,
            'openmeteo': parsed_om,
            'timestamp': datetime.now().isoformat()
        }

    def _parse_owm_data(self, weather_data, air_data):
        """ Metodo privato per estrarre e formattare i dati da OpenWeatherMap. """
        if not weather_data:
            return None
        main = weather_data['main']
        wind = weather_data['wind']
        owm_parsed = {
            'temperature': main['temp'],
            'humidity': main['humidity'],
            'pressure': main['pressure'],
            'wind_speed': wind.get('speed', 0),
            'wind_direction': wind.get('deg', 0),
            'air_quality': None
        }
        if air_data:
            components = air_data['list'][0]['components']
            aqi = air_data['list'][0]['main']['aqi']
            owm_parsed['air_quality'] = {
                'aqi': aqi,
                'co': components['co'],
                'no2': components['no2'],
                'o3': components['o3'],
                'pm2_5': components['pm2_5'],
                'pm10': components['pm10']
            }
        return owm_parsed

    def _parse_openmeteo_data(self, meteo_data):
        """ Metodo privato per estrarre e formattare i dati da Open-Meteo. """
        if not meteo_data:
            return None
        current = meteo_data['current_weather']
        return {
            'temperature': current['temperature'],
            'windspeed': current['windspeed'],
            'winddirection': current['winddirection'],
            'time': current['time']
        }


def save_to_json(data, filename):
    """
    Salva i dati in un file JSON.

    :param data: Dati da salvare.
    :param filename: Nome del file di output.
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Dati salvati in: {filename}")


# --- Blocco eseguito solo se lo script viene lanciato direttamente ---
if __name__ == "__main__":
    API_KEY = '2300cb7362ef7560c3e75c5b6aa48b2c'  # Inserisci la tua chiave API qui
    client = WeatherAPI(API_KEY)

    city = input("Inserisci il nome della città: ").strip()
    if not city:
        print("Nessuna città inserita. Uscita.")
        exit()

    print(f"\n=== Ottenendo dati per {city} ===")
    result = client.get_all_data_for_city(city)
    if result:
        output_filename = f"weather_data_{city}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        save_to_json(result, output_filename)
    else:
        print("Nessun dato ottenuto.")
        