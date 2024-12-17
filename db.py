import sqlite3
from datetime import datetime
from collections import OrderedDict
import json
import pytz
import re

DB_PATH = "email_matches.db"

def create_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS email_matches (
        from_email TEXT,
        to_email TEXT,
        subject TEXT,
        date TEXT,
        PRIMARY KEY (from_email, to_email, subject, date)
    )""")

    conn.commit()
    conn.close()

def create_matched_data_report_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS matched_data_report (
        from_email TEXT,
        to_email TEXT,
        subject TEXT,
        date TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (from_email, to_email, subject, date)
    )""")
    conn.commit()
    conn.close()

def create_config_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id TEXT NOT NULL,
            app_password TEXT NOT NULL,
            mail_to_check TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_config(email_id, app_password, mail_to_check):
    create_config_table()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM config_table")

        cursor.execute('''
            INSERT INTO config_table (email_id, app_password, mail_to_check)
            VALUES (?, ?, ?)
        ''', (email_id, app_password, json.dumps(mail_to_check))) 

        conn.commit()
        success = True
    except Exception as e:
        print(f"Error updating config_table: {e}")
        success = False
    finally:
        conn.close()
    return success

def insert_into_db(from_email, to_email, subject, date):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
    SELECT 1 FROM email_matches WHERE from_email=? AND to_email=? AND subject=? AND date=?
    """, (from_email, to_email, subject, date))
    if c.fetchone() is None:  
        c.execute("""
        INSERT INTO email_matches (from_email, to_email, subject, date)
        VALUES (?, ?, ?, ?)""", (from_email, to_email, subject, date))
        conn.commit()
        print(f"Inserted: {from_email}, {to_email}, {subject}, {date}")
    else:
        print(f"Skipped duplicate entry")
    conn.close()

def insert_into_matched_report(from_email, to_email, subject, date):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    INSERT OR IGNORE INTO matched_data_report (from_email, to_email, subject, date)
    VALUES (?, ?, ?, ?)""", (from_email, to_email, subject, date))
    conn.commit()
    print(f"Inserted into matched_data_report: {from_email}, {to_email}, {subject}, {date}")
    conn.close()

def remove_expired_entries(latest_email_info):
    """Remove expired entries from DB."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        latest_email_set = set(latest_email_info)

        c.execute("SELECT from_email, to_email, subject, date FROM email_matches")
        existing_records = c.fetchall()

        expired_entries = [
            (from_email, to_email, subject, date)
            for (from_email, to_email, subject, date) in existing_records
            if (from_email, to_email, subject, date) not in latest_email_set
        ]
        # print(f"Expired entries that we are going to remove is:{expired_entries}")
    
        if expired_entries:
            print(f"Expired entries that we are going to remove: {expired_entries}")
            c.executemany(
                """
                DELETE FROM email_matches 
                WHERE from_email=? AND to_email=? AND subject=? AND date=?
                """, expired_entries
            )
            print(f"Removed {len(expired_entries)} expired entries.")
        
        conn.commit()

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        conn.close()

def is_email_in_db(from_email, to_email, subject, date):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    SELECT 1 FROM email_matches 
    WHERE from_email = ? AND to_email = ? AND subject = ? AND date = ?
    """, (from_email, to_email, subject, date))
    result = c.fetchone()
    conn.close()
    return result is not None

# def remove_duplicates(data):
#     """Remove duplicate entries and sort the dictionary by date."""
#     cleaned_data = {}

#     for date, entries in data.items():
#         unique_entries = set() 
#         cleaned_data[date] = []

#         for entry in entries:
#             entry_tuple = (entry["from_email"], entry["subject"], entry["mail_datetime"])
            
#             if entry_tuple not in unique_entries:
#                 unique_entries.add(entry_tuple) 
#                 cleaned_data[date].append(entry) 

#     sorted_cleaned_data = OrderedDict(sorted(cleaned_data.items()))

#     return sorted_cleaned_data

def fetch_reports():
    """Fetch reports grouped by date from the database."""
    create_matched_data_report_table()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = """
    SELECT 
        date AS report_date, 
        from_email, 
        to_email, 
        subject
    FROM 
        matched_data_report
    ORDER BY 
        date DESC;
    """
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()
    # print(data)
    grouped_data = {}
    for row in data:
        report_date, from_email, to_email, subject = row

        if "GMT" in report_date:
             report_date = report_date.replace("GMT", "+0000")

        clean_date = report_date.split("(")[0].strip()
        dt = datetime.strptime(clean_date, "%a, %d %b %Y %H:%M:%S %z")

        report_date_str = dt.astimezone().strftime("%d %b %Y")
        
        if report_date_str not in grouped_data:
            grouped_data[report_date_str] = []
        grouped_data[report_date_str].append({
            "from_email": from_email,
            "subject": subject,
            "mail_datetime": report_date,
        })
    # cleaned_data = remove_duplicates(grouped_data)
    return grouped_data

def fetch_config():
    """Fetch the latest config from the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT email_id, app_password, mail_to_check FROM config_table LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        email_id, app_password, mail_to_check = row
        return {
            "email_id": email_id,
            "app_password": app_password,
            "mail_to_check": json.loads(mail_to_check)
        }
    return None



