import requests


def geocode_place(place):
    """
    Find the real latitude and longitude of a place
    using OpenStreetMap Nominatim.
    """

    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": place,
        "format": "json",
        "limit": 1,
        "countrycodes": "in"
    }

    headers = {
        "User-Agent": "TravelGenie/1.0"
    }

    try:
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()

        results = response.json()

        if not results:
            return {
                "success": False,
                "message": "Destination not found."
            }

        location = results[0]

        return {
            "success": True,
            "name": location.get("display_name", place),
            "lat": float(location["lat"]),
            "lon": float(location["lon"])
        }

    except requests.exceptions.RequestException:
        return {
            "success": False,
            "message": "Unable to connect to location service."
        }

    except (KeyError, TypeError, ValueError):
        return {
            "success": False,
            "message": "Invalid location data received."
        }