import json
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from gmail_auth import authenticate_gmail
from googleapiclient.discovery import build
from typing import Dict, Any, List
from fetch_emails import fetch_emails
import logging

RULES_FILE = "rules.json"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailProcessor:
    def __init__(self):
        self.rules = self._load_rules()
        self.service = None
        self.total_processed = 0
        self.total_matched = 0
        self._init_gmail_service()
        self.label_cache = self._get_existing_labels()
        self.system_labels = {
            'SPAM': 'SPAM',
            'TRASH': 'TRASH',
            'IMPORTANT': 'IMPORTANT',
            'INBOX': 'INBOX'
        }

    def _load_rules(self) -> Dict[str, Any]:
        try:
            with open(RULES_FILE, "r", encoding="utf-8") as file:
                rules = json.load(file).get("rules", [])
                logger.info(f"✅ Loaded {len(rules)} rules from {RULES_FILE}")
                return rules
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"❌ Error loading rules file: {e}")
            return []

    def _init_gmail_service(self):
        try:
            creds = authenticate_gmail()
            self.service = build("gmail", "v1", credentials=creds)
            logger.info("✅ Gmail service initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gmail service: {e}")
            raise

    def _match_string_condition(self, condition: str, values: List[str], text: str) -> bool:
        if not text or not values:
            return False

        text = text.lower()
        condition = condition.lower()

        # For debugging
        logger.debug(f"Matching text: '{text}' against values: {values} using condition: {condition}")

        result = False
        if isinstance(values, str):
            values = [values]

        if condition == "contains":
            result = any(val.lower() in text for val in values)
        elif condition == "startswith":
            result = any(text.startswith(val.lower()) for val in values)
        elif condition == "endswith":
            result = any(text.endswith(val.lower()) for val in values)
        elif condition == "equals":
            result = any(text == val.lower() for val in values)
        elif condition == "noreply":
            result = "noreply" in text or "no-reply" in text

        logger.debug(f"Match result: {result}")
        return result

    def process_emails(self):
        logger.info("🔄 Starting email processing...")
        emails = fetch_emails(max_results=10)
        self.total_processed = len(emails)
        self.total_matched = 0

        if not emails:
            logger.info("📭 No unread emails found.")
            return

        logger.info(f"📨 Processing {len(emails)} emails...")
        print("\n" + "="*50 + "\n")  # Separator for better readability

        for email in emails:
            try:
                self.process_single_email(email)
            except Exception as e:
                logger.error(f"❌ Error processing email: {e}")

        print("\n" + "="*50)  # Separator for better readability
        logger.info(f"✅ Summary: Processed {self.total_processed} emails, {self.total_matched} matched rules.")

    def process_single_email(self, email: Dict[str, Any]) -> bool:
        gmail_id = email["gmail_id"]
        sender = email["sender"]
        subject = email["subject"]
        received_date = email["date_received"]

        print(f"\n📧 Processing email:")
        print(f"   From: {sender}")
        print(f"   Subject: {subject}")
        print(f"   Date: {received_date}")

        try:
            email_date = parsedate_to_datetime(received_date).astimezone(timezone.utc)
        except Exception as e:
            logger.error(f"❌ Error parsing date '{received_date}': {e}")
            return False

        matched_any_rule = False
        for rule_index, rule_set in enumerate(self.rules, 1):
            predicate = rule_set.get("predicate", "ANY").upper()
            conditions = rule_set.get("conditions", [])
            action = rule_set.get("action")

            if not conditions:
                continue

            matches = []
            for condition in conditions:
                match = self._match_rule(condition, sender, subject, email_date)
                matches.append(match)

            rule_matched = all(matches) if predicate == "ALL" else any(matches)

            if rule_matched:
                print(f"\n✨ Matched Rule #{rule_index}:")
                print(f"   Predicate: {predicate}")
                self._apply_rule_action(gmail_id, action)
                matched_any_rule = True
                self.total_matched += 1

        if not matched_any_rule:
            print("   ℹ️ No rules matched")

        return matched_any_rule

    def _match_rule(self, rule: Dict[str, Any], sender: str, subject: str, email_date: datetime) -> bool:
        field = rule["field"].lower()
        condition = rule["condition"].lower()
        value = rule["value"]

        if field == "from":
            return self._match_string_condition(condition, value, sender)
        elif field == "subject":
            return self._match_string_condition(condition, value, subject)
        elif field == "received date":
            now = datetime.now(timezone.utc)
            
            if condition.startswith("last"):
                try:
                    days = int(condition.split()[1])
                    return email_date >= now - timedelta(days=days)
                except (ValueError, IndexError):
                    return False
            elif condition.startswith("older than"):
                try:
                    days = int(condition.split()[2])
                    return email_date <= now - timedelta(days=days)
                except (ValueError, IndexError):
                    return False
            elif condition == "month":
                return email_date.strftime("%B_%Y").lower() == value.replace(" ", "_").lower()
            elif condition == "year":
                return email_date.strftime("%Y") == value
            elif condition == "equals":
                return email_date.strftime("%a, %d %b %Y") == value

        return False

    def _apply_rule_action(self, gmail_id: str, action: Dict[str, Any]):
        action_type = action.get("type")
        try:
            if action_type == "MarkAsRead":
                self.service.users().messages().modify(
                    userId="me",
                    id=gmail_id,
                    body={"removeLabelIds": ["UNREAD"]}
                ).execute()
                print(f"   📖 Action: Marked as Read")

            elif action_type == "MoveTo":
                folder = action.get("folder")
                if folder.upper() in self.system_labels:
                    self.service.users().messages().modify(
                        userId="me",
                        id=gmail_id,
                        body={"addLabelIds": [self.system_labels[folder.upper()]]}
                    ).execute()
                else:
                    self._apply_label(gmail_id, folder)
                print(f"   📂 Action: Moved to {folder}")

            elif action_type == "Archive":
                self.service.users().messages().modify(
                    userId="me",
                    id=gmail_id,
                    body={"removeLabelIds": ["INBOX"]}
                ).execute()
                print(f"   📦 Action: Archived")

            elif action_type == "CreateLabel":
                label_name = action.get("label")
                self._create_label(label_name)
                self._apply_label(gmail_id, label_name)
                print(f"   🏷️ Action: Created/Applied label '{label_name}'")

        except Exception as e:
            logger.error(f"❌ Error applying action {action_type}: {e}")

    def _apply_label(self, gmail_id: str, label_name: str):
        label_name = label_name.upper()
        if label_name not in self.label_cache:
            self._create_label(label_name)

        try:
            label_id = self.label_cache[label_name]
            self.service.users().messages().modify(
                userId="me",
                id=gmail_id,
                body={"addLabelIds": [label_id]}
            ).execute()
        except Exception as e:
            logger.error(f"❌ Error applying label '{label_name}': {e}")

    def _get_existing_labels(self) -> Dict[str, str]:
        try:
            response = self.service.users().labels().list(userId="me").execute()
            labels = {label["name"].upper(): label["id"] for label in response.get("labels", [])}
            logger.info(f"✅ Retrieved {len(labels)} existing labels")
            return labels
        except Exception as e:
            logger.error(f"❌ Error fetching labels: {e}")
            return {}

    def _create_label(self, label_name: str):
        try:
            if label_name.upper() in self.label_cache:
                return

            label_body = {
                "name": label_name,
                "labelListVisibility": "labelShow",
                "messageListVisibility": "show"
            }

            response = self.service.users().labels().create(userId="me", body=label_body).execute()
            self.label_cache[label_name.upper()] = response["id"]
            logger.info(f"✅ Created new label: {label_name}")
        except Exception as e:
            logger.error(f"❌ Error creating label '{label_name}': {e}")

if __name__ == "__main__":
    processor = EmailProcessor()
    processor.process_emails()