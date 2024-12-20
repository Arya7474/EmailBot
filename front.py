import subprocess
import os
import sys
# from flask import Flask, request , render_template , jsonify
from flask import Flask, request, render_template, redirect, url_for, session, jsonify
import pygame
import signal
import sys
import db
import requests
import re

# app = Flask(__name__)
app = Flask(
    __name__,
    template_folder=os.getenv("TEMPLATE_PATH", ""),
    static_folder=os.getenv("STATIC_PATH", ""),
)

app.secret_key = os.getenv("SECRET_KEY", "default_key")
BACKEND_SCRIPT_PATH = os.getenv("BACKEND_SCRIPT_PATH", "")
PID_FILE = os.getenv("PID_FILE", "")
ERROR_FILE = os.getenv("ERROR_FILE", "")
ALERT_FILE = os.getenv("ALERT_FILE", "") 
ERALT = os.getenv("ERALT", "")
# Testing with zenduty
# ZENDUTY_INTEGRATION_KEY = ""
# ZENDUTY_URL = f"https://events.zenduty.com/api/events/{ZENDUTY_INTEGRATION_KEY}/"

# def send_zenduty_alert():
#     headers = {"Content-Type": "application/json"}
#     payload = {
#         "alert_type": "critical",
#         "message": "Wake up Sir!!",
#         "summary": "System alert triggered",
#         "entity_id": "alert_12345"
#     }
#     try:
#         response = requests.post(ZENDUTY_URL, headers=headers, json=payload)
#         response.raise_for_status()
#         print("Zenduty alert sent successfully!")
#         return {"status": "success", "response": response.json()}
#     except requests.exceptions.RequestException as e:
#         print(f"Error sending Zenduty alert: {e}")
#         return {"status": "error", "error": str(e)}


def error_alert():
    if not pygame.mixer.music.get_busy():
        play_sound(ERALT)  
        print("Error Alert playing!")
    else:
        print("Error Alert already playing!")


def validate_password(password):
    if len(password) <= 6:
        return False, "Password must be longer than 6 characters."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character."
    return True, ""

# creating config_table initially if not present
db.create_config_table()
#creating users table initially if not present
db.create_users_table() 

pygame.mixer.init()
# user authentication

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Validate password
        is_valid, error_message = validate_password(password)
        if not is_valid:
            return render_template("signup.html", error=error_message)

        if db.add_user(username, password):
            return redirect(url_for('login'))
        else:
            return render_template("signup.html", error="Username already exists.")
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if db.verify_user(username, password):
            session["user"] = username
            return redirect(url_for("home"))
        else:
            return render_template("login.html", error="Invalid username or password.")
    return render_template("login.html")

# @app.route("/", methods=["GET"])
# def home():
#     reports = db.fetch_reports(time_filter="daily") 
#     return render_template("index.html", reports=reports)

@app.route("/", methods=["GET"])
def home():
    if "user" not in session:
        return redirect(url_for("login"))  # Redirect to login if not authenticated
    
    username = session["user"]
    reports = db.fetch_reports(time_filter="daily")
    return render_template("index.html", reports=reports,username=username)

@app.route("/submit_config", methods=["POST"])
def submit_config():
    try:
        email_id = request.form.get("email")
        app_password = request.form.get("app-password")
        mail_to_check = request.form.get("manual-entry", "").strip()

        if not mail_to_check or "," not in mail_to_check:
            return render_template("failure.html", message="Invalid input! Please separate values with commas, Minimum 2 values required to start with.")
        # mail_to_check = mail_to_check.split(",")
        mail_to_check = [item.strip() for item in mail_to_check.split(",")]
        success = db.add_config(email_id, app_password, mail_to_check) 

        if success:
            return render_template("success.html", status="Configuration updated successfully!")
        else:
            return render_template("failure.html", message="Failed to update configuration in the database.")
    except Exception as e:
        return render_template("failure.html", message=f"An unexpected error occurred: {str(e)}")

@app.route("/start_backend", methods=["POST"])
def start_backend():
    if os.path.exists(PID_FILE):  
        return {"status": "Backend is already running!"}, 400
    config = db.fetch_config()
    if not config:
        error_message = {"alert": "No configuration found in the database.Please add Config First"}
        requests.post(f"http://localhost:5000/error", json=error_message)
        return {"status": "Configuration missing.Backend not started!"}, 400

    process = subprocess.Popen([sys.executable, BACKEND_SCRIPT_PATH])
    
    with open(PID_FILE, "w") as f:
        f.write(str(process.pid))

    return {"status": "Backend started!"}, 200

@app.route("/stop_backend", methods=["POST"])
def stop_backend():
    if not os.path.exists(PID_FILE): 
        return {"status": "No backend process running!"}, 400

    with open(PID_FILE, "r") as f:
        pid = int(f.read().strip())

    try:
        os.kill(pid, signal.SIGTERM) 
    except ProcessLookupError:
        pass 

    os.remove(PID_FILE)

    # Remove user from session
    session.pop("user", None)

    return {"status": "Backend stopped!"}, 200

def play_sound(file_path):
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play(loops=-1)

@app.route("/stop", methods=["POST"])
def stop_alert():
    if pygame.mixer.music.get_busy():  
        pygame.mixer.music.stop() 
        return {"status": "Alert stopped!"}, 200
    else:
        return {"status": "No alert is playing to stop!"}, 400

@app.route("/trigger", methods=["POST"])
def trigger_alert():
    if not pygame.mixer.music.get_busy():
        play_sound(ALERT_FILE)  
        return {"status": "Alert playing!"}, 200
    else:
        return {"status": "Alert is already playing!"}, 400

def write_error_to_file(message: str) -> None:
    with open(ERROR_FILE, "w") as f:
        f.write(message)

def read_error_from_file() -> str:
    if os.path.exists(ERROR_FILE):
        with open(ERROR_FILE, "r") as f:
            error_message = f.read().strip()
        os.remove(ERROR_FILE)
        return error_message
    return None

@app.route("/error", methods=["POST", "GET"])
def handle_error():
    if request.method == "POST":
        error_message = request.json.get("alert", "IGNORE")
        write_error_to_file(error_message)
        # requests.post("http://localhost:5000/trigger")
        # send_zenduty_alert()
        error_alert()
        return {"status": "Error received"}, 200
    elif request.method == "GET":
        # print("Received GET request for /error")
        error_message = read_error_from_file()
        if error_message:
            return {"status": "Error available", "message": error_message}, 200
        else:
            return {"status": "No error available", "message": None}, 200

@app.route("/get_latest_config", methods=["GET"])
def get_latest_config():
    try:
        config = db.fetch_config()
        if config:
            return jsonify(config), 200  
        else:
            return jsonify({"status": "No configuration found."}), 404  
    except Exception as e:
        return jsonify({"status": str(e)}), 500 


@app.route("/filter_reports", methods=["POST"])
def filter_reports():
    try:
        time_filter = request.json.get("filter", "daily")

        grouped_reports = db.fetch_reports(time_filter)

        return jsonify({"status": "success", "reports": grouped_reports}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)



