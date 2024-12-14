import sqlite3
from datetime import datetime
from collections import OrderedDict
# SQLite DB setup
DB_PATH = "email_matches.db"

# Create SQLite database and table if not exist
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
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_email TEXT,
        to_email TEXT,
        subject TEXT,
        date TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.commit()
    conn.close()

def insert_into_db(from_email, to_email, subject, date):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Check if the entry already exists
    c.execute("""
    SELECT 1 FROM email_matches WHERE from_email=? AND to_email=? AND subject=? AND date=?
    """, (from_email, to_email, subject, date))
    if c.fetchone() is None:  # If no entry exists, insert it
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
    INSERT INTO matched_data_report (from_email, to_email, subject, date)
    VALUES (?, ?, ?, ?)""", (from_email, to_email, subject, date))
    conn.commit()
    print(f"Inserted into matched_data_report: {from_email}, {to_email}, {subject}, {date}")
    conn.close()

def remove_expired_entries(latest_email_info):
    """Remove expired entries from DB."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # Prepare a set of the latest email info for comparison
        latest_email_set = set(latest_email_info)

        # Get all records from the database
        c.execute("SELECT from_email, to_email, subject, date FROM email_matches")
        existing_records = c.fetchall()

        # Find expired entries (those in the DB but not in the latest emails)
        expired_entries = [
            (from_email, to_email, subject, date)
            for (from_email, to_email, subject, date) in existing_records
            if (from_email, to_email, subject, date) not in latest_email_set
        ]
        print(f"Expired entries that we are going to remove is:{expired_entries}")
        # Remove expired entries
        if expired_entries:
            c.executemany(
                """
                DELETE FROM email_matches 
                WHERE from_email=? AND to_email=? AND subject=? AND date=?
                """, expired_entries
            )
            print(f"Removed {len(expired_entries)} expired entries.")
        
        # Commit changes
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

# def fetch_reports():
#     """Fetch reports grouped by date from the database."""
#     conn = sqlite3.connect(DB_PATH)
#     cursor = conn.cursor()
#     query = """
#     SELECT 
#         date AS report_date, 
#         from_email, 
#         to_email, 
#         subject, 
#         date
#     FROM 
#         matched_data_report
#     GROUP BY 
#         date, from_email, subject, to_email
#     ORDER BY 
#         date DESC;
#     """
#     cursor.execute(query)
#     data = cursor.fetchall()
#     conn.close()

#     # Group data by date
#     grouped_data = {}
#     for row in data:
#         report_date, from_email, to_email, subject, date = row
#         if report_date not in grouped_data:
#             grouped_data[report_date] = []
#         grouped_data[report_date].append({
#             "from_email": from_email,
#             "subject": subject,
#             "mail_datetime": date,
#         })
#     return grouped_data

# def remove_duplicates(data):
#     """Remove duplicate entries from the grouped data."""
#     cleaned_data = {}

#     for date, entries in data.items():
#         unique_entries = set()  # Track unique entries
#         cleaned_data[date] = []

#         for entry in entries:
#             # Create a tuple of the entry values to check for uniqueness
#             entry_tuple = (entry["from_email"], entry["subject"], entry["mail_datetime"])
            
#             if entry_tuple not in unique_entries:
#                 unique_entries.add(entry_tuple)  # Add to the set of unique entries
#                 cleaned_data[date].append(entry)  # Add to cleaned data

#     return cleaned_data

def remove_duplicates(data):
    """Remove duplicate entries and sort the dictionary by date."""
    cleaned_data = {}

    # Remove duplicates
    for date, entries in data.items():
        unique_entries = set()  # Track unique entries
        cleaned_data[date] = []

        for entry in entries:
            # Create a tuple of the entry values to check for uniqueness
            entry_tuple = (entry["from_email"], entry["subject"], entry["mail_datetime"])
            
            if entry_tuple not in unique_entries:
                unique_entries.add(entry_tuple)  # Add to the set of unique entries
                cleaned_data[date].append(entry)  # Add to cleaned data

    # Sort the dictionary by date
    sorted_cleaned_data = OrderedDict(sorted(cleaned_data.items()))

    return sorted_cleaned_data

def fetch_reports():
    """Fetch reports grouped by date from the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = """
    SELECT 
        date AS report_date, 
        from_email, 
        to_email, 
        subject, 
        date
    FROM 
        matched_data_report
    ORDER BY 
        date DESC;
    """
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()

    # Group data by date
    grouped_data = {}
    for row in data:
        report_date, from_email, to_email, subject, date = row

        # Handle 'GMT' and convert to date format
        if "GMT" in report_date:
            report_date = report_date.replace("GMT", "+0000")
        
        # Extract just the date part
        report_date_only = datetime.strptime(report_date, "%a, %d %b %Y %H:%M:%S %z").date()

        # Convert date to a string for consistent grouping
        report_date_str = report_date_only.strftime("%Y-%m-%d")
        
        if report_date_str not in grouped_data:
            grouped_data[report_date_str] = []
        grouped_data[report_date_str].append({
            "from_email": from_email,
            "subject": subject,
            "mail_datetime": date,
        })
    cleaned_data = remove_duplicates(grouped_data)
    return cleaned_data
