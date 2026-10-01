# =========================================================
# LOCAL GUIDE SERVICE
# =========================================================

def get_local_guides(destination):
    """
    Return local guide information for the selected destination.

    This version uses clearly labelled demo guide profiles.
    No fake mobile numbers or personal contact details are used.
    """

    destination = (destination or "").strip()

    if not destination:
        return {
            "success": False,
            "message": "Destination is required.",
            "guides": [],
            "data_source": "Demo Data"
        }

    guides = [
        {
            "name": "Local Culture Guide",
            "location": destination,
            "languages": "English, Telugu",
            "expertise": "Culture & sightseeing",
            "rating": 4.7,
            "experience": "Local sightseeing and cultural experiences",
            "data_source": "Demo Data"
        },
        {
            "name": "Nature Explorer Guide",
            "location": destination,
            "languages": "English, Hindi",
            "expertise": "Nature & photography",
            "rating": 4.6,
            "experience": "Nature spots, viewpoints and photography",
            "data_source": "Demo Data"
        },
        {
            "name": "Food Experience Guide",
            "location": destination,
            "languages": "English, Telugu",
            "expertise": "Local food experiences",
            "rating": 4.8,
            "experience": "Local food and popular food places",
            "data_source": "Demo Data"
        }
    ]

    return {
        "success": True,
        "message": f"Found {len(guides)} local guide options.",
        "guides": guides,
        "data_source": "Demo Data"
    }