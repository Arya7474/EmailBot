import db
import time
import imaplib
import email
from email.header import decode_header
import requests
import logging
from datetime import datetime

# Flask-related imports
from flask import Flask, request
import os
import threading

# Frontend Flask URL
FRONTEND_TRIGGER_URL = "http://localhost:5000/trigger"

# Logger setup (for better error handling)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# SQLite DB setup
# DB_PATH = "email_matches.db"

# Function to send alert to frontend
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

# # Create SQLite database and table if not exist
# def create_db():
#     conn = sqlite3.connect(DB_PATH)
#     c = conn.cursor()
#     c.execute("""
#     CREATE TABLE IF NOT EXISTS email_matches (
#         from_email TEXT,
#         to_email TEXT,
#         subject TEXT,
#         date TEXT,
#         PRIMARY KEY (from_email, to_email, subject, date)
#     )""")
#     conn.commit()
#     conn.close()

# Function to check and insert matched emails into DB
# def insert_into_db(from_email, to_email, subject, date):
#     conn = sqlite3.connect(DB_PATH)
#     c = conn.cursor()
#     # timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#     c.execute("""
#     INSERT OR IGNORE INTO email_matches (from_email, to_email, subject, date)
#     VALUES (?, ?, ?, ?)""", (from_email, to_email, subject, date))
#     conn.commit()
#     print(f"Inserted: {from_email}, {to_email}, {subject}, {date}")
#     conn.close()

# def insert_into_db(from_email, to_email, subject, date):
#     conn = sqlite3.connect(DB_PATH)
#     c = conn.cursor()
#     # Check if the entry already exists
#     c.execute("""
#     SELECT 1 FROM email_matches WHERE from_email=? AND to_email=? AND subject=? AND date=?
#     """, (from_email, to_email, subject, date))
#     if c.fetchone() is None:  # If no entry exists, insert it
#         c.execute("""
#         INSERT INTO email_matches (from_email, to_email, subject, date)
#         VALUES (?, ?, ?, ?)""", (from_email, to_email, subject, date))
#         conn.commit()
#         print(f"Inserted: {from_email}, {to_email}, {subject}, {date}")
#     else:
#         print(f"Skipped duplicate entry")
#     conn.close()

# Function to fetch and check the latest emails
# def fetch_latest_emails(email_id, app_password, mail_to_check):
#     try:
#         # Connect to Gmail's IMAP server
#         mail = imaplib.IMAP4_SSL("imap.gmail.com")
        
#         # Log in to the account
#         mail.login(email_id, app_password)
#         print(f"Login successful for {email_id}")
        
#         # Select the inbox (only Primary category emails)
#         mail.select("inbox")
        
#         # Search for all emails in the Primary category (CATEGORY_PERSONAL)
#         status, messages = mail.search(None, "ALL")
#         if status != "OK":
#             print("Failed to retrieve emails.")
#             return

#         # Get a list of email IDs
#         email_ids = messages[0].split()
        
#         # Get the last 20 email IDs
#         latest_email_ids = email_ids[-20:] if len(email_ids) > 20 else email_ids
        
#         email_info_list = []  # List to store TO and FROM info sequentially
#         latest_email_info = []  # For checking expired emails

#         # Fetch emails and extract their TO and FROM fields
#         for email_id in latest_email_ids:
#             # Fetch the email by ID
#             status, msg_data = mail.fetch(email_id, "(BODY[HEADER.FIELDS (TO FROM SUBJECT DATE)])")
#             if status != "OK":
#                 print(f"Failed to fetch email ID {email_id.decode()}")
#                 continue
            
#             for response_part in msg_data:
#                 if isinstance(response_part, tuple):
#                     # Parse the email
#                     msg = email.message_from_bytes(response_part[1])
                    
#                     # Decode the "To", "From", "Subject" and "Date" fields
#                     to_field = msg.get("To", "").strip()
#                     from_field = msg.get("From", "").strip()
#                     subject = msg.get("Subject", "").strip()
#                     date = msg.get("Date", "").strip()
                    
#                     # Extract only the email addresses
#                     to_email = extract_email(to_field)
#                     from_email = extract_email(from_field)
                    
#                     # Append TO and FROM email addresses to the list
#                     if to_email and from_email and subject and date:
#                         latest_email_info.append((from_email, to_email, subject, date))
#                         email_info_list.append(to_email)
#                         email_info_list.append(from_email)
        
#         # Check if any of the mail_to_check are present
#         for Mail in mail_to_check:
#             if Mail in email_info_list:
#                 print(f"{Mail} is present in the list. Triggering alert!")
#                 send_frontend_alert(f"Alert: {Mail} is in your inbox!")
#                 # Insert to DB
#                 for entry in latest_email_info:
#                     if len(entry) == 4:
#                         from_email, to_email, subject, date = entry
#                         insert_into_db(from_email, to_email, subject, date)
#                         break
#                     else:
#                         print(f"Skipping entry: {entry} (unexpected number of values)")
#             else:
#                 print(f"{Mail} is not found in the list.")
        
