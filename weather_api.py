import requests
from datetime import datetime
from typing import Optional, Dict, Any, Tuple

class WeatherAPI:
    """Client per le API meteo OpenWeatherMap e Open-Meteo"""
    
    def __init__(self, openweather_api_key: str):
        self.OPENWEATHER_API_KEY = openweather_api_key
        self.OWM_CURRENT_URL = "http://api.openweathermap.org/data/2.5/weather"
        self.OWN_FORECAST_URL = "http://api.openweathermap.org/data/2.5/forecast"
        self.OWM_AIR_POLLUTION_URL = "http://api.openweathermap.org/data/2.5/air_pollution"
        self.OWM_GEO_URL = "http://api.openweathermap.org/geo/1.0/direct"
        self.OPEN_METEO_CURRENT_URL = "https://api.open-meteo.com/v1/forecast"

    def get_coordinates(self, city_name: str) -> Tuple[Optional[float], Optional[float]]:
        """Ottiene le coordinate geografiche di una città"""
        params = {
            'q': city_name,
            'limit': 1,
            'appid': self.OPENWEATHER_API_KEY
        }
        print(f"[DEBUG] chiamata geocoding per {city_name}")
        response = requests.get(self.OWM_GEO_URL, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                lat = data[0]['lat']
                lon = data[0]['lon']
                print(f"[DEBUG] coordinate trovate: lat={lat}, lon={lon}")
                return lat, lon
            else:
                print(f"[ERROR] nessuna coordinata trovata per {city_name}")
        else:
            print(f"[ERROR] errore geocoding: {response.status_code} - {response.text}")
        return None, None

    def get_current_weather_owm(self, lat: float, lon: float) -> Optional[Dict]:
        """Ottiene il meteo attuale da OpenWeatherMap"""
        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.OPENWEATHER_API_KEY,
            'units': 'metric'
        }
        response = requests.get(self.OWM_CURRENT_URL, params=params)
        
        if response.status_code == 200:
            print("[DEBUG] Meteo Attuale OWM ok!")
            return response.json()
        else:
            print(f"Errore nella richiesta meteo OpenWeatherMap: {response.status_code}")
            return None

    def get_forecast_5d_own(self, lat: float, lon: float) -> Optional[Dict]:
        """Ottiene le previsioni a 5 giorni da OpenWeatherMap"""
        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.OPENWEATHER_API_KEY,
            'units': 'metric'
        }
        print(f"[DEBUG] Chiamata previsioni 5 giorni OWM")
        response = requests.get(self.OWN_FORECAST_URL, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Errore OWM Forecast: {response.status_code}")
            return None
        
    def get_air_quality_owm(self, lat: float, lon: float) -> Optional[Dict]:
        """Ottiene i dati sulla qualità dell'aria"""
        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.OPENWEATHER_API_KEY
        }
        response = requests.get(self.OWM_AIR_POLLUTION_URL, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Errore nella richiesta qualità aria: {response.status_code}")
            return None

    def get_current_weather_openmeteo(self, lat: float, lon: float) -> Optional[Dict]:
        """Ottiene il meteo attuale da Open-Meteo"""
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

    def get_all_data_for_city(self, city_name: str) -> Optional[Dict[str, Any]]:
        """Raccoglie tutti i dati meteo per una città"""
        lat, lon = self.get_coordinates(city_name)
        if not lat or not lon:
            print(f"Coordinate non trovate per {city_name}")
            return None

        weather_owm = self.get_current_weather_owm(lat, lon)
        air_owm = self.get_air_quality_owm(lat, lon)
        forecast_own = self.get_forecast_5d_own(lat, lon)
        parsed_owm = self._parse_owm_data(weather_owm, air_owm)
        parsed_forecast = self._parse_forecast_data(forecast_own)

        weather_om = self.get_current_weather_openmeteo(lat, lon)
        parsed_om = self._parse_openmeteo_data(weather_om)

        return {
            'city': city_name,
            'openweathermap_current': parsed_owm,
            'openweathermap_forecast_5d': parsed_forecast,
            'openmeteo_current': parsed_om,
            'timestamp': datetime.now().isoformat()
        }

    def _parse_owm_data(self, weather_data: Optional[Dict], air_data: Optional[Dict]) -> Optional[Dict]:
        """Parse dei dati meteo attuali di OpenWeatherMap"""
        if not weather_data:
            print("Dati meteo attuali OWM mancanti per il parsing")
            return None
            
        main = weather_data.get('main', {})
        wind = weather_data.get('wind', {})
        owm_parsed = {
            'temperature': main.get('temp'),
            'feels_like': main.get('feels_like'),
            'humidity': main.get('humidity'),
            'pressure': main.get('pressure'),
            'wind_speed': wind.get('speed', 0),
            'wind_direction': wind.get('deg', 0),
            'description': weather_data.get('weather', [{}])[0].get('description', 'N/A')
        }
        
        if air_data and 'list' in air_data and len(air_data['list']) > 0:
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

    def _parse_forecast_data(self, forecast_data: Optional[Dict]) -> Optional[list]:
        """Parse dei dati previsione di OpenWeatherMap"""
        if not forecast_data or 'list' not in forecast_data:
            print("Dati previsione OWM mancanti o non validi per il parsing")
            return None
            
        parsed_list = []
        for item in forecast_data['list']:
            try:
                main = item['main']
                parsed_list.append({
                    'datetime': item['dt_txt'],
                    'temperature': main['temp'],
                    'feels_like': main['feels_like'],
                    'humidity': main['humidity'],
                    'pressure': main['pressure'],
                    'description': item['weather'][0]['description']
                })
            except (KeyError, IndexError) as e:
                print(f"Errore nel parsing di un elemento della previsione: {e}")
                continue
        return parsed_list

    def _parse_openmeteo_data(self, meteo_data: Optional[Dict]) -> Optional[Dict]:
        """Parse dei dati Open-Meteo"""
        if not meteo_data:
            print("Dati Open-Meteo mancanti per il parsing")
            return None
            
        current = meteo_data.get('current_weather', {})
        return {
            'temperature': current.get('temperature'),
            'windspeed': current.get('windspeed'),
            'winddirection': current.get('winddirection'),
            'time': current.get('time'),
            'weathercode': current.get('weathercode')
        }
