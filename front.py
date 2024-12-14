from flask import Flask, request , render_template , jsonify
import pygame
import signal
import sys
import subprocess
import os
import db
# app = Flask(__name__)
app = Flask(
    __name__,
    template_folder="/Users/scorvicsdomain/emailBot/templates",
    static_folder="/Users/scorvicsdomain/emailBot/static",
)

# Absolute path to the backend script
BACKEND_SCRIPT_PATH = "/Users/scorvicsdomain/emailBot/back.py"
PID_FILE = "backend_process.pid"
# Initialize pygame mixer for MP3 playback
pygame.mixer.init()


@app.route("/", methods=["GET"])
def home():
    """Serve the UI for managing alerts."""
    # return render_template("index.html")
    reports = db.fetch_reports()
    print(reports)
    return render_template("index.html", reports=reports)

# @app.route("/start_backend", methods=["POST"])
# def start_backend():
#     """Start the backend process if not already running."""
#     global process
#     if process is None or process.poll() is not None:  # Check if the process is not running
#         process = subprocess.Popen([sys.executable, BACKEND_SCRIPT_PATH])  # Use absolute path
#         return {"status": "Backend started!"}, 200
#     return {"status": "Backend is already running!"}, 400

# @app.route("/stop_backend", methods=["POST"])
# def stop_backend():
#     """Stop the backend process."""
#     global process
#     if process is not None:
#         process.terminate()  # Send a termination signal to the process
#         process = None
#         return {"status": "Backend stopped!"}, 200
#     return {"status": "No backend process running!"}, 400

@app.route("/start_backend", methods=["POST"])
def start_backend():
    """Start the backend process if not already running."""
    if os.path.exists(PID_FILE):  # Check if the PID file exists
        return {"status": "Backend is already running!"}, 400

    # Start the backend process
    process = subprocess.Popen([sys.executable, BACKEND_SCRIPT_PATH])
    
    # Save the process ID to the PID file
    with open(PID_FILE, "w") as f:
        f.write(str(process.pid))

    return {"status": "Backend started!"}, 200

@app.route("/stop_backend", methods=["POST"])
def stop_backend():
    """Stop the backend process."""
    if not os.path.exists(PID_FILE):  # Check if the PID file exists
        return {"status": "No backend process running!"}, 400

    # Read the process ID from the PID file
    with open(PID_FILE, "r") as f:
        pid = int(f.read().strip())

    try:
        os.kill(pid, signal.SIGTERM)  # Terminate the process
    except ProcessLookupError:
        pass  # Process already terminated

    # Remove the PID file
    os.remove(PID_FILE)

    return {"status": "Backend stopped!"}, 200

def play_sound(file_path):
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play(loops=-1)

@app.route("/stop", methods=["POST"])
def stop_alert():
    pygame.mixer.music.stop()  # Stop the sound
    return {"status": "Ringtone stopped!"}, 200

@app.route("/trigger", methods=["POST"])
def trigger_alert():
    play_sound("/Users/scorvicsdomain/emailBot/alert.mp3")  # Start playing the sound
    return {"status": "Ringtone playing!"}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)