#         # Check for expired entries and remove them from the database
#         remove_expired_entries(latest_email_info)
        
#         # Logout from the account
#         mail.logout()

#     except imaplib.IMAP4.error as e:
#         print(f"Login failed for {email_id}. App password might be expired or incorrect.")
#         print(f"Error: {e}")
#     except Exception as e:
#         print(f"An error occurred: {str(e)}"

# def remove_expired_entries(latest_email_info):
#     """Remove expired entries from DB."""
#     conn = sqlite3.connect(DB_PATH)
#     c = conn.cursor()
    
#     # Get all records from the database
#     c.execute("SELECT * FROM email_matches")
#     existing_records = c.fetchall()

#     # Convert the records to a set for faster comparison
#     existing_set = set(existing_records)

#     # Compare with the latest emails and find expired entries
#     for (from_email, to_email, subject, date) in existing_records:
#         if (from_email, to_email, subject, date) not in latest_email_info:
#             c.execute("""
#             DELETE FROM email_matches WHERE from_email=? AND to_email=? AND subject=? AND date=?
#             """, (from_email, to_email, subject, date))
#             conn.commit()
#             print(f"Removed expired entry: {from_email}, {to_email}, {subject}, {date}")

#     conn.close()

# def remove_expired_entries(latest_email_info):
#     """Remove expired entries from DB."""
#     conn = sqlite3.connect(DB_PATH)
#     c = conn.cursor()
    
#     try:
#         # Prepare a set of the latest email info for comparison
#         latest_email_set = set(latest_email_info)

#         # Get all records from the database
#         c.execute("SELECT from_email, to_email, subject, date FROM email_matches")
#         existing_records = c.fetchall()

#         # Find expired entries (those in the DB but not in the latest emails)
#         expired_entries = [
#             (from_email, to_email, subject, date)
#             for (from_email, to_email, subject, date) in existing_records
#             if (from_email, to_email, subject, date) not in latest_email_set
#         ]
#         print(f"Expired entries that we are going to remove is:{expired_entries}")
#         # Remove expired entries
#         if expired_entries:
#             c.executemany(
#                 """
#                 DELETE FROM email_matches 
#                 WHERE from_email=? AND to_email=? AND subject=? AND date=?
#                 """, expired_entries
#             )
#             print(f"Removed {len(expired_entries)} expired entries.")
        
#         # Commit changes
#         conn.commit()

#     except sqlite3.Error as e:
#         print(f"Database error: {e}")
#     except Exception as e:
#         print(f"Unexpected error: {e}")
#     finally:
#         conn.close()


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
        
        email_ids = messages[0].split()[-500:]  # Get the last 20 email IDs
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
        
        
        # for Mail in mail_to_check:
        #     for from_email, to_email, subject, date in latest_email_info:
        #         if Mail in [from_email, to_email]:
        #             print(f"{Mail} is present in the list. Triggering alert!")
        #             send_frontend_alert(f"Alert: {Mail} is in your inbox!")
        #             insert_into_db(from_email, to_email, subject, date)
        
        # Check matches and insert into DB
            print(latest_email_info)
            # latest_email_info = list(set(latest_email_info))
            for Mail in mail_to_check:
                for from_email, to_email, subject, date in latest_email_info:
                    if Mail in [from_email, to_email]:
                        # Check if the email is already in the database
                        if not db.is_email_in_db(from_email, to_email, subject, date):
                            print(f"{Mail} is present in the list. Triggering alert!")
                            send_frontend_alert(f"Alert: {Mail} is in your inbox!")
                            db.insert_into_db(from_email, to_email, subject, date)
                            db.insert_into_matched_report(from_email, to_email, subject, date)
                        else:
                            print(f"{Mail} is present but already handled. Skipping alert and insert.")

        # Remove expired entries
        db.remove_expired_entries(latest_email_info)
        mail.logout()

    except imaplib.IMAP4.error as e:
        print(f"Login failed for {email_id}. Error: {e}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


def extract_email(address):
    """Extract email address from a string."""
    if '<' in address and '>' in address:
        start_idx = address.find('<') + 1
        end_idx = address.find('>')
        return address[start_idx:end_idx]
    else:
        return address


if __name__ == "__main__":
    email_id = ""
    app_password = ""
    mail_to_check = []
    # Create the database if not already created
    db.create_db()
    db.create_matched_data_report_table()
    
    # Run the function every 10 sec
    while True:
        fetch_latest_emails(email_id, app_password, mail_to_check)
        time.sleep(10)  # Sleep for 10 sec

