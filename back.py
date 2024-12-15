import db
import time
import imaplib
import email
from email.header import decode_header
import requests
import logging
from datetime import datetime
import email.utils
from flask import Flask, request
import os
import threading

FRONTEND_TRIGGER_URL = "http://localhost:5000/trigger"
ERROR_MSG_URL = "http://localhost:5000/error"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def send_frontend_alert(message: str) -> None:
    """Send alert to frontend with error handling."""
    try:
        response = requests.post(
            FRONTEND_TRIGGER_URL,
            json={"alert": message},
            timeout=10
        )
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Failed to send frontend alert: {e}")

def send_ERROR(message: str) -> None:
    """Send alert to frontend with error handling."""
    try:
        response = requests.post(
            ERROR_MSG_URL,
            json={"alert": message},
            timeout=10
        )
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Failed to send frontend alert: {e}")

def fetch_latest_emails(email_id, app_password, mail_to_check):
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(email_id, app_password)
        print(f"Succefully login to {email_id}")
        mail.select("inbox")
        
        status, messages = mail.search(None, "ALL")
        if status != "OK":
            print("Failed to retrieve emails.")
            return
        
        email_ids = messages[0].split()[-100:] 
        latest_email_info = []
        
        for email_id in email_ids:
            status, msg_data = mail.fetch(email_id, "(BODY[HEADER.FIELDS (TO FROM SUBJECT DATE)])")
            if status != "OK":
                continue
            
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    to_email = extract_email(msg.get("To", "").strip())
                    from_email = extract_email(msg.get("From", "").strip())
                    subject = msg.get("Subject", "").strip()
                    date = msg.get("Date", "").strip()
                    
                    if to_email and from_email and subject and date:
                        if (from_email, to_email, subject, date) not in latest_email_info:
                            latest_email_info.append((from_email, to_email, subject, date))

            print(latest_email_info)
            for Mail in mail_to_check:
                for from_email, to_email, subject, date in latest_email_info:
                    if Mail in [from_email, to_email]:
                        if not db.is_email_in_db(from_email, to_email, subject, date):
                            print(f"{Mail} is present in the list. Triggering alert!")
                            send_frontend_alert(f"Alert: {Mail} is in your inbox!")
                            db.insert_into_db(from_email, to_email, subject, date)
                            db.insert_into_matched_report(from_email, to_email, subject, date)
                        else:
                            print(f"{Mail} is present but already handled. Skipping alert and insert.")

        db.remove_expired_entries(latest_email_info)
        mail.logout()

    except imaplib.IMAP4.error as e:
        print(f"Login failed for {email_id}. Error: {e}")
        send_ERROR(f"Login failed for {email_id}. Error: {e}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        send_ERROR(f"An error occurred: {str(e)}")


def extract_email(address):
    """Extract email address from a string."""
    if '<' in address and '>' in address:
        start_idx = address.find('<') + 1
        end_idx = address.find('>')
        return address[start_idx:end_idx]
    else:
        return address

    
if __name__ == "__main__":
    db.create_db()
    db.create_matched_data_report_table()
    db.create_config_table()
   
    while True:
        config = db.fetch_config()
        if config:
            email_id = config["email_id"]
            app_password = config["app_password"]
            mail_to_check = config["mail_to_check"]

            fetch_latest_emails(email_id, app_password, mail_to_check)
        else:
            print("No configuration found in the database.")
            send_ERROR("No configuration found in the database.Please add Config First")
        time.sleep(10)  # Sleep for 10 sec

