import os
from datetime import datetime
from flask import Flask, redirect, url_for, session, jsonify, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_dance.contrib.google import make_google_blueprint, google
from functools import wraps

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersekrit")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rides.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Google OAuth setup using Flask-Dance
google_bp = make_google_blueprint(
    client_id=os.environ.get("GOOGLE_OAUTH_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET"),
    scope=["profile", "email"],
    redirect_url="/login/google/authorized"
)
app.register_blueprint(google_bp, url_prefix="/login")

# ---------------------
# Database Model
# ---------------------
class Ride(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(120), nullable=False)
    departure = db.Column(db.String(120), nullable=False)   # "Leaving from"
    destination = db.Column(db.String(120), nullable=False)   # "Going to"
    travel_date = db.Column(db.Date, nullable=False)          # Date input (DD/MM/YYYY)
    seats_available = db.Column(db.Integer, nullable=False)
    price_per_seat = db.Column(db.Float, nullable=False)
    additional_info = db.Column(db.String(500))
    gender = db.Column(db.String(10))  # Optional field for gender filter

    def to_dict(self):
        return {
            "id": self.id,
            "user_email": self.user_email,
            "departure": self.departure,
            "destination": self.destination,
            "travel_date": self.travel_date.strftime("%d/%m/%Y"),
            "seats_available": self.seats_available,
            "price_per_seat": self.price_per_seat,
            "additional_info": self.additional_info,
            "gender": self.gender
        }

@app.before_first_request
def create_tables():
    db.create_all()

# ---------------------
# Helper Functions & Decorators
# ---------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not google.authorized or "google_oauth_token" not in session:
            return redirect(url_for("google.login"))
        if "user_email" not in session:
            return redirect(url_for("google.login"))
        return f(*args, **kwargs)
    return decorated_function

# ---------------------
# Routes for OAuth and Serving Front End
# ---------------------
@app.route("/")
def index():
    return send_from_directory(app.static_folder, 'Index.html')

@app.route("/login/google/authorized")
def google_authorized():
    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        return redirect(url_for("google.login"))
    user_info = resp.json()
    user_email = user_info.get("email")
    college_domain = "yourcollege.edu"  # Replace with your actual college domain
    if not user_email.endswith("@" + college_domain):
        return "Access denied: You must log in with your college email.", 403
    session["user_email"] = user_email
    return redirect(url_for("index"))

# ---------------------
# API Endpoints
# ---------------------

# Publish a ride endpoint
@app.route('/api/rides', methods=['POST'])
@login_required
def publish_ride():
    data = request.get_json()
    try:
        departure = data['departure']          # "Leaving from"
        destination = data['destination']      # "Going to"
        # Expect travel_date in format "DD/MM/YYYY"
        travel_date_str = data['travel_date']
        travel_date = datetime.strptime(travel_date_str, "%d/%m/%Y").date()
        seats_available = int(data['seats_available'])
        price_per_seat = float(data['price_per_seat'])
        additional_info = data.get('additional_info', '')
        gender = data.get('gender')  # Optional field
    except (KeyError, ValueError):
        return jsonify({"error": "Invalid input. Please check that all required fields are provided and formatted correctly."}), 400

    new_ride = Ride(
        user_email=session["user_email"],
        departure=departure,
        destination=destination,
        travel_date=travel_date,
        seats_available=seats_available,
        price_per_seat=price_per_seat,
        additional_info=additional_info,
        gender=gender
    )
    db.session.add(new_ride)
    db.session.commit()
    return jsonify({"message": "Ride published successfully!", "ride": new_ride.to_dict()}), 201

# Retrieve rides with optional filtering (for rides.html and search forms)
@app.route('/api/rides', methods=['GET'])
def get_rides():
    departure = request.args.get('departure')
    destination = request.args.get('destination')
    travel_date_str = request.args.get('travel_date')  # Expected format: DD/MM/YYYY
    gender = request.args.get('gender')

    query = Ride.query
    if departure:
        query = query.filter(Ride.departure.ilike(f'%{departure}%'))
    if destination:
        query = query.filter(Ride.destination.ilike(f'%{destination}%'))
    if travel_date_str:
        try:
            travel_date = datetime.strptime(travel_date_str, "%d/%m/%Y").date()
            query = query.filter(Ride.travel_date == travel_date)
        except ValueError:
            return jsonify({"error": "Invalid date format. Expected DD/MM/YYYY."}), 400
    if gender:
        query = query.filter(Ride.gender == gender)

    rides = query.all()
    return jsonify([ride.to_dict() for ride in rides]), 200

# Matching endpoint: Given a ride ID (from the current user), return rides on the same travel date with a similar destination.
@app.route('/api/matches', methods=['GET'])
@login_required
def get_matches():
    ride_id = request.args.get('ride_id')
    if not ride_id:
        return jsonify({"error": "ride_id query parameter is required"}), 400
    try:
        user_ride = Ride.query.filter_by(id=int(ride_id), user_email=session["user_email"]).first()
        if not user_ride:
            return jsonify({"error": "Ride not found or not owned by the current user."}), 404
    except ValueError:
        return jsonify({"error": "Invalid ride_id parameter."}), 400

    candidates = Ride.query.filter(
        Ride.id != user_ride.id,
        Ride.travel_date == user_ride.travel_date,
        Ride.destination.ilike(f'%{user_ride.destination}%')
    ).all()

    matches = []
    for candidate in candidates:
        # Optional gender filtering if needed
        if user_ride.gender and candidate.gender and user_ride.gender != candidate.gender:
            continue
        matches.append(candidate.to_dict())

    return jsonify({"matches": matches}), 200

# ---------------------
# Static Files Routing
# ---------------------
@app.route('/<path:path>')
def static_proxy(path):
    return send_from_directory(app.static_folder, path)

# ---------------------
# Main Entrypoint
# ---------------------
if __name__ == '__main__':
    app.run(debug=True)
