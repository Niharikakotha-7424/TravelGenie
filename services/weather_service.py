import requests
from config import OPENWEATHER_API_KEY


def get_weather(city):
    """Get current weather information for a city."""

    if not OPENWEATHER_API_KEY:
        return {
            "success": False,
            "message": "OpenWeather API key is not configured."
        }

    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric"
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        return {
            "success": True,
            "city": data["name"],
            "temperature": round(data["main"]["temp"], 1),
            "feels_like": round(data["main"]["feels_like"], 1),
            "humidity": data["main"]["humidity"],
            "description": data["weather"][0]["description"].title(),
            "icon": data["weather"][0]["icon"]
        }

    except requests.exceptions.RequestException:
        return {
            "success": False,
            "message": "Unable to fetch weather data."
        }

    except (KeyError, TypeError, ValueError):
        return {
            "success": False,
            "message": "Invalid weather data received."
        }