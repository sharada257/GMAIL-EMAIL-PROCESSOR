from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
from typing import Optional
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

def authenticate_gmail() -> Optional[Credentials]:
    try:
        creds = None
        
        if os.path.exists("token.json"):
            try:
                creds = Credentials.from_authorized_user_file("token.json", SCOPES)
                logger.info("Loaded existing credentials from token.json")
            except Exception as e:
                logger.error(f"Error loading token.json: {e}")
                if os.path.exists("token.json"):
                    os.remove("token.json")
                    logger.info("Removed invalid token.json")

    
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    logger.info("Refreshing expired credentials")
                    creds.refresh(Request())
                    logger.info("Successfully refreshed credentials")
                except Exception as e:
                    logger.error(f"Error refreshing credentials: {e}")
                    return None
            else:
                try:
                    if not os.path.exists("credentials.json"):
                        logger.error("credentials.json not found")
                        raise FileNotFoundError(
                            "credentials.json not found. Please download it from Google Cloud Console "
                            "and save it in the same directory as this script."
                        )

                
                    flow = InstalledAppFlow.from_client_secrets_file(
                        "credentials.json",
                        SCOPES,
                        redirect_uri='http://localhost'
                    )

                    logger.info("Starting local server for authentication")
                    creds = flow.run_local_server(port=0)
                    logger.info("Successfully obtained new credentials")

                except Exception as e:
                    logger.error(f"Error during OAuth flow: {e}")
                    return None

            try:
                with open("token.json", "w") as token:
                    token.write(creds.to_json())
                logger.info("Saved credentials to token.json")
            except Exception as e:
                logger.error(f"Error saving credentials to token.json: {e}")
                return None

        return creds

    except Exception as e:
        logger.error(f"Unexpected error during authentication: {e}")
        return None

if __name__ == "__main__":
    credentials = authenticate_gmail()
    if credentials:
        print("Authentication successful!")
        print(f"Token valid until: {credentials.expiry}")
    else:
        print("Authentication failed!")