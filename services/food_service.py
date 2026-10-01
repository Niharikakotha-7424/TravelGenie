import requests


# -----------------------------------------------------
# DEMO FALLBACK FOOD DATA
# -----------------------------------------------------

def get_demo_food_places(lat, lon):
    """
    Fallback food data used when OpenStreetMap Overpass
    services are unavailable.

    These are clearly marked as Demo Data.
    """

    return [
        {
            "name": "Local Restaurant",
            "type": "Restaurant",
            "lat": float(lat) + 0.003,
            "lon": float(lon) + 0.003,
            "price": None,
            "rating": None,
            "tag": "Demo Data"
        },
        {
            "name": "City Cafe",
            "type": "Cafe",
            "lat": float(lat) - 0.002,
            "lon": float(lon) + 0.002,
            "price": None,
            "rating": None,
            "tag": "Demo Data"
        },
        {
            "name": "Local Food Court",
            "type": "Food Court",
            "lat": float(lat) + 0.002,
            "lon": float(lon) - 0.003,
            "price": None,
            "rating": None,
            "tag": "Demo Data"
        }
    ]


# -----------------------------------------------------
# GET FOOD PLACES
# -----------------------------------------------------

def get_food_places(lat, lon, radius=10000):
    """
    Find real food-related places near a destination
    using OpenStreetMap Overpass API.

    If Overpass is unavailable, return clearly labelled
    demo data instead of causing the Flask page to fail.
    """

    # -------------------------------------------------
    # CHECK COORDINATES
    # -------------------------------------------------

    if lat is None or lon is None:

        return {
            "success": False,
            "message": "Destination coordinates are unavailable.",
            "foods": []
        }

    try:
        lat = float(lat)
        lon = float(lon)

    except (TypeError, ValueError):

        return {
            "success": False,
            "message": "Invalid destination coordinates.",
            "foods": []
        }


    # -------------------------------------------------
    # OVERPASS QUERY
    # -------------------------------------------------

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


    # -------------------------------------------------
    # OVERPASS SERVERS
    # -------------------------------------------------

    urls = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.private.coffee/api/interpreter"
    ]


    data = None


    # -------------------------------------------------
    # REQUEST LIVE DATA
    # -------------------------------------------------

    for url in urls:

        try:

            print(
                "FOOD API REQUEST:",
                url
            )

            response = requests.post(
                url,
                data=query,
                headers={
                    "User-Agent": (
                        "TravelGenie/1.0 "
                        "(travel planning application)"
                    )
                },
                timeout=15
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
                url,
                error
            )

            continue


        except ValueError as error:

            print(
                "FOOD API JSON ERROR:",
                url,
                error
            )

            continue


    # -------------------------------------------------
    # ALL OVERPASS SERVERS FAILED
    # -------------------------------------------------

    if data is None:

        print(
            "FOOD API UNAVAILABLE - USING DEMO DATA"
        )

        demo_foods = get_demo_food_places(
            lat,
            lon
        )

        return {
            "success": True,
            "message": (
                "Live food data is temporarily unavailable. "
                "Showing Demo Data."
            ),
            "foods": demo_foods
        }


    # -------------------------------------------------
    # PROCESS FOOD PLACES
    # -------------------------------------------------

    foods = []

    seen_names = set()


    for element in data.get(
        "elements",
        []
    ):

        tags = element.get(
            "tags",
            {}
        )


        # ---------------------------------------------
        # FOOD PLACE NAME
        # ---------------------------------------------

        name = tags.get(
            "name"
        )


        if not name:
            continue


        name = name.strip()


        if not name:
            continue


        name_key = name.lower()


        if name_key in seen_names:
            continue


        seen_names.add(
            name_key
        )


        # ---------------------------------------------
        # FOOD TYPE
        # ---------------------------------------------

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


        # ---------------------------------------------
        # GET COORDINATES
        # ---------------------------------------------

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


        if (
            food_lat is None
            or food_lon is None
        ):
            continue


        # ---------------------------------------------
        # ADD FOOD PLACE
        # ---------------------------------------------

        try:

            food_lat = float(
                food_lat
            )

            food_lon = float(
                food_lon
            )

        except (
            TypeError,
            ValueError
        ):

            continue


        foods.append({

            "name": name,

            "type": food_type,

            "lat": food_lat,

            "lon": food_lon,

            # OSM does not reliably provide
            # restaurant prices or ratings.

            "price": None,

            "rating": None,

            "tag": "Live OpenStreetMap Data"

        })


    # -------------------------------------------------
    # NO LIVE RESULTS
    # -------------------------------------------------

    if not foods:

        print(
            "FOOD API RETURNED NO NAMED PLACES - "
            "USING DEMO DATA"
        )

        demo_foods = get_demo_food_places(
            lat,
            lon
        )

        return {

            "success": True,

            "message": (
                "No named food places were found. "
                "Showing Demo Data."
            ),

            "foods": demo_foods

        }


    # -------------------------------------------------
    # LIMIT RESULTS
    # -------------------------------------------------

    foods = foods[:20]


    # -------------------------------------------------
    # RETURN LIVE RESULT
    # -------------------------------------------------

    return {

        "success": True,

        "message": (
            f"Found {len(foods)} food places."
        ),

        "foods": foods

    }
