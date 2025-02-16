import sqlite3
import os
import logging
from typing import Optional, Tuple, List
from datetime import datetime
import sys
sys.stdout.reconfigure(encoding="utf-8")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_PATH = "data/emails.db"

def ensure_data_directory():
    """Ensure the data directory exists."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_db_connection() -> Tuple[Optional[sqlite3.Connection], Optional[sqlite3.Cursor]]:
    """
    Create a database connection and return connection and cursor.
    """
    try:
        ensure_data_directory()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        return conn, cursor
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return None, None

def create_database() -> bool:
    """
    Delete existing database and create a new one with the required tables.
    """
    try:
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
            logger.info("Existing database deleted.")

        conn, cursor = get_db_connection()
        if not conn or not cursor:
            return False

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gmail_id TEXT UNIQUE NOT NULL,  
                sender TEXT NOT NULL,
                subject TEXT,
                message TEXT,
                folder TEXT,
                received_date TIMESTAMP NOT NULL,
                read_status BOOLEAN DEFAULT 0,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_received_date 
            ON emails(received_date)
        """)

        conn.commit()
        logger.info("Database and tables created successfully.")
        return True

    except Exception as e:
        logger.error(f"Error creating database: {e}")
        return False

    finally:
        if conn:
            conn.close()

def insert_email(gmail_id: str, sender: str, subject: str, message: str, folder: str, received_date: str) -> bool:
    """
    Insert email into the database.
    """
    try:
        conn, cursor = get_db_connection()
        if not conn or not cursor:
            return False

        cursor.execute("""
            INSERT INTO emails (gmail_id, sender, subject, message, folder, received_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (gmail_id, sender, subject, message, folder, received_date))

        conn.commit()
        logger.info(f"Email from {sender} successfully inserted into database")
        return True

    except sqlite3.IntegrityError:
        logger.warning(f"Duplicate email detected (Gmail ID: {gmail_id}), skipping insertion.")
        return False

    except Exception as e:
        logger.error(f"Error inserting email: {e}")
        return False

    finally:
        if conn:
            conn.close()

def get_unread_emails() -> List[dict]:
    """
    Retrieve all unread emails from the database.
    """
    try:
        conn, cursor = get_db_connection()
        if not conn or not cursor:
            return []

        cursor.execute("""
            SELECT id, gmail_id, sender, subject, folder, received_date 
            FROM emails 
            WHERE read_status = 0
            ORDER BY received_date DESC
        """)

        columns = [column[0] for column in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return results

    except Exception as e:
        logger.error(f"Error retrieving unread emails: {e}")
        return []

    finally:
        if conn:
            conn.close()
def insert_many_emails(emails: List[dict]) -> bool:
    """
    Insert multiple emails into the database in a single transaction.
    
    Args:
        emails (List[dict]): A list of email dictionaries containing keys:
            - gmail_id
            - sender
            - subject
            - message
            - folder
            - received_date

    Returns:
        bool: True if insertion is successful, False otherwise.
    """
    try:
        conn, cursor = get_db_connection()
        if not conn or not cursor:
            return False

        cursor.executemany("""
            INSERT INTO emails (gmail_id, sender, subject, message, folder, received_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [(email['gmail_id'], email['sender'], email['subject'], email['body'], "Inbox", email['date_received'])
              for email in emails])

        conn.commit()
        logger.info(f"Successfully inserted {len(emails)} emails into the database.")
        return True

    except sqlite3.IntegrityError:
        logger.warning("Some emails were duplicates and were not inserted.")
        return False

    except Exception as e:
        logger.error(f"Error inserting multiple emails: {e}")
        return False

    finally:
        if conn:
            conn.close()


def update_email_status(email_id: int, read_status: bool) -> bool:
    """
    Update email read status.
    """
    try:
        conn, cursor = get_db_connection()
        if not conn or not cursor:
            return False

        cursor.execute("""
            UPDATE emails 
            SET read_status = ? 
            WHERE id = ?
        """, (read_status, email_id))

        conn.commit()
        logger.info(f"Email ID {email_id} marked as {'Read' if read_status else 'Unread'}")
        return True

    except Exception as e:
        logger.error(f"Error updating email status: {e}")
        return False

    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    if create_database():
        test_email = {
            'gmail_id': 'test12345',
            'sender': 'test@example.com',
            'subject': 'Test Email',
            'message': 'This is a test email',
            'folder': 'Inbox',
            'received_date': datetime.now().isoformat()
        }
        
        if insert_email(
            test_email['gmail_id'],
            test_email['sender'],
            test_email['subject'],
            test_email['message'],
            test_email['folder'],
            test_email['received_date']
        ):
            print("Test email inserted successfully")

        unread_emails = get_unread_emails()
        print("Unread Emails:")
        for email in unread_emails:
            print(email)

        if unread_emails:
            first_email_id = unread_emails[0]['id']
            if update_email_status(first_email_id, True):
                print(f"Marked email ID {first_email_id} as Read")
