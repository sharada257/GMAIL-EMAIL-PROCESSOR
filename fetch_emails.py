from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
import logging
from typing import List, Dict, Any
from gmail_auth import authenticate_gmail
from database import insert_many_emails

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_emails(max_results: int = 20) -> List[Dict[str, Any]]:
    """
    Fetch emails from Gmail and prepare them for database storage.

    Args:
        max_results (int): Maximum number of emails to fetch.

    Returns:
        List[Dict[str, Any]]: List of processed email data.
    """
    creds = authenticate_gmail()
    if not creds:
        logger.error("Failed to authenticate with Gmail")
        return []

    try:
        service = build("gmail", "v1", credentials=creds)
        results = service.users().messages().list(userId="me", maxResults=max_results).execute()

        messages = results.get("messages", [])
        processed_emails = []

        for msg in messages:
            try:
                msg_detail = service.users().messages().get(userId="me", id=msg["id"]).execute()
                headers = msg_detail["payload"]["headers"]

                email_data = {
                    "gmail_id": msg["id"],  # ✅ Ensure Gmail ID is stored
                    "sender": next((h["value"] for h in headers if h["name"].lower() == "from"), "Unknown"),
                    "subject": next((h["value"] for h in headers if h["name"].lower() == "subject"), "No Subject"),
                    "date_received": next((h["value"] for h in headers if h["name"].lower() == "date"), "Unknown"),
                    "body": ""
                }

                # Handle different payload structures
                payload = msg_detail.get("payload", {})
                if "parts" in payload:
                    for part in payload["parts"]:
                        if part.get("mimeType") == "text/plain":
                            body_data = part.get("body", {}).get("data", "")
                            if body_data:
                                email_data["body"] = base64.urlsafe_b64decode(body_data).decode("utf-8", "ignore")
                                break
                elif "body" in payload:
                    body_data = payload["body"].get("data", "")
                    if body_data:
                        email_data["body"] = base64.urlsafe_b64decode(body_data).decode("utf-8", "ignore")

                processed_emails.append(email_data)

            except Exception as e:
                logger.error(f"Error processing message {msg['id']}: {e}")
                continue

        return processed_emails

    except HttpError as error:
        logger.error(f"Gmail API error: {error}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []

if __name__ == "__main__":
    emails = fetch_emails()
    if emails:
        logger.info(f"Successfully fetched {len(emails)} emails")

        # ✅ Insert fetched emails into the database
        if insert_many_emails(emails):
            logger.info("Emails successfully stored in database")
        else:
            logger.error("Failed to store emails in database")
    else:
        logger.error("No emails fetched")
