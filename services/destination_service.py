def calculate_budget(
    days,
    travelers,
    transport,
    accommodation,
    activity_level
):

    transport_rates = {
        "Bus": 250,
        "Train": 400,
        "Flight": 1800,
        "Cab": 900,
        "Local": 180
    }

    stay_rates = {
        "Hostel": 450,
        "Hotel": 900,
        "Homestay": 700,
        "Lockers": 250
    }

    activity_rates = {
        "Low": 150,
        "Medium": 300,
        "High": 550
    }

    transport_cost = (
        transport_rates.get(
            transport,
            400
        )
        * travelers
    )

    stay_cost = (
        stay_rates.get(
            accommodation,
            600
        )
        * days
        * travelers
    )

    food_cost = (
        300
        * days
        * travelers
    )

    activity_cost = (
        activity_rates.get(
            activity_level,
            300
        )
        * days
        * travelers
    )

    other_cost = (
        100
        * days
        * travelers
    )

    total = (
        transport_cost
        + stay_cost
        + food_cost
        + activity_cost
        + other_cost
    )

    return {
        "transport": transport_cost,
        "stay": stay_cost,
        "food": food_cost,
        "activities": activity_cost,
        "other": other_cost,
        "total": total
    }