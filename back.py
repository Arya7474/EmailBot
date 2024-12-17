import db
import time
import imaplib
import email
import requests
import logging
import email.utils
from email.utils import parsedate_to_datetime
import pytz 

# variables
IST = pytz.timezone('Asia/Kolkata')
server="imap.gmail.com"
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

def extract_email(address):
    """Extract email address from a string."""
    if '<' in address and '>' in address:
        start_idx = address.find('<') + 1
        end_idx = address.find('>')
        return address[start_idx:end_idx]
    else:
        return address

def fetch_and_search_emails(EMAIL,PASSWORD,mail_to_check,IST,server):
    try:
        mail = imaplib.IMAP4_SSL(server)
        if mail.login(EMAIL, PASSWORD):
            print(f"Login Successfull for {EMAIL}")
        else:
            print(f"Login Failed")
            return
        mail.select("inbox")
        result, data = mail.search(None, "ALL")
        email_ids = data[0].split()
        
        last_100_ids = email_ids[-100:]
        if not last_100_ids:
            print("No emails found.")
            return
        
        fetch_range = ",".join(last_100_ids.decode('utf-8') for last_100_ids in last_100_ids)
        result, data = mail.fetch(fetch_range, "(BODY[HEADER.FIELDS (FROM TO SUBJECT DATE)])")
        
        print("Fetching, parsing, and searching emails...")
        # current_dates = [] 
        current_emails = [] 
        for response_part in data:
            if isinstance(response_part, tuple):
                raw_email = response_part[1].decode('utf-8')
                msg = email.message_from_string(raw_email)

                sender = extract_email(msg.get('From', 'Unknown Sender').strip())
                to_email = extract_email(msg.get('To', 'Unknown Recipient').strip())
                subject = msg.get('Subject', 'No Subject')
                date = msg.get('Date', 'Unknown Date')

                if date != 'Unknown Date':
                    email_date = parsedate_to_datetime(date).astimezone(IST)
                    date_str = email_date.strftime('%Y-%m-%d %H:%M:%S %Z')  # Format: YYYY-MM-DD HH:MM:SS IST
                    # current_dates.append(date_str)
                else:
                    date_str = "Unknown Date"
                current_emails.append((sender, to_email, subject, date_str))
                # Check if sender email matches any in mail_to_check
                if any(email_id in sender for email_id in mail_to_check):
                    if not db.is_email_in_db(sender, to_email, subject, date_str):
                        print(f"{sender} is present in the list. Triggering alert!")
                        send_frontend_alert(f"Alert: {sender} is in your inbox!")
                        db.insert_into_db(sender, to_email, subject, date_str)
                        db.insert_into_matched_report(sender, to_email, subject, date)
                    else:
                        print(f"{sender} - Already handled. Skipping alert.")

        db.remove_expired_entries(current_emails)
    
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        try:
            mail.logout()
        except:
            print("failed to mail login")
            pass

if __name__ == "__main__":
    db.create_db()
    db.create_matched_data_report_table()
   
    while True:
        # print("started.......")
        config = db.fetch_config()
        if config:
            email_id = config["email_id"]
            app_password = config["app_password"]
            mail_to_check = config["mail_to_check"]

            fetch_and_search_emails(email_id, app_password, mail_to_check,IST,server)
        else:
            print("No configuration found in the database.")
            send_ERROR("No configuration found in the database.Please add Config First")
        # print("sleep for 10 sec....")
        time.sleep(10)



