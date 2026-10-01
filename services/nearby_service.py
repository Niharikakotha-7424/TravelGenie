import requests


def get_nearby_places(
    lat,
    lon,
    radius=10000
):
    """
    Find real nearby places around a destination
    using OpenStreetMap Overpass API.
    """

    if lat is None or lon is None:

        return {
            "success": False,
            "message": "Destination coordinates are unavailable.",
            "places": []
        }


    # -----------------------------------------------------
    # FIND NEARBY TOURIST / NATURE / CULTURE PLACES
    # -----------------------------------------------------

    query = f"""
    [out:json][timeout:25];

    (
        node["tourism"="attraction"](around:{radius},{lat},{lon});
        way["tourism"="attraction"](around:{radius},{lat},{lon});

        node["tourism"="viewpoint"](around:{radius},{lat},{lon});
        way["tourism"="viewpoint"](around:{radius},{lat},{lon});

        node["tourism"="museum"](around:{radius},{lat},{lon});
        way["tourism"="museum"](around:{radius},{lat},{lon});

        node["historic"](around:{radius},{lat},{lon});
        way["historic"](around:{radius},{lat},{lon});

        node["natural"="waterfall"](around:{radius},{lat},{lon});
        way["natural"="waterfall"](around:{radius},{lat},{lon});

        node["natural"="peak"](around:{radius},{lat},{lon});
        way["natural"="peak"](around:{radius},{lat},{lon});

        node["leisure"="park"](around:{radius},{lat},{lon});
        way["leisure"="park"](around:{radius},{lat},{lon});
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
    # REQUEST DATA
    # -----------------------------------------------------

    for url in urls:

        try:

            response = requests.post(
                url,
                data=query,
                headers={
                    "User-Agent":
                        "TravelGenie/1.0"
                },
                timeout=35
            )

            response.raise_for_status()

            data = response.json()

            print(
                "NEARBY API SUCCESS:",
                url
            )

            break


        except requests.exceptions.RequestException as error:

            print(
                "NEARBY API REQUEST ERROR:",
                error
            )

            continue


        except ValueError as error:

            print(
                "NEARBY API JSON ERROR:",
                error
            )

            continue


    # -----------------------------------------------------
    # NO DATA
    # -----------------------------------------------------

    if data is None:

        return {
            "success": False,
            "message":
                "Unable to fetch live nearby places.",
            "places": []
        }


    # -----------------------------------------------------
    # PROCESS RESULTS
    # -----------------------------------------------------

    places = []

    seen_names = set()


    for element in data.get(
        "elements",
        []
    ):

        tags = element.get(
            "tags",
            {}
        )


        name = tags.get(
            "name"
        )


        # Ignore unnamed places

        if not name:
            continue


        name_key = name.strip().lower()


        # Remove duplicate names

        if name_key in seen_names:
            continue


        seen_names.add(
            name_key
        )


        # -------------------------------------------------
        # GET COORDINATES
        # -------------------------------------------------

        if element.get("type") == "node":

            place_lat = element.get(
                "lat"
            )

            place_lon = element.get(
                "lon"
            )

        else:

            center = element.get(
                "center",
                {}
            )

            place_lat = center.get(
                "lat"
            )

            place_lon = center.get(
                "lon"
            )


        if (
            place_lat is None
            or place_lon is None
        ):

            continue


        # -------------------------------------------------
        # DETERMINE CATEGORY
        # -------------------------------------------------

        if tags.get("tourism") == "viewpoint":

            category = "Viewpoint"

        elif tags.get("tourism") == "museum":

            category = "Museum"

        elif tags.get("tourism") == "attraction":

            category = "Attraction"

        elif "historic" in tags:

            category = "Historic"

        elif tags.get("natural") == "waterfall":

            category = "Waterfall"

        elif tags.get("natural") == "peak":

            category = "Nature"

        elif tags.get("leisure") == "park":

            category = "Park"

        else:

            category = "Hidden Gem"


        places.append({

            "name": name,

            "category": category,

            "lat": float(place_lat),

            "lon": float(place_lon),

            "tag": "Live OpenStreetMap Data"

        })


    # -----------------------------------------------------
    # LIMIT RESULTS
    # -----------------------------------------------------

    places = places[:30]


    return {

        "success": True,

        "message":
            f"Found {len(places)} nearby places.",

        "places": places

    }