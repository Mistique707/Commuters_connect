# Commuter Connect

**Commuter Connect** is a web-based carpooling platform designed to help college commuters find and share rides easily. By connecting drivers with empty seats to passengers heading the same way, the platform promotes sustainable travel, reduces commuting costs, and fosters a sense of community.


## 🚀 Features

* **Google OAuth Integration:** Secure login using Google accounts, exclusively restricted to verified college email domains (e.g., `@yourcollege.edu`).
* **Publish a Ride:** Drivers can easily post their travel plans, specifying departure location, destination, date, available seats, and price per seat.
* **Search & Match:** Passengers can search for available rides using a clean, intuitive interface based on their desired route and travel date.
* **Responsive Design:** The UI is optimized for both desktop and mobile web experiences, adapting layout and navigation depending on the device.
* **User Profiles:** Users can view and edit basic profile information such as username, email, and name.
* **Dynamic Ride Management:** Uses a Flask backend with a local SQLite database to seamlessly add, retrieve, and filter ride listings.

## 🛠️ Tech Stack

* **Backend:** Python, Flask
* **Database:** SQLite (managed via Flask-SQLAlchemy)
* **Authentication:** Google OAuth 2.0 (via Flask-Dance)
* **Frontend:** HTML5, CSS3, Vanilla JavaScript
* **Icons & Fonts:** Google Material Icons, Google Fonts (Roboto, Teko, Quantico)

## 📁 Project Structure

```text
Commuters_connect/
│
├── app.py                  # Main Flask application and API routes
├── dynamic_updates.py      # Alternative Flask routing with template rendering
├── instance/
│   └── rides.db            # SQLite database file
├── static/                 # Static assets (CSS, JS, Images, HTML components)
│   ├── Connect.png         # Project Logo
│   ├── Home.css            # Desktop styling
│   ├── Phone-home.css      # Mobile styling
│   ├── Website-load.js     # Device detection script
│   └── ...                 # HTML views (Home, Login, Profile, etc.)
└── templates/              # Jinja2 HTML templates for dynamic rendering
    └── rides.html
