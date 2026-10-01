from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify
)

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

import json
import os
import requests

from config import (
    OPENAI_API_KEY,
    OPENWEATHER_API_KEY,
    GOOGLE_MAPS_API_KEY
)

from services.weather_service import get_weather
from services.geocoding_service import geocode_place
from services.stays_service import get_stays
from services.food_service import get_food_places
from services.nearby_service import get_nearby_places
from services.guide_service import get_local_guides


app = Flask(__name__)


# =========================================================
# CONFIGURATION
# =========================================================

app.config["SECRET_KEY"] = "travelgenie-development-secret-key"

BASE_DIR = os.path.abspath(
    os.path.dirname(__file__)
)

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "travelgenie.db"
)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///" + DATABASE_PATH
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# =========================================================
# DATABASE MODELS
# =========================================================

class User(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    full_name = db.Column(
        db.String(120),
        nullable=False
    )

    username = db.Column(
        db.String(80),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    mobile = db.Column(
        db.String(20),
        nullable=True
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    trips = db.relationship(
        "Trip",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def set_password(self, password):

        self.password_hash = generate_password_hash(
            password
        )

    def check_password(self, password):

        return check_password_hash(
            self.password_hash,
            password
        )


class Trip(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    title = db.Column(
        db.String(150),
        nullable=False
    )

    destination = db.Column(
        db.String(120),
        nullable=False
    )

    start_location = db.Column(
        db.String(120),
        nullable=True
    )

    days = db.Column(
        db.Integer,
        nullable=False
    )

    travelers = db.Column(
        db.Integer,
        nullable=False
    )

    budget = db.Column(
        db.Float,
        nullable=False
    )

    estimated_cost = db.Column(
        db.Float,
        nullable=False
    )

    itinerary_json = db.Column(
        db.Text,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )



class GuideRequest(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=True
    )

    guide_name = db.Column(
        db.String(120),
        nullable=False
    )

    destination = db.Column(
        db.String(120),
        nullable=False
    )

    traveler_name = db.Column(
        db.String(120),
        nullable=False
    )

    traveler_email = db.Column(
        db.String(120),
        nullable=False
    )

    traveler_mobile = db.Column(
        db.String(20),
        nullable=True
    )

    preferred_date = db.Column(
        db.String(30),
        nullable=False
    )

    preferred_time = db.Column(
        db.String(30),
        nullable=False
    )

    language = db.Column(
        db.String(50),
        nullable=False
    )

    travelers = db.Column(
        db.Integer,
        nullable=False
    )

    message = db.Column(
        db.Text,
        nullable=True
    )

    status = db.Column(
        db.String(30),
        default="Pending"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

# =========================================================
# REVIEW MODEL
# =========================================================

class Review(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    destination = db.Column(
        db.String(120),
        nullable=False
    )

    item_name = db.Column(
        db.String(150),
        nullable=False
    )

    category = db.Column(
        db.String(50),
        nullable=False
    )

    rating = db.Column(
        db.Integer,
        nullable=False
    )

    review_text = db.Column(
        db.Text,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user = db.relationship(
        "User",
        backref="reviews",
        lazy=True
    )


# =========================================================
# DESTINATION DATA
# =========================================================

DESTINATIONS = {

    "visakhapatnam": {

        "name": "Visakhapatnam",

        "state": "Andhra Pradesh",

        "lat": 17.6868,

        "lon": 83.2185,

        "description":
            "A beautiful coastal city known for beaches, hills, "
            "food and scenic viewpoints.",

        "places": [

            {
                "name": "RK Beach",
                "category": "Beach",
                "cost": 0,
                "duration": 90,
                "lat": 17.7126,
                "lon": 83.3229
            },

            {
                "name": "Kailasagiri",
                "category": "Nature",
                "cost": 50,
                "duration": 120,
                "lat": 17.7474,
                "lon": 83.3422
            },

            {
                "name":
                    "INS Kurusura Submarine Museum",
                "category": "Culture",
                "cost": 100,
                "duration": 90,
                "lat": 17.7101,
                "lon": 83.3195
            },

            {
                "name": "Simhachalam",
                "category": "Spiritual",
                "cost": 0,
                "duration": 120,
                "lat": 17.7667,
                "lon": 83.2500
            },

            {
                "name": "Yarada Beach",
                "category": "Beach",
                "cost": 0,
                "duration": 120,
                "lat": 17.6588,
                "lon": 83.2705
            }
        ],

        "foods": [
            "Andhra meals",
            "Seafood",
            "Punugulu",
            "Dosa",
            "Local street food"
        ],

        "tips": [
            "Carry water during sightseeing.",
            "Beach visits are better during morning or evening.",
            "Keep some flexibility for traffic."
        ]
    },


    "hyderabad": {

        "name": "Hyderabad",

        "state": "Telangana",

        "lat": 17.3850,

        "lon": 78.4867,

        "description":
            "A historic and modern city famous for heritage, "
            "food, shopping and technology.",

        "places": [

            {
                "name": "Charminar",
                "category": "Culture",
                "cost": 50,
                "duration": 90,
                "lat": 17.3616,
                "lon": 78.4747
            },

            {
                "name": "Golconda Fort",
                "category": "History",
                "cost": 25,
                "duration": 150,
                "lat": 17.3833,
                "lon": 78.4011
            },

            {
                "name": "Hussain Sagar",
                "category": "Nature",
                "cost": 0,
                "duration": 90,
                "lat": 17.4239,
                "lon": 78.4738
            },

            {
                "name": "Salar Jung Museum",
                "category": "Culture",
                "cost": 50,
                "duration": 120,
                "lat": 17.3713,
                "lon": 78.4804
            },

            {
                "name": "Birla Mandir",
                "category": "Spiritual",
                "cost": 0,
                "duration": 90,
                "lat": 17.4062,
                "lon": 78.4691
            }
        ],

        "foods": [
            "Hyderabadi Biryani",
            "Haleem",
            "Irani Chai",
            "Osmania Biscuits",
            "Street food"
        ],

        "tips": [
            "Plan heritage attractions together.",
            "Avoid peak traffic hours.",
            "Try local food at trusted locations."
        ]
    },


    "goa": {

        "name": "Goa",

        "state": "Goa",

        "lat": 15.4909,

        "lon": 73.8278,

        "description":
            "A popular destination for beaches, culture, food "
            "and relaxed travel experiences.",

        "places": [

            {
                "name": "Baga Beach",
                "category": "Beach",
                "cost": 0,
                "duration": 120,
                "lat": 15.5557,
                "lon": 73.7517
            },

            {
                "name": "Calangute Beach",
                "category": "Beach",
                "cost": 0,
                "duration": 120,
                "lat": 15.5440,
                "lon": 73.7550
            },

            {
                "name": "Basilica of Bom Jesus",
                "category": "Culture",
                "cost": 0,
                "duration": 90,
                "lat": 15.5009,
                "lon": 73.9115
            },

            {
                "name": "Fort Aguada",
                "category": "History",
                "cost": 50,
                "duration": 120,
                "lat": 15.4920,
                "lon": 73.7730
            },

            {
                "name": "Dona Paula",
                "category": "Nature",
                "cost": 0,
                "duration": 90,
                "lat": 15.4589,
                "lon": 73.8050
            }
        ],

        "foods": [
            "Goan thali",
            "Seafood",
            "Pav bhaji",
            "Local snacks",
            "Fresh fruit drinks"
        ],

        "tips": [
            "Carry sunscreen and water.",
            "Keep travel time between beaches in mind.",
            "Respect local rules and surroundings."
        ]
    },


    "araku valley": {

        "name": "Araku Valley",

        "state": "Andhra Pradesh",

        "lat": 18.3273,

        "lon": 82.8760,

        "description":
            "A scenic hill destination known for greenery, "
            "coffee plantations and tribal culture.",

        "places": [

            {
                "name": "Borra Caves",
                "category": "Adventure",
                "cost": 60,
                "duration": 120,
                "lat": 18.2800,
                "lon": 83.0480
            },

            {
                "name": "Araku Tribal Museum",
                "category": "Culture",
                "cost": 20,
                "duration": 90,
                "lat": 18.3275,
                "lon": 82.8770
            },

            {
                "name": "Coffee Museum",
                "category": "Food",
                "cost": 20,
                "duration": 60,
                "lat": 18.3260,
                "lon": 82.8780
            },

            {
                "name": "Katiki Waterfalls",
                "category": "Nature",
                "cost": 50,
                "duration": 120,
                "lat": 18.2780,
                "lon": 83.0200
            }
        ],

        "foods": [
            "Araku coffee",
            "Tribal cuisine",
            "Andhra meals",
            "Local snacks"
        ],

        "tips": [
            "Carry comfortable shoes.",
            "Weather can change quickly in hill areas.",
            "Keep enough time for transportation."
        ]
    },


    "jaipur": {

        "name": "Jaipur",

        "state": "Rajasthan",

        "lat": 26.9124,

        "lon": 75.7873,

        "description":
            "The Pink City, known for forts, palaces, culture "
            "and traditional food.",

        "places": [

            {
                "name": "Amber Fort",
                "category": "History",
                "cost": 100,
                "duration": 150,
                "lat": 26.9855,
                "lon": 75.8513
            },

            {
                "name": "Hawa Mahal",
                "category": "Culture",
                "cost": 50,
                "duration": 90,
                "lat": 26.9239,
                "lon": 75.8267
            },

            {
                "name": "City Palace",
                "category": "Culture",
                "cost": 200,
                "duration": 120,
                "lat": 26.9258,
                "lon": 75.8237
            },

            {
                "name": "Jantar Mantar",
                "category": "Culture",
                "cost": 50,
                "duration": 90,
                "lat": 26.9247,
                "lon": 75.8246
            }
        ],

        "foods": [
            "Dal Baati Churma",
            "Ghewar",
            "Kachori",
            "Rajasthani thali",
            "Lassi"
        ],

        "tips": [
            "Carry water during fort visits.",
            "Start sightseeing early.",
            "Keep some time for local shopping."
        ]
    }
}


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def get_destination(destination):

    key = destination.strip().lower()

    if key in DESTINATIONS:
        return DESTINATIONS[key]

    for name, data in DESTINATIONS.items():

        if key in name or name in key:
            return data

    return None


def current_user():

    username = session.get(
        "username"
    )

    if not username:
        return None

    return User.query.filter_by(
        username=username
    ).first()


def login_required():

    return "username" in session


def get_transport_cost(transport):

    rates = {

        "Bus": 250,

        "Train": 400,

        "Flight": 1800,

        "Cab": 900,

        "Local": 180

    }

    return rates.get(
        transport,
        400
    )


def get_stay_cost(accommodation):

    rates = {

        "Hostel": 450,

        "Hotel": 900,

        "Homestay": 700,

        "Lockers": 250

    }

    return rates.get(
        accommodation,
        600
    )


def get_activity_cost(level):

    rates = {

        "Low": 150,

        "Medium": 300,

        "High": 550

    }

    return rates.get(
        level,
        300
    )

# =========================================================
# OSRM ROAD ROUTE
# =========================================================

def get_road_route(route_points):

    coordinates = []

    for point in route_points:

        lat = point.get("lat")
        lon = point.get("lon")

        if (
            lat is not None
            and lon is not None
        ):

            coordinates.append(
                f"{lon},{lat}"
            )

    # Need at least two points
    if len(coordinates) < 2:

        return {
            "success": False,
            "message": "Not enough locations for a route."
        }

    # OSRM expects:
    # longitude,latitude;longitude,latitude

    coordinate_string = ";".join(
        coordinates
    )

    url = (
        "https://router.project-osrm.org/"
        f"route/v1/driving/{coordinate_string}"
    )

    params = {
        "overview": "full",
        "geometries": "geojson",
        "steps": "false"
    }

    try:

        import requests

        response = requests.get(
            url,
            params=params,
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        if data.get("code") != "Ok":

            return {
                "success": False,
                "message": "Road route could not be calculated."
            }

        routes = data.get(
            "routes",
            []
        )

        if not routes:

            return {
                "success": False,
                "message": "No route found."
            }

        route = routes[0]

        geometry = route.get(
            "geometry",
            {}
        )

        route_coordinates = geometry.get(
            "coordinates",
            []
        )

        # GeoJSON gives [lon, lat]
        # Leaflet needs [lat, lon]

        leaflet_coordinates = [

            [
                coordinate[1],
                coordinate[0]
            ]

            for coordinate in route_coordinates

            if len(coordinate) >= 2

        ]

        return {

            "success": True,

            "coordinates":
                leaflet_coordinates,

            "distance_km":
                round(
                    route.get(
                        "distance",
                        0
                    ) / 1000,
                    2
                ),

            "duration_minutes":
                round(
                    route.get(
                        "duration",
                        0
                    ) / 60
                )

        }

    except requests.exceptions.RequestException:

        return {
            "success": False,
            "message": "Unable to connect to routing service."
        }

    except (
        KeyError,
        TypeError,
        ValueError
    ):

        return {
            "success": False,
            "message": "Invalid route data received."
        }


# =========================================================
# BUDGET CALCULATION
# =========================================================

def calculate_budget(
    days,
    travelers,
    transport,
    accommodation,
    activity_level
):

    transport_cost = (
        get_transport_cost(
            transport
        )
        * travelers
    )

    stay_cost = (
        get_stay_cost(
            accommodation
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
        get_activity_cost(
            activity_level
        )
        * days
        * travelers
    )

    sightseeing_buffer = (
        100
        * days
        * travelers
    )

    total = (
        transport_cost
        + stay_cost
        + food_cost
        + activity_cost
        + sightseeing_buffer
    )

    return {

        "transport": transport_cost,

        "stay": stay_cost,

        "food": food_cost,

        "activities": activity_cost,

        "other": sightseeing_buffer,

        "total": total

    }


# =========================================================
# ITINERARY CREATION
# =========================================================

def create_itinerary(
    destination_data,
    days,
    travelers,
    interests,
    activity_level
):

    places = destination_data["places"]

    selected = []

    interests_lower = [

        item.strip().lower()

        for item in interests

        if item.strip()

    ]

    interest_keywords = {

        "nature": [
            "nature",
            "hill",
            "waterfall",
            "lake",
            "park",
            "viewpoint"
        ],

        "beaches": [
            "beach",
            "coast",
            "sea"
        ],

        "food": [
            "food",
            "restaurant",
            "cafe",
            "food court"
        ],

        "adventure": [
            "adventure",
            "cave",
            "trek",
            "waterfall"
        ],

        "culture": [
            "culture",
            "history",
            "museum",
            "fort",
            "palace"
        ],

        "shopping": [
            "shopping",
            "market",
            "bazaar"
        ],

        "spiritual": [
            "spiritual",
            "temple",
            "church",
            "mosque"
        ]
    }

    for place in places:

        place_category = place.get(
            "category",
            ""
        ).strip().lower()

        place_name = place.get(
            "name",
            ""
        ).strip().lower()

        matched = False

        for interest in interests_lower:

            keywords = interest_keywords.get(
                interest,
                [interest]
            )

            for keyword in keywords:

                if (
                    keyword in place_category
                    or keyword in place_name
                ):

                    matched = True
                    break

            if matched:
                break

        if matched and place not in selected:

            selected.append(place)

    if activity_level.lower() == "low":

        places_sorted = sorted(
            places,
            key=lambda place: place["duration"]
        )

    elif activity_level.lower() == "high":

        places_sorted = sorted(
            places,
            key=lambda place: place["duration"],
            reverse=True
        )

    else:

        places_sorted = places[:]

    for place in places_sorted:

        if place not in selected:

            selected.append(place)

    itinerary = []

    place_index = 0

    for day in range(
        1,
        days + 1
    ):

        day_places = []

        for _ in range(2):

            if place_index >= len(selected):
                break

            place = selected[
                place_index
            ]

            if len(day_places) == 0:

                visit_time = "09:00 AM"

            else:

                visit_time = "02:30 PM"

            day_places.append({

                "time": visit_time,

                "place": place["name"],

                "category": place["category"],

                "duration": place["duration"],

                "cost": place["cost"],

                "lat": place["lat"],

                "lon": place["lon"]

            })

            place_index += 1

        itinerary.append({

            "day": day,

            "title":
                f"Day {day} — Explore "
                f"{destination_data['name']}",

            "places": day_places

        })

    return itinerary


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template(
        "home.html",
        user=current_user(),
        destinations=list(
            DESTINATIONS.values()
        )
    )


# =========================================================
# WEATHER API
# =========================================================

@app.route("/api/weather")
def weather_api():

    city = request.args.get(
        "city",
        ""
    ).strip()

    if not city:

        return jsonify({

            "success": False,

            "message":
                "Please provide a city name."

        }), 400

    weather = get_weather(
        city
    )

    return jsonify(
        weather
    )


# =========================================================
# GEOCODING API
# =========================================================

@app.route("/api/geocode")
def geocode_api():

    place = request.args.get(
        "place",
        ""
    ).strip()

    if not place:

        return jsonify({

            "success": False,

            "message":
                "Please provide a place name."

        }), 400

    location = geocode_place(
        place
    )

    return jsonify(
        location
    )


# =========================================================
# PLANNER
# =========================================================

@app.route(
    "/planner",
    methods=["GET", "POST"]
)
def planner():

    if request.method == "POST":

        start_location = request.form.get(
            "start_location",
            ""
        ).strip()

        destination = request.form.get(
            "destination",
            ""
        ).strip()

        days = int(
            request.form.get(
                "days",
                1
            )
        )

        travelers = int(
            request.form.get(
                "travelers",
                1
            )
        )

        budget = float(
            request.form.get(
                "budget",
                0
            )
        )

        purpose = request.form.get(
            "purpose",
            "Relaxation"
        )

        interests_raw = request.form.get(
            "interests",
            ""
        )

        interests = [

            x.strip()

            for x in interests_raw.split(",")

            if x.strip()

        ]

        transport = request.form.get(
            "transport",
            "Bus"
        )

        accommodation = request.form.get(
            "accommodation",
            "Hostel"
        )

        food = request.form.get(
            "food",
            "Both"
        )

        activity_level = request.form.get(
            "activity_level",
            "Medium"
        )

        language = request.form.get(
            "language",
            "English"
        )

        accessibility = request.form.get(
            "accessibility",
            "None"
        )

        special_preference = request.form.get(
            "special_preference",
            ""
        )

        destination_data = get_destination(
            destination
        )

        # -------------------------------------------------
        # UNKNOWN DESTINATION FALLBACK
        # -------------------------------------------------

        if destination_data is None:

            destination_data = {

                "name":
                    destination.title(),

                "state":
                    "India",

                "lat":
                    20.5937,

                "lon":
                    78.9629,

                "description":
                    "Destination information is currently "
                    "shown as Demo Data.",

                "places": [

                    {
                        "name":
                            f"{destination.title()} City Center",

                        "category":
                            "Culture",

                        "cost":
                            0,

                        "duration":
                            90,

                        "lat":
                            20.5937,

                        "lon":
                            78.9629
                    },

                    {
                        "name":
                            f"{destination.title()} Local Market",

                        "category":
                            "Food",

                        "cost":
                            100,

                        "duration":
                            90,

                        "lat":
                            20.6000,

                        "lon":
                            78.9700
                    },

                    {
                        "name":
                            f"{destination.title()} Scenic Spot",

                        "category":
                            "Nature",

                        "cost":
                            50,

                        "duration":
                            120,

                        "lat":
                            20.5850,

                        "lon":
                            78.9500
                    }
                ],

                "foods": [

                    "Local cuisine",

                    "Popular street food",

                    "Regional meals"

                ],

                "tips": [

                    "Demo Data — connect a destination API "
                    "for live information."

                ]
            }

        budget_data = calculate_budget(

            days,

            travelers,

            transport,

            accommodation,

            activity_level

        )

        itinerary = create_itinerary(

            destination_data,

            days,

            travelers,

            interests,

            activity_level

        )

        trip = {

            "start_location":
                start_location,

            "destination":
                destination_data["name"],

            "state":
                destination_data["state"],

            "days":
                days,

            "travelers":
                travelers,

            "budget":
                budget,

            "purpose":
                purpose,

            "interests":
                interests,

            "transport":
                transport,

            "accommodation":
                accommodation,

            "food":
                food,

            "activity_level":
                activity_level,

            "language":
                language,

            "accessibility":
                accessibility,

            "special_preference":
                special_preference,

            "description":
                destination_data["description"],

            "itinerary":
                itinerary,

            "budget_data":
                budget_data,

            "foods":
                destination_data["foods"],

            "tips":
                destination_data["tips"],

            "places":
                destination_data["places"],

            "demo_data":
                destination not in DESTINATIONS

        }

        session[
            "current_trip"
        ] = trip

        return redirect(
            url_for("analyzing")
        )

    return render_template(
        "planner.html",
        user=current_user()
    )


# =========================================================
# ANALYZING
# =========================================================

@app.route("/analyzing")
def analyzing():

    if "current_trip" not in session:

        return redirect(
            url_for("planner")
        )

    return render_template(
        "analyzing.html",
        user=current_user()
    )


# =========================================================
# TRIP RESULT
# =========================================================

@app.route("/result")
def result():

    trip = session.get(
        "current_trip"
    )

    if not trip:

        return redirect(
            url_for("planner")
        )

    weather = get_weather(
        trip["destination"]
    )

    location = geocode_place(
        trip["destination"]
    )

    return render_template(

        "result.html",

        trip=trip,

        user=current_user(),

        weather=weather,

        location=location

    )


# =========================================================
# BUDGET OPTIMIZER
# =========================================================

@app.route("/budget")
def budget():

    trip = session.get(
        "current_trip"
    )

    if not trip:

        return redirect(
            url_for("planner")
        )

    budget_data = trip[
        "budget_data"
    ]

    estimated = budget_data[
        "total"
    ]

    suggestions = []

    optimized_cost = estimated

    if trip["transport"] in [
        "Flight",
        "Cab"
    ]:

        suggestions.append(
            "Choose Bus or Train to reduce transportation cost."
        )

        if trip["transport"] == "Flight":

            optimized_cost -= (

                get_transport_cost(
                    "Flight"
                )

                - get_transport_cost(
                    "Train"
                )

            ) * trip["travelers"]

        else:

            optimized_cost -= (

                get_transport_cost(
                    "Cab"
                )

                - get_transport_cost(
                    "Bus"
                )

            ) * trip["travelers"]

    if trip["accommodation"] == "Hotel":

        suggestions.append(
            "Choose a Hostel or Homestay for a lower stay cost."
        )

        optimized_cost -= (

            get_stay_cost(
                "Hotel"
            )

            - get_stay_cost(
                "Hostel"
            )

        ) * trip["days"] * trip["travelers"]

    if trip["activity_level"] == "High":

        suggestions.append(
            "Choose selected high-value activities instead of "
            "doing every activity."
        )

        optimized_cost -= (

            get_activity_cost(
                "High"
            )

            - get_activity_cost(
                "Medium"
            )

        ) * trip["days"] * trip["travelers"]

    optimized_cost = max(
        optimized_cost,
        0
    )

    trip[
        "optimized_cost"
    ] = optimized_cost

    session[
        "current_trip"
    ] = trip

    return render_template(

        "budget.html",

        trip=trip,

        user=current_user(),

        suggestions=suggestions,

        optimized_cost=optimized_cost

    )


# =========================================================
# SMART MAP
# =========================================================

@app.route("/map")
def map_view():

    trip = session.get(
        "current_trip"
    )

    if not trip:

        return redirect(
            url_for("planner")
        )

    # -----------------------------------------------------
    # REAL DESTINATION LOCATION
    # -----------------------------------------------------

    location = geocode_place(
        trip["destination"]
    )

    # -----------------------------------------------------
    # OPTIMIZED COST
    # -----------------------------------------------------

    optimized_cost = trip.get(

        "optimized_cost",

        trip[
            "budget_data"
        ]["total"]

    )

    # -----------------------------------------------------
    # ROUTE POINTS
    # -----------------------------------------------------

    route_points = []

    # -----------------------------------------------------
    # STARTING LOCATION
    # -----------------------------------------------------

    start_location = trip.get(
        "start_location",
        ""
    )

    start_location_data = None

    if start_location:

        start_location_data = geocode_place(
            start_location
        )

        if start_location_data.get("success"):

            route_points.append({

                "name":
                    start_location,

                "type":
                    "Starting Location",

                "day":
                    0,

                "lat":
                    start_location_data["lat"],

                "lon":
                    start_location_data["lon"]

            })

    # -----------------------------------------------------
    # DESTINATION
    # -----------------------------------------------------

    if location.get("success"):

        route_points.append({

            "name":
                trip["destination"],

            "type":
                "Destination",

            "day":
                0,

            "lat":
                location["lat"],

            "lon":
                location["lon"]

        })

    # -----------------------------------------------------
    # ITINERARY MAP PLACES
    # -----------------------------------------------------

    map_places = []

    for day in trip.get(
        "itinerary",
        []
    ):

        day_number = day.get(
            "day"
        )

        for place in day.get(
            "places",
            []
        ):

            latitude = place.get(
                "lat"
            )

            longitude = place.get(
                "lon"
            )

            map_place = {

                "name":
                    place.get(
                        "place"
                    ),

                "category":
                    place.get(
                        "category"
                    ),

                "cost":
                    place.get(
                        "cost",
                        0
                    ),

                "duration":
                    place.get(
                        "duration",
                        0
                    ),

                "day":
                    day_number,

                "time":
                    place.get(
                        "time",
                        ""
                    ),

                "lat":
                    latitude,

                "lon":
                    longitude

            }

            map_places.append(
                map_place
            )

            if (

                latitude is not None

                and longitude is not None

            ):

                route_points.append({

                    "name":
                        place.get(
                            "place"
                        ),

                    "type":
                        place.get(
                            "category",
                            "Place"
                        ),

                    "day":
                        day_number,

                    "lat":
                        latitude,

                    "lon":
                        longitude

                })

    # -----------------------------------------------------
    # LIVE NEARBY PLACES FOR MAP
    # -----------------------------------------------------

    nearby_places = []

    if location.get("success"):

        nearby_result = get_nearby_places(

            location.get("lat"),

            location.get("lon")

        )

        if nearby_result.get("success"):

            nearby_places = nearby_result.get(

                "places",

                []

            )

    # -----------------------------------------------------
    # ACTUAL ROAD ROUTE
    # -----------------------------------------------------

    road_route = get_road_route(
        route_points
    )

    # -----------------------------------------------------
    # RETURN MAP
    # -----------------------------------------------------

    return render_template(

        "map.html",

        trip=trip,

        user=current_user(),

        location=location,

        optimized_cost=optimized_cost,

        map_places=map_places,

        route_points=route_points,

        nearby_places=nearby_places,

        road_route=road_route

    )




# =========================================================
# STAYS
# =========================================================

@app.route("/stays")
def stays():

    trip = session.get(
        "current_trip"
    )

    if not trip:

        return redirect(
            url_for("planner")
        )

    destination_data = get_destination(
        trip["destination"]
    )

    location = geocode_place(
        trip["destination"]
    )

    if destination_data:

        latitude = destination_data.get(
            "lat"
        )

        longitude = destination_data.get(
            "lon"
        )

    elif location.get("success"):

        latitude = location.get(
            "lat"
        )

        longitude = location.get(
            "lon"
        )

    else:

        latitude = None

        longitude = None

    live_result = get_stays(

        latitude,

        longitude

    )

    if (

        live_result["success"]

        and live_result["stays"]

    ):

        stays_data = live_result[
            "stays"
        ]

        demo_mode = False

    else:

        stays_data = [

            {

                "name":
                    "Budget Stay Option",

                "type":
                    "Hostel",

                "price":
                    450,

                "rating":
                    None,

                "tag":
                    "Demo Data"

            },

            {

                "name":
                    "Comfort Stay Option",

                "type":
                    "Homestay",

                "price":
                    700,

                "rating":
                    None,

                "tag":
                    "Demo Data"

            },

            {

                "name":
                    "Premium Stay Option",

                "type":
                    "Hotel",

                "price":
                    900,

                "rating":
                    None,

                "tag":
                    "Demo Data"

            }

        ]

        demo_mode = True

    return render_template(

        "stays.html",

        trip=trip,

        stays=stays_data,

        user=current_user(),

        demo_mode=demo_mode

    )


# =========================================================
# FOOD
# =========================================================

@app.route("/food")
def food():

    trip = session.get(
        "current_trip"
    )

    if not trip:

        return redirect(
            url_for("planner")
        )

    destination_data = get_destination(
        trip["destination"]
    )

    location = geocode_place(
        trip["destination"]
    )

    if destination_data:

        latitude = destination_data.get(
            "lat"
        )

        longitude = destination_data.get(
            "lon"
        )

    elif location.get("success"):

        latitude = location.get(
            "lat"
        )

        longitude = location.get(
            "lon"
        )

    else:

        latitude = None

        longitude = None

    live_result = get_food_places(

        latitude,

        longitude

    )

    if (

        live_result["success"]

        and live_result["foods"]

    ):

        food_data = live_result[
            "foods"
        ]

        demo_mode = False

    else:

        food_data = [

            {

                "name":
                    "Local Food Option",

                "type":
                    "Restaurant",

                "price":
                    None,

                "rating":
                    None,

                "tag":
                    "Demo Data"

            },

            {

                "name":
                    "Popular Cafe Option",

                "type":
                    "Cafe",

                "price":
                    None,

                "rating":
                    None,

                "tag":
                    "Demo Data"

            },

            {

                "name":
                    "Local Street Food Option",

                "type":
                    "Fast Food",

                "price":
                    None,

                "rating":
                    None,

                "tag":
                    "Demo Data"

            }

        ]

        demo_mode = True

    return render_template(

        "food.html",

        trip=trip,

        foods=food_data,

        user=current_user(),

        demo_mode=demo_mode

    )


# =========================================================
# NEARBY PLACES
# =========================================================

@app.route("/nearby")
def nearby():

    trip = session.get(
        "current_trip"
    )

    if not trip:

        return redirect(
            url_for("planner")
        )

    destination_data = get_destination(
        trip["destination"]
    )

    location = geocode_place(
        trip["destination"]
    )

    latitude = None

    longitude = None

    if destination_data:

        latitude = destination_data.get(
            "lat"
        )

        longitude = destination_data.get(
            "lon"
        )

    if (

        latitude is None

        or longitude is None

    ) and location.get("success"):

        latitude = location[
            "lat"
        ]

        longitude = location[
            "lon"
        ]

    nearby_data = get_nearby_places(

        latitude,

        longitude

    )

    if nearby_data.get("success"):

        places = nearby_data.get(

            "places",

            []

        )

        data_source = (
            "Live OpenStreetMap Data"
        )

        demo_data = False

    else:

        places = []

        data_source = "Demo Data"

        demo_data = True

    return render_template(

        "nearby.html",

        trip=trip,

        user=current_user(),

        places=places,

        data_source=data_source,

        demo_data=demo_data,

        location=location

    )


# =========================================================
# GUIDES
# =========================================================

@app.route("/guides")
def guides():

    trip = session.get("current_trip")

    if not trip:
        return redirect(
            url_for("planner")
        )

    destination = trip.get(
        "destination",
        ""
    )

    guide_data = get_local_guides(
        destination
    )

    if guide_data.get("success"):

        guides_list = guide_data.get(
            "guides",
            []
        )

        data_source = guide_data.get(
            "data_source",
            "Demo Data"
        )

        demo_data = (
            data_source == "Demo Data"
        )

    else:

        guides_list = []

        data_source = "Demo Data"

        demo_data = True

    return render_template(
        "guides.html",
        trip=trip,
        guides=guides_list,
        user=current_user(),
        data_source=data_source,
        demo_data=demo_data
    )

# =========================================================
# REQUEST A GUIDE
# =========================================================

@app.route(
    "/request-guide",
    methods=["GET", "POST"]
)
def request_guide():

    trip = session.get("current_trip")

    if not trip:
        return redirect(
            url_for("planner")
        )

    user = current_user()

    # -----------------------------------------------------
    # GET — SHOW REQUEST FORM
    # -----------------------------------------------------

    if request.method == "GET":

        guide_name = request.args.get(
            "guide",
            "Local Culture Guide"
        ).strip()

        return render_template(
            "guide_request.html",
            trip=trip,
            user=user,
            guide_name=guide_name
        )

    # -----------------------------------------------------
    # POST — SAVE GUIDE REQUEST
    # -----------------------------------------------------

    guide_name = request.form.get(
        "guide_name",
        ""
    ).strip()

    traveler_name = request.form.get(
        "traveler_name",
        ""
    ).strip()

    traveler_email = request.form.get(
        "traveler_email",
        ""
    ).strip()

    traveler_mobile = request.form.get(
        "traveler_mobile",
        ""
    ).strip()

    preferred_date = request.form.get(
        "preferred_date",
        ""
    ).strip()

    preferred_time = request.form.get(
        "preferred_time",
        ""
    ).strip()

    language = request.form.get(
        "language",
        ""
    ).strip()

    travelers_raw = request.form.get(
        "travelers",
        "1"
    ).strip()

    message = request.form.get(
        "message",
        ""
    ).strip()

    # -----------------------------------------------------
    # BASIC VALIDATION
    # -----------------------------------------------------

    if not guide_name:
        flash(
            "Please select a guide.",
            "danger"
        )
        return redirect(
            url_for("guides")
        )

    if not traveler_name or not traveler_email:
        flash(
            "Please enter your name and email.",
            "danger"
        )
        return redirect(
            url_for(
                "request_guide",
                guide=guide_name
            )
        )

    if not preferred_date:
        flash(
            "Please select a preferred date.",
            "danger"
        )
        return redirect(
            url_for(
                "request_guide",
                guide=guide_name
            )
        )

    if not preferred_time:
        flash(
            "Please select a preferred time.",
            "danger"
        )
        return redirect(
            url_for(
                "request_guide",
                guide=guide_name
            )
        )

    if not language:
        flash(
            "Please select a preferred language.",
            "danger"
        )
        return redirect(
            url_for(
                "request_guide",
                guide=guide_name
            )
        )

    try:
        travelers = int(travelers_raw)

        if travelers < 1 or travelers > 50:
            raise ValueError

    except ValueError:

        flash(
            "Number of travelers must be between 1 and 50.",
            "danger"
        )

        return redirect(
            url_for(
                "request_guide",
                guide=guide_name
            )
        )

    # -----------------------------------------------------
    # CREATE GUIDE REQUEST
    # -----------------------------------------------------

    guide_request = GuideRequest(

        user_id=user.id if user else None,

        guide_name=guide_name,

        destination=trip["destination"],

        traveler_name=traveler_name,

        traveler_email=traveler_email,

        traveler_mobile=traveler_mobile,

        preferred_date=preferred_date,

        preferred_time=preferred_time,

        language=language,

        travelers=travelers,

        message=message,

        status="Pending"

    )

    db.session.add(
        guide_request
    )

    db.session.commit()

    # -----------------------------------------------------
    # SUCCESS
    # -----------------------------------------------------

    flash(
        "Guide request submitted successfully!",
        "success"
    )

    return redirect(
        url_for(
            "guide_request_success",
            request_id=guide_request.id
        )
    )


# =========================================================
# GUIDE REQUEST SUCCESS
# =========================================================

@app.route(
    "/guide-request-success/<int:request_id>"
)
def guide_request_success(request_id):

    trip = session.get("current_trip")

    if not trip:
        return redirect(
            url_for("planner")
        )

    guide_request = GuideRequest.query.filter_by(
        id=request_id
    ).first()

    if not guide_request:
        flash(
            "Guide request not found.",
            "danger"
        )

        return redirect(
            url_for("guides")
        )

    return render_template(
        "guide_request_success.html",
        trip=trip,
        guide_request=guide_request,
        user=current_user()
    )

# =========================================================
# GUIDE REQUEST MANAGEMENT
# =========================================================

@app.route("/guide-requests")
def guide_requests():

    # Login required
    if not login_required():

        flash(
            "Please login to view guide requests.",
            "warning"
        )

        return redirect(
            url_for("login")
        )

    user = current_user()

    requests_list = GuideRequest.query.order_by(
        GuideRequest.created_at.desc()
    ).all()

    return render_template(
        "guide_requests.html",
        requests_list=requests_list,
        user=user
    )


# =========================================================
# UPDATE GUIDE REQUEST STATUS
# =========================================================

@app.route(
    "/guide-request-status/<int:request_id>",
    methods=["POST"]
)
def update_guide_request_status(request_id):
    if not login_required():
        flash(
            "Please login to update guide requests.",
            "warning"
        )

        return redirect(
            url_for("login")
        )

    guide_request = GuideRequest.query.filter_by(
        id=request_id
    ).first()

    if not guide_request:

        flash(
            "Guide request not found.",
            "danger"
        )

        return redirect(
            url_for("guide_requests")
        )

    status = request.form.get(
        "status",
        "Pending"
    ).strip()

    allowed_statuses = [
        "Pending",
        "Confirmed",
        "Rejected"
    ]

    if status not in allowed_statuses:

        flash(
            "Invalid request status.",
            "danger"
        )

        return redirect(
            url_for("guide_requests")
        )

    guide_request.status = status

    db.session.commit()

    flash(
        f"Guide request #{guide_request.id} "
        f"updated to {status}.",
        "success"
    )

    return redirect(
        url_for("guide_requests")
    )

# =========================================================
# REVIEWS
# =========================================================

@app.route(
    "/add-review",
    methods=["POST"]
)
def add_review():

    if not login_required():

        flash(
            "Please login to submit a review.",
            "warning"
        )

        return redirect(
            url_for("login")
        )

    user = current_user()

    destination = request.form.get(
        "destination",
        ""
    ).strip()

    item_name = request.form.get(
        "item_name",
        ""
    ).strip()

    category = request.form.get(
        "category",
        ""
    ).strip()

    rating_raw = request.form.get(
        "rating",
        ""
    ).strip()

    review_text = request.form.get(
        "review_text",
        ""
    ).strip()

    # -----------------------------------------------------
    # BASIC VALIDATION
    # -----------------------------------------------------

    if not destination:

        flash(
            "Destination is required.",
            "danger"
        )

        return redirect(
            request.referrer or url_for("home")
        )

    if not item_name:

        flash(
            "Please select a place, stay, food option or guide.",
            "danger"
        )

        return redirect(
            request.referrer or url_for("home")
        )

    if category not in [
        "Place",
        "Stay",
        "Food",
        "Guide"
    ]:

        flash(
            "Invalid review category.",
            "danger"
        )

        return redirect(
            request.referrer or url_for("home")
        )

    try:

        rating = int(rating_raw)

    except (TypeError, ValueError):

        flash(
            "Rating must be between 1 and 5.",
            "danger"
        )

        return redirect(
            request.referrer or url_for("home")
        )

    if rating < 1 or rating > 5:

        flash(
            "Rating must be between 1 and 5.",
            "danger"
        )

        return redirect(
            request.referrer or url_for("home")
        )

    if not review_text:

        flash(
            "Please write a review.",
            "danger"
        )

        return redirect(
            request.referrer or url_for("home")
        )

    if len(review_text) > 1000:

        flash(
            "Review must be 1000 characters or less.",
            "danger"
        )

        return redirect(
            request.referrer or url_for("home")
        )

    # -----------------------------------------------------
    # CREATE REVIEW
    # -----------------------------------------------------

    new_review = Review(

        user_id=user.id,

        destination=destination,

        item_name=item_name,

        category=category,

        rating=rating,

        review_text=review_text

    )

    db.session.add(
        new_review
    )

    db.session.commit()

    flash(
        "Your review was submitted successfully!",
        "success"
    )

    return redirect(
        request.referrer or url_for("home")
    )


# =========================================================
# SAVE TRIP
# =========================================================

@app.route(
    "/save-trip",
    methods=["POST"]
)
def save_trip():

    if not login_required():

        flash(

            "Please login to save your trip.",

            "warning"

        )

        return redirect(
            url_for("login")
        )

    trip_data = session.get(
        "current_trip"
    )

    if not trip_data:

        flash(

            "No trip available to save.",

            "danger"

        )

        return redirect(
            url_for("planner")
        )

    user = current_user()

    saved_trip = Trip(

        user_id=user.id,

        title=(

            f"{trip_data['days']}-Day "

            f"{trip_data['destination']} Trip"

        ),

        destination=
            trip_data["destination"],

        start_location=
            trip_data["start_location"],

        days=
            trip_data["days"],

        travelers=
            trip_data["travelers"],

        budget=
            trip_data["budget"],

        estimated_cost=
            trip_data["budget_data"]["total"],

        itinerary_json=
            json.dumps(trip_data)

    )

    db.session.add(
        saved_trip
    )

    db.session.commit()

    flash(

        "Trip saved successfully!",

        "success"

    )

    return redirect(
        url_for("trips")
    )


# =========================================================
# MY TRIPS
# =========================================================

@app.route("/trips")
def trips():

    if not login_required():

        return redirect(
            url_for("login")
        )

    user = current_user()

    saved_trips = Trip.query.filter_by(

        user_id=user.id

    ).order_by(

        Trip.created_at.desc()

    ).all()

    return render_template(

        "trips.html",

        trips=saved_trips,

        user=user

    )


# =========================================================
# VIEW SAVED TRIP
# =========================================================

@app.route(
    "/trip/<int:trip_id>"
)
def view_trip(trip_id):

    user = current_user()

    if not user:

        flash(

            "Please login to view your saved trips.",

            "error"

        )

        return redirect(
            url_for("login")
        )

    trip_record = Trip.query.filter_by(

        id=trip_id,

        user_id=user.id

    ).first()

    if not trip_record:

        flash(

            "Trip not found.",

            "error"

        )

        return redirect(
            url_for("trips")
        )

    try:

        trip_data = json.loads(

            trip_record.itinerary_json

        )

    except (

        TypeError,

        ValueError,

        json.JSONDecodeError

    ):

        flash(

            "Unable to load this saved trip.",

            "error"

        )

        return redirect(
            url_for("trips")
        )

    weather = get_weather(

        trip_record.destination

    )

    location = geocode_place(

        trip_record.destination

    )

    return render_template(

        "result.html",

        trip=trip_data,

        user=user,

        weather=weather,

        location=location,

        saved=True

    )

# =========================================================
# EDIT SAVED TRIP — 14.5
# =========================================================

@app.route(
    "/edit-trip/<int:trip_id>",
    methods=["GET", "POST"]
)
def edit_trip(trip_id):

    # -----------------------------------------------------
    # LOGIN CHECK
    # -----------------------------------------------------

    if not login_required():

        flash(
            "Please login to edit your saved trips.",
            "warning"
        )

        return redirect(
            url_for("login")
        )

    user = current_user()

    # -----------------------------------------------------
    # GET SAVED TRIP
    # -----------------------------------------------------

    trip_record = Trip.query.filter_by(

        id=trip_id,

        user_id=user.id

    ).first()

    if not trip_record:

        flash(
            "Trip not found.",
            "danger"
        )

        return redirect(
            url_for("trips")
        )

    # -----------------------------------------------------
    # LOAD ORIGINAL TRIP DATA
    # -----------------------------------------------------

    try:

        trip_data = json.loads(
            trip_record.itinerary_json
        )

    except (
        TypeError,
        ValueError,
        json.JSONDecodeError
    ):

        flash(
            "Unable to load this saved trip.",
            "danger"
        )

        return redirect(
            url_for("trips")
        )

    # -----------------------------------------------------
    # GET — SHOW EDIT FORM
    # -----------------------------------------------------

    if request.method == "GET":

        return render_template(

            "edit_trip.html",

            trip=trip_data,

            trip_record=trip_record,

            user=user

        )

    # -----------------------------------------------------
    # POST — UPDATE TRIP
    # -----------------------------------------------------

    try:

        start_location = request.form.get(
            "start_location",
            ""
        ).strip()

        destination = request.form.get(
            "destination",
            ""
        ).strip()

        days = int(
            request.form.get(
                "days",
                1
            )
        )

        travelers = int(
            request.form.get(
                "travelers",
                1
            )
        )

        budget = float(
            request.form.get(
                "budget",
                0
            )
        )

    except (
        TypeError,
        ValueError
    ):

        flash(
            "Please enter valid trip details.",
            "danger"
        )

        return redirect(
            url_for(
                "edit_trip",
                trip_id=trip_id
            )
        )

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    if not destination:

        flash(
            "Destination is required.",
            "danger"
        )

        return redirect(
            url_for(
                "edit_trip",
                trip_id=trip_id
            )
        )

    if days < 1 or days > 30:

        flash(
            "Trip duration must be between 1 and 30 days.",
            "danger"
        )

        return redirect(
            url_for(
                "edit_trip",
                trip_id=trip_id
            )
        )

    if travelers < 1 or travelers > 50:

        flash(
            "Travelers must be between 1 and 50.",
            "danger"
        )

        return redirect(
            url_for(
                "edit_trip",
                trip_id=trip_id
            )
        )

    if budget < 0:

        flash(
            "Budget cannot be negative.",
            "danger"
        )

        return redirect(
            url_for(
                "edit_trip",
                trip_id=trip_id
            )
        )

    # -----------------------------------------------------
    # OTHER PREFERENCES
    # -----------------------------------------------------

    purpose = request.form.get(
        "purpose",
        trip_data.get(
            "purpose",
            "Relaxation"
        )
    )

    interests_raw = request.form.get(
        "interests",
        ",".join(
            trip_data.get(
                "interests",
                []
            )
        )
    )

    interests = [

        item.strip()

        for item in interests_raw.split(",")

        if item.strip()

    ]

    transport = request.form.get(
        "transport",
        trip_data.get(
            "transport",
            "Bus"
        )
    )

    accommodation = request.form.get(
        "accommodation",
        trip_data.get(
            "accommodation",
            "Hostel"
        )
    )

    food = request.form.get(
        "food",
        trip_data.get(
            "food",
            "Both"
        )
    )

    activity_level = request.form.get(
        "activity_level",
        trip_data.get(
            "activity_level",
            "Medium"
        )
    )

    language = request.form.get(
        "language",
        trip_data.get(
            "language",
            "English"
        )
    )

    accessibility = request.form.get(
        "accessibility",
        trip_data.get(
            "accessibility",
            "None"
        )
    )

    special_preference = request.form.get(
        "special_preference",
        trip_data.get(
            "special_preference",
            ""
        )
    ).strip()

    # -----------------------------------------------------
    # FIND DESTINATION
    # -----------------------------------------------------

    destination_data = get_destination(
        destination
    )

    # -----------------------------------------------------
    # UNKNOWN DESTINATION
    # -----------------------------------------------------

    if destination_data is None:

        destination_data = {

            "name":
                destination.title(),

            "state":
                "India",

            "lat":
                20.5937,

            "lon":
                78.9629,

            "description":
                "Destination information is currently "
                "shown as Demo Data.",

            "places": [

                {
                    "name":
                        f"{destination.title()} City Center",

                    "category":
                        "Culture",

                    "cost":
                        0,

                    "duration":
                        90,

                    "lat":
                        20.5937,

                    "lon":
                        78.9629
                },

                {
                    "name":
                        f"{destination.title()} Local Market",

                    "category":
                        "Food",

                    "cost":
                        100,

                    "duration":
                        90,

                    "lat":
                        20.6000,

                    "lon":
                        78.9700
                },

                {
                    "name":
                        f"{destination.title()} Scenic Spot",

                    "category":
                        "Nature",

                    "cost":
                        50,

                    "duration":
                        120,

                    "lat":
                        20.5850,

                    "lon":
                        78.9500
                }

            ],

            "foods": [

                "Local cuisine",
                "Popular street food",
                "Regional meals"

            ],

            "tips": [

                "Demo Data — connect a destination API "
                "for live information."

            ]

        }

        demo_data = True

    else:

        demo_data = False

    # -----------------------------------------------------
    # RECALCULATE BUDGET
    # -----------------------------------------------------

    budget_data = calculate_budget(

        days,

        travelers,

        transport,

        accommodation,

        activity_level

    )

    # -----------------------------------------------------
    # RECREATE ITINERARY
    # -----------------------------------------------------

    itinerary = create_itinerary(

        destination_data,

        days,

        travelers,

        interests,

        activity_level

    )

    # -----------------------------------------------------
    # UPDATE TRIP DATA
    # -----------------------------------------------------

    updated_trip = {

        "start_location":
            start_location,

        "destination":
            destination_data["name"],

        "state":
            destination_data["state"],

        "days":
            days,

        "travelers":
            travelers,

        "budget":
            budget,

        "purpose":
            purpose,

        "interests":
            interests,

        "transport":
            transport,

        "accommodation":
            accommodation,

        "food":
            food,

        "activity_level":
            activity_level,

        "language":
            language,

        "accessibility":
            accessibility,

        "special_preference":
            special_preference,

        "description":
            destination_data["description"],

        "itinerary":
            itinerary,

        "budget_data":
            budget_data,

        "foods":
            destination_data["foods"],

        "tips":
            destination_data["tips"],

        "places":
            destination_data["places"],

        "demo_data":
            demo_data

    }

    # -----------------------------------------------------
    # UPDATE DATABASE
    # -----------------------------------------------------

    trip_record.title = (

        f"{days}-Day "

        f"{destination_data['name']} Trip"

    )

    trip_record.destination = (
        destination_data["name"]
    )

    trip_record.start_location = (
        start_location
    )

    trip_record.days = days

    trip_record.travelers = travelers

    trip_record.budget = budget

    trip_record.estimated_cost = (
        budget_data["total"]
    )

    trip_record.itinerary_json = json.dumps(
        updated_trip
    )

    db.session.commit()

    # -----------------------------------------------------
    # UPDATE CURRENT SESSION TRIP
    # -----------------------------------------------------

    session[
        "current_trip"
    ] = updated_trip

    # -----------------------------------------------------
    # SUCCESS
    # -----------------------------------------------------

    flash(
        "Trip updated successfully!",
        "success"
    )

    return redirect(
        url_for(
            "view_trip",
            trip_id=trip_id
        )
    )


# =========================================================
# DELETE TRIP
# =========================================================

@app.route(

    "/delete-trip/<int:trip_id>",

    methods=["POST"]

)
def delete_trip(trip_id):

    if not login_required():

        return redirect(
            url_for("login")
        )

    user = current_user()

    trip = Trip.query.filter_by(

        id=trip_id,

        user_id=user.id

    ).first_or_404()

    db.session.delete(
        trip
    )

    db.session.commit()

    flash(

        "Trip deleted.",

        "success"

    )

    return redirect(
        url_for("trips")
    )


# =========================================================
# LOGIN
# =========================================================

@app.route(

    "/login",

    methods=["GET", "POST"]

)
def login():

    if request.method == "POST":

        identity = request.form.get(

            "identity",

            ""

        ).strip()

        password = request.form.get(

            "password",

            ""

        )

        user = User.query.filter(

            (User.username == identity)

            |

            (User.email == identity)

        ).first()

        if user and user.check_password(
            password
        ):

            session[
                "username"
            ] = user.username

            flash(

                "Welcome back to TravelGenie!",

                "success"

            )

            return redirect(
                url_for("dashboard")
            )

        flash(

            "Invalid username/email or password.",

            "danger"

        )

    return render_template(

        "login.html",

        user=current_user()

    )


# =========================================================
# REGISTER
# =========================================================

@app.route(

    "/register",

    methods=["GET", "POST"]

)
def register():

    if request.method == "POST":

        full_name = request.form.get(

            "full_name",

            ""

        ).strip()

        username = request.form.get(

            "username",

            ""

        ).strip()

        email = request.form.get(

            "email",

            ""

        ).strip().lower()

        mobile = request.form.get(

            "mobile",

            ""

        ).strip()

        password = request.form.get(

            "password",

            ""

        )

        confirm_password = request.form.get(

            "confirm_password",

            ""

        )

        if not all([

            full_name,

            username,

            email,

            password,

            confirm_password

        ]):

            flash(

                "Please fill all required fields.",

                "danger"

            )

            return redirect(
                url_for("register")
            )

        if password != confirm_password:

            flash(

                "Passwords do not match.",

                "danger"

            )

            return redirect(
                url_for("register")
            )

        if User.query.filter_by(

            username=username

        ).first():

            flash(

                "Username already exists.",

                "danger"

            )

            return redirect(
                url_for("register")
            )

        if User.query.filter_by(

            email=email

        ).first():

            flash(

                "Email already registered.",

                "danger"

            )

            return redirect(
                url_for("register")
            )

        new_user = User(

            full_name=full_name,

            username=username,

            email=email,

            mobile=mobile

        )

        new_user.set_password(
            password
        )

        db.session.add(
            new_user
        )

        db.session.commit()

        flash(

            "Account created successfully!",

            "success"

        )

        return redirect(
            url_for("login")
        )

    return render_template(

        "register.html",

        user=current_user()

    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if not login_required():

        return redirect(
            url_for("login")
        )

    user = current_user()

    trips = Trip.query.filter_by(

        user_id=user.id

    ).order_by(

        Trip.created_at.desc()

    ).all()

    total_trips = len(
        trips
    )

    total_budget = sum(

        trip.budget

        for trip in trips

    )

    total_estimated = sum(

        trip.estimated_cost

        for trip in trips

    )

    money_difference = max(

        total_estimated
        - total_budget,

        0

    )

    return render_template(

        "dashboard.html",

        user=user,

        trips=trips,

        total_trips=total_trips,

        total_budget=total_budget,

        total_estimated=total_estimated,

        money_difference=money_difference

    )


# =========================================================
# PROFILE
# =========================================================

@app.route(

    "/profile",

    methods=["GET", "POST"]

)
def profile():

    if not login_required():

        return redirect(
            url_for("login")
        )

    user = current_user()

    if request.method == "POST":

        full_name = request.form.get(

            "full_name",

            ""

        ).strip()

        mobile = request.form.get(

            "mobile",

            ""

        ).strip()

        if full_name:

            user.full_name = full_name

        user.mobile = mobile

        db.session.commit()

        flash(

            "Profile updated successfully.",

            "success"

        )

        return redirect(
            url_for("profile")
        )

    return render_template(

        "profile.html",

        user=user

    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(

        "You have been logged out.",

        "success"

    )

    return redirect(
        url_for("home")
    )


# =========================================================
# ABOUT
# =========================================================

@app.route("/about")
def about():

    return render_template(

        "about.html",

        user=current_user()

    )

# =========================================================
# REVIEWS API — 13.3
# =========================================================

@app.route("/api/reviews")
def api_reviews():

    destination = request.args.get(
        "destination",
        ""
    ).strip()

    item_name = request.args.get(
        "item_name",
        ""
    ).strip()

    category = request.args.get(
        "category",
        ""
    ).strip()

    query = Review.query

    if destination:
        query = query.filter_by(
            destination=destination
        )

    if item_name:
        query = query.filter_by(
            item_name=item_name
        )

    if category:
        query = query.filter_by(
            category=category
        )

    reviews = query.order_by(
        Review.created_at.desc()
    ).all()

    return jsonify({

        "success": True,

        "total_reviews":
            len(reviews),

        "reviews": [

            {
                "id":
                    review.id,

                "reviewer":
                    review.user.full_name
                    if review.user
                    else "Anonymous",

                "destination":
                    review.destination,

                "item_name":
                    review.item_name,

                "category":
                    review.category,

                "rating":
                    review.rating,

                "review_text":
                    review.review_text,

                "created_at":
                    review.created_at.strftime(
                        "%d %b %Y"
                    )
            }

            for review in reviews

        ]

    })


# =========================================================
# REVIEW STATISTICS API — 13.4
# =========================================================

@app.route("/api/review-stats")
def api_review_stats():

    destination = request.args.get(
        "destination",
        ""
    ).strip()

    item_name = request.args.get(
        "item_name",
        ""
    ).strip()

    category = request.args.get(
        "category",
        ""
    ).strip()

    query = Review.query

    if destination:
        query = query.filter_by(
            destination=destination
        )

    if item_name:
        query = query.filter_by(
            item_name=item_name
        )

    if category:
        query = query.filter_by(
            category=category
        )

    reviews = query.all()

    total_reviews = len(
        reviews
    )

    if total_reviews > 0:

        average_rating = round(
            sum(
                review.rating
                for review in reviews
            ) / total_reviews,
            1
        )

    else:

        average_rating = 0

    rating_breakdown = {
        "5": 0,
        "4": 0,
        "3": 0,
        "2": 0,
        "1": 0
    }

    for review in reviews:

        rating_breakdown[
            str(review.rating)
        ] += 1

    return jsonify({

        "success": True,

        "total_reviews":
            total_reviews,

        "average_rating":
            average_rating,

        "rating_breakdown":
            rating_breakdown

    })


# =========================================================
# REVIEWS PAGE — 13.5
# =========================================================

@app.route("/reviews")
def reviews_page():

    trip = session.get(
        "current_trip"
    )

    return render_template(
        "reviews.html",
        trip=trip,
        user=current_user(),
        destinations=list(
            DESTINATIONS.values()
        )
    )


# =========================================================
# DESTINATION SEARCH API
# =========================================================

@app.route("/api/destinations")
def destination_api():

    query = request.args.get(

        "q",

        ""

    ).strip().lower()

    results = []

    for key, data in DESTINATIONS.items():

        if (

            not query

            or query in key

            or query in data[
                "state"
            ].lower()

        ):

            results.append({

                "name":
                    data["name"],

                "state":
                    data["state"],

                "lat":
                    data["lat"],

                "lon":
                    data["lon"]

            })

    return jsonify(
        results
    )


# =========================================================
# CREATE DATABASE
# =========================================================

with app.app_context():

    db.create_all()


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(

        debug=True,

        host="127.0.0.1",

        port=5000

    )