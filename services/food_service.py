import requests


def get_food_places(lat, lon, radius=10000):
    """
    Find real food-related places near a destination
    using OpenStreetMap Overpass API.
    """

    # -----------------------------------------------------
    # CHECK COORDINATES
    # -----------------------------------------------------

    if lat is None or lon is None:
        return {
            "success": False,
            "message": "Destination coordinates are unavailable.",
            "foods": []
        }


    # -----------------------------------------------------
    # OVERPASS QUERY
    # -----------------------------------------------------

    query = f"""
    [out:json][timeout:20];

    (
        node["amenity"="restaurant"](around:{radius},{lat},{lon});
        way["amenity"="restaurant"](around:{radius},{lat},{lon});

        node["amenity"="cafe"](around:{radius},{lat},{lon});
        way["amenity"="cafe"](around:{radius},{lat},{lon});

        node["amenity"="fast_food"](around:{radius},{lat},{lon});
        way["amenity"="fast_food"](around:{radius},{lat},{lon});

        node["amenity"="food_court"](around:{radius},{lat},{lon});
        way["amenity"="food_court"](around:{radius},{lat},{lon});
    );

    out center tags;
    """


    # -----------------------------------------------------
    # OVERPASS SERVERS
    # -----------------------------------------------------

    urls = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter"
    ]


    data = None


    # -----------------------------------------------------
    # REQUEST LIVE DATA
    # -----------------------------------------------------

    for url in urls:

        try:

            response = requests.post(
                url,
                data=query,
                headers={
                    "User-Agent": "TravelGenie/1.0"
                },
                timeout=30
            )

            response.raise_for_status()

            data = response.json()

            print(
                "FOOD API SUCCESS:",
                url
            )

            break


        except requests.exceptions.RequestException as error:

            print(
                "FOOD API REQUEST ERROR:",
                error
            )

            continue


        except ValueError as error:

            print(
                "FOOD API JSON ERROR:",
                error
            )

            continue


    # -----------------------------------------------------
    # BOTH SERVERS FAILED
    # -----------------------------------------------------

    if data is None:

        return {
            "success": False,
            "message": "Unable to fetch live food data.",
            "foods": []
        }


    # -----------------------------------------------------
    # PROCESS FOOD PLACES
    # -----------------------------------------------------

    foods = []

    seen_names = set()


    for element in data.get("elements", []):

        tags = element.get(
            "tags",
            {}
        )


        # -----------------------------------------------
        # FOOD PLACE NAME
        # -----------------------------------------------

        name = tags.get("name")


        if not name:
            continue


        name_key = name.strip().lower()


        if name_key in seen_names:
            continue


        seen_names.add(name_key)


        # -----------------------------------------------
        # FOOD TYPE
        # -----------------------------------------------

        amenity = tags.get(
            "amenity",
            "restaurant"
        )


        type_names = {
            "restaurant": "Restaurant",
            "cafe": "Cafe",
            "fast_food": "Fast Food",
            "food_court": "Food Court"
        }


        food_type = type_names.get(
            amenity,
            "Food Place"
        )


        # -----------------------------------------------
        # GET COORDINATES
        # -----------------------------------------------

        if element.get("type") == "node":

            food_lat = element.get(
                "lat"
            )

            food_lon = element.get(
                "lon"
            )

        else:

            center = element.get(
                "center",
                {}
            )

            food_lat = center.get(
                "lat"
            )

            food_lon = center.get(
                "lon"
            )


        if food_lat is None or food_lon is None:
            continue


        # -----------------------------------------------
        # ADD FOOD PLACE
        # -----------------------------------------------

        foods.append({

            "name": name,

            "type": food_type,

            "lat": float(food_lat),

            "lon": float(food_lon),

            # OpenStreetMap does not reliably provide
            # restaurant prices or ratings.

            "price": None,

            "rating": None,

            "tag": "Live OpenStreetMap Data"

        })


    # -----------------------------------------------------
    # LIMIT RESULTS
    # -----------------------------------------------------

    foods = foods[:20]


    # -----------------------------------------------------
    # RETURN RESULT
    # -----------------------------------------------------

    return {

        "success": True,

        "message": (
            f"Found {len(foods)} food places."
        ),

        "foods": foods

    }