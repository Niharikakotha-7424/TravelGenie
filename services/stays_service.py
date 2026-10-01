import requests


def get_stays(lat, lon, radius=10000):
    """
    Find real accommodation places near a destination
    using OpenStreetMap Overpass API.

    Returns real OSM places when available.
    """

    if lat is None or lon is None:
        return {
            "success": False,
            "message": "Destination coordinates are unavailable.",
            "stays": []
        }

    query = f"""
    [out:json][timeout:20];

    (
        node[
            tourism=hotel
        ](
            around:{radius},{lat},{lon}
        );

        way[
            tourism=hotel
        ](
            around:{radius},{lat},{lon}
        );

        node[
            tourism=hostel
        ](
            around:{radius},{lat},{lon}
        );

        way[
            tourism=hostel
        ](
            around:{radius},{lat},{lon}
        );

        node[
            tourism=guest_house
        ](
            around:{radius},{lat},{lon}
        );

        way[
            tourism=guest_house
        ](
            around:{radius},{lat},{lon}
        );

        node[
            tourism=apartment
        ](
            around:{radius},{lat},{lon}
        );

        way[
            tourism=apartment
        ](
            around:{radius},{lat},{lon}
        );
    );

    out center tags;
    """

    urls = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter"
    ]

    data = None

    for url in urls:

        try:

            response = requests.post(
                url,
                data=query,
                timeout=30
            )

            response.raise_for_status()

            data = response.json()

            break

        except (
            requests.exceptions.RequestException,
            ValueError
        ):
            continue

    if data is None:

        return {
            "success": False,
            "message": "Unable to fetch live accommodation data.",
            "stays": []
        }

    stays = []

    seen_names = set()

    for element in data.get("elements", []):

        tags = element.get("tags", {})

        name = tags.get("name")

        if not name:
            continue

        name_key = name.strip().lower()

        if name_key in seen_names:
            continue

        seen_names.add(name_key)

        tourism_type = tags.get(
            "tourism",
            "accommodation"
        )

        type_names = {
            "hotel": "Hotel",
            "hostel": "Hostel",
            "guest_house": "Guest House",
            "apartment": "Apartment"
        }

        stay_type = type_names.get(
            tourism_type,
            "Accommodation"
        )

        if element.get("type") == "node":

            stay_lat = element.get("lat")
            stay_lon = element.get("lon")

        else:

            center = element.get(
                "center",
                {}
            )

            stay_lat = center.get("lat")
            stay_lon = center.get("lon")

        if stay_lat is None or stay_lon is None:
            continue

        stays.append({
            "name": name,
            "type": stay_type,
            "lat": float(stay_lat),
            "lon": float(stay_lon),

            # OSM does not guarantee price/rating.
            "price": None,
            "rating": None,

            "tag": "Live OpenStreetMap Data"
        })

    # Keep the page manageable
    stays = stays[:20]

    return {
        "success": True,
        "message": (
            f"Found {len(stays)} accommodation places."
        ),
        "stays": stays
    }