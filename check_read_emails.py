import sqlite3

DB_PATH = "data/emails.db"

def check_read_emails():
    """Retrieve and display emails marked as 'Read'."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, sender, subject, read_status FROM emails WHERE read_status = 'Read';")
    emails = cursor.fetchall()

    conn.close()

    if emails:
        print("\nProcessed Emails:")
        for email in emails:
            print(f"ID: {email[0]}, From: {email[1]}, Subject: {email[2]}, Status: {email[3]}")
    else:
        print("\nNo emails have been marked as 'Read' yet.")

if __name__ == "__main__":
    check_read_emails()
