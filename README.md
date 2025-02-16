# 📩 Gmail Email Processor

## 📌 Overview

The **Gmail Email Processor** is a Python-based automation tool that integrates with the **Gmail API** to fetch, filter, and categorize emails based on predefined rules stored in a `rules.json` file. The processed emails are stored in an SQLite database for further analysis and tracking.

## 🚀 Features

- ✅ **Fetch Emails**: Retrieves unread emails from Gmail.
- ✅ **Rule-Based Processing**: Applies user-defined rules for email categorization.
- ✅ **Label Management**: Creates and assigns labels dynamically.
- ✅ **Automatic Archiving & Spam Detection**: Moves emails to the appropriate folders.
- ✅ **SQLite Storage**: Stores fetched emails for record-keeping.
- ✅ **Predicate Support**: Supports `ANY` or `ALL` conditions for rule matching.

## 🏗️ Project Structure

```
📂 GMAIL_EMAIL_PROCESSOR
│── 📂 data/                # Contains the SQLite database
│── 📜 process_emails.py    # Main script to fetch and process emails
│── 📜 gmail_auth.py        # Handles Gmail API authentication
│── 📜 fetch_emails.py      # Fetches emails from Gmail
│── 📜 database.py          # Handles SQLite database operations
│── 📜 rules.json           # Contains email filtering rules
│── 📜 README.md            # Project documentation
```

## ⚙️ Installation

### 🔹 Prerequisites

- Python 3.8+
- A **Google Cloud** project with Gmail API enabled.
- OAuth 2.0 credentials (Client ID & Secret).
- `token.json` file for authentication.

## ⚙️ Setup
    1. 🛠 **Clone the repository**:
    ```sh
    git clone https://github.com/your-repo/gmail-email-processor.git
    cd gmail-email-processor
    ```
    2. 📦 **Install dependencies**:
    ```sh
    pip install -r requirements.txt
    ```
    3. 🔐 **Configure Gmail API**:
    - Go to [Google Cloud Console](https://console.cloud.google.com/)
    - Create a new project
    - Enable the **Gmail API**
    - Create **OAuth 2.0 credentials** (Download `client_secret.json`)
    - Place `client_secret.json` in the credentials.json
   

## 📌 Execution Order
Follow this order to properly execute the files:
1.  **Authenticate Gmail API**:
```sh
python gmail_auth.py
```
This will generate a `token.json` file for authentication.

2.  **Create the database**:
```sh
python database.py
```
3.  **Fetch and store emails:**:
```sh
python fetch_emails.py
```
4.  **Process emails based on rules:**:
```sh
python process_emails.py
```
 
## 🎯 Usage

### 🔹 Run the Email Processor

```sh
python process_emails.py
```

### 🔹 Modify `rules.json`

Customize your rules in the `rules.json` file. Example:

```json
{
    "predicate": "ANY",
    "rules": [
        {
            "field": "From",
            "condition": "Contains",
            "value": ["pixlr.com", "quora.com"],
            "action": "Mark as Read"
        },
        {
            "field": "Received Date",
            "condition": "Year",
            "value": "2025",
            "action": "Move to Yearly"
        }
    ]
}
```
## 📬 Viewing Processed Emails
- 📥 **Archived Emails**: Go to Gmail > "All Mail"
- 🏷 **Labeled Emails**: Check the corresponding label in Gmail
- 🚫 **Spam Emails**: Found under the "Spam" folder
- 🔥 **Important Emails**: Available in the "Important" folder

## 🛠️ Troubleshooting

- **Emails not fetching?** Check API credentials and `token.json`.
- **Database file not visible?** Ensure the `data/` folder exists.
- **Ensure** you have enabled the Gmail API in your Google Cloud Console.


## 📬 Contact

For any issues, reach out via GitHub Issues or email `sharadav257@gmail.com`.
