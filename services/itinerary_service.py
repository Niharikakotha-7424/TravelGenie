def generate_smart_itinerary(
    destination,
    places,
    days,
    interests=None
):
    """
    Generates a simple rule-based personalized itinerary.

    This is prototype logic.
    A real AI model/API can be connected later.
    """

    interests = interests or []

    selected = []

    for place in places:

        if not interests:
            selected.append(place)
            continue

        category = place.get(
            "category",
            ""
        ).lower()

        if any(
            interest.lower() in category
            for interest in interests
        ):
            selected.append(place)

    for place in places:

        if place not in selected:
            selected.append(place)

    itinerary = []

    index = 0

    for day in range(
        1,
        days + 1
    ):

        day_places = []

        for _ in range(2):

            if index >= len(selected):
                break

            day_places.append(
                selected[index]
            )

            index += 1

        itinerary.append({
            "day": day,
            "destination": destination,
            "places": day_places
        })

    return itinerary