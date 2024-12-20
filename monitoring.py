import requests
import time
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

SERVER_URL = "http://localhost:5000/"

LOG_FILE = "server_status.log"

EMAIL_ALERTS_ENABLED = True
EMAIL_FROM = ""  # Replace with your email
EMAIL_PASSWORD = ""  # Replace with your app password (not account password)
EMAIL_TO = ""  # Replace with recipient's email
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
CHECK_INTERVAL = 10 
WRITE_LOG_INTERVAL = 1800


def send_email_alert(subject, message):
    if not EMAIL_ALERTS_ENABLED:
        return

    try:
        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = EMAIL_FROM
        msg["To"] = EMAIL_TO

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
            print("Email alert sent successfully.")
    except Exception as e:
        print(f"Failed to send email alert: {e}")


def is_server_running():
    try:
        response = requests.get(SERVER_URL, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False


def log_status():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as log_file:
        log_file.write(f"Server is alive. Current time is {current_time}\n")
    print(f"Logged status at {current_time}")


def monitor_server():
    last_log_time = time.time()

    while True:
        if is_server_running():
            print("Server is running.")
        else:
            print("Server is down! Sending alert...")
            send_email_alert(
                "Flask Server Down Alert",
                f"The Flask server at {SERVER_URL} is not responding. Please investigate immediately",
            )

        if time.time() - last_log_time >= WRITE_LOG_INTERVAL:
            log_status()
            last_log_time = time.time()

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    monitor_server()
