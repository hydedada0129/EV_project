'''
pickle is unsafe:
Pickle can execute arbitrary code during loading (pickle.load()).
If someone gives you a maliciously crafted .pickle file, it can run dangerous code on your computer (delete files, install viruses, etc.).
JSON, by contrast, is just plain text — it cannot execute code, only store data.
'''


import os
from dotenv import load_dotenv
import pickle
import base64 # Needed for encoding email
from email.message import EmailMessage
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()
RECIPIENT_EMAIL = os.getenv('GMAIL_RECIPIENT') # Use os.getenv as load_dotenv sets them

# --- Define global constants for the main block ---
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.pickle'
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly",
          "https://www.googleapis.com/auth/gmail.send"]

#Function 1: Get Credentials
def get_credentials(token_path, credentials_path, SCOPES):
    creds=None
    #If token.json exists and the Access Token inside is valid, it loads the tokens from the file.
    if os.path.exists(token_path):
        # creds = Credentials.from_authorized_user_file("token.pickle", SCOPES)
        try:
            #load credentials from pickle file
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
            print(f"credentials loaded from {token_path}")
        except (pickle.UnpicklingError, EOFError, FileNotFoundError) as e:
            print(f"error loading credentials from {token_path}: {e}. need to re-authenticate.")
            creds = None

    #If the Access Token is expired, it uses the Refresh Token (from token.pickle) to get a new Access Token from Google automatically (no browser needed!).
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired credentials...")
            try:
                creds.refresh(Request())
                try:
                    with open(token_path, 'wb') as token:
                        pickle.dump(creds, token)
                    print(f"refreshed credentials saved to {token_path}")
                except Exception as e:
                    print(f"error saving refreshed credentials to {token_path}: {e}")
            except Exception as e:
                print(f"Error refreshing token: {e}")
                print("Need to re-authenticate.")
                creds = None
                # Clean up potentially invalid token file
                if os.path.exists(token_path):
                    try:
                        os.remove(token_path)
                        print(f"Removed potentially invalid {token_path}")
                    except OSError as oe:
                        print(f"Error removing {token_path} during refresh failure: {oe}")
        #If token.json doesn't exist (or tokens are invalid), it triggers the "First Time" flow
        if not creds:
            print("No valid credentials found or refresh failed. Starting authentication flow...")
            if not os.path.exists(credentials_path):
                print(f"ERROR: Credentials file '{credentials_path}' not found.")
                return None
            try:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                # Use port=0 to find an available port automatically
                creds = flow.run_local_server(port=8080)
                # --- Save the new credentials using pickle ---
                try:
                    with open(token_path, 'wb') as token:
                        pickle.dump(creds, token)
                    print(f"Credentials saved to {token_path}")
                except Exception as e:
                    print(f"Error saving new credentials to {token_path}: {e}")
            except Exception as e:
                print(f"Error during authentication flow execution: {e}")
                # If the flow itself fails, we can't get creds, so return None
                return None    # At this point, creds should be valid if we didn't return None earlier
    if creds and creds.valid:
        print("Credentials are valid.")
        print("Granted Scopes:", creds.scopes)

        return creds
    else:
        # This case should ideally not be reached if logic above is correct,
        # but serves as a final fallback.
        print("Failed to obtain valid credentials.")
        return None

# Function 2: Build Service Object
def build_api_service(api_name, api_version, credentials):
    # Builds a Google API service object using provided credentials.
    if not credentials or not credentials.valid:
        print("Cannot build service: Invalid or missing credentials provided.")
        return None

    try:
        service = build(api_name, api_version, credentials=credentials)
        print(f"{api_name.capitalize()} API service ({api_version}) created successfully.")
        # Check if required scopes seem present (optional but good practice)
        granted_scopes = getattr(credentials, 'scopes', []) # Safely get scopes
        return service
    except HttpError as error:
        print(f'An HTTP error occurred building the {api_name} service: {error}')
        if error.resp.status in [401, 403]:
            print(f"Authorization error ({error.resp.status}) during service build.")
            print("Check if credentials have the necessary permissions for this API.")
        return None
    except Exception as e:
        print(f'An unexpected error occurred building the {api_name} service: {e}')
        return None

# Function 3: Send Email
def send_email(service, creds, to_email, subject, body_text):
    #Creates and sends an email message using the provided service object.
    # Check if the service seems to have the required scope (good practice)
    send_scope = 'https://www.googleapis.com/auth/gmail.send'
    granted_scopes = getattr(creds, 'scopes', [])
    # if hasattr(service, '_credentials') and hasattr(service._credentials, 'scopes'):
    #     granted_scopes = service._credentials.scopes
    if send_scope not in granted_scopes:
        print(f"ERROR: Service credentials lack the required '{send_scope}' scope.")
        print("Please ensure it's included in SCOPES and re-authenticate if necessary.")
        return None

    try:
        message = EmailMessage()
        message.set_content(body_text)
        message['To'] = to_email
        message['Subject'] = subject
        # 'From' is automatically set by Gmail

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': encoded_message}

        send_message = service.users().messages().send(
            userId="me", body=create_message
        ).execute()
        print(f"Message Id: {send_message['id']} sent successfully to {to_email}.")
        return send_message

    except HttpError as error:
        print(f'An HTTP error occurred sending email: {error}')
        # e.g., check error.resp.status == 403 for permission denied
        return None
    except Exception as e:
        print(f'An unexpected error occurred sending email: {e}')
        return None

if __name__ == '__main__':
    if not RECIPIENT_EMAIL:
        print("Error: GMAIL_RECIPIENT not set in .env file or environment.")
        exit()
    gmail_service = None

    # 1. Get Credentials
    print("--- Attempting to get credentials ---")
    my_credentials = get_credentials(
        token_path=TOKEN_FILE,
        credentials_path=CREDENTIALS_FILE,
        SCOPES=SCOPES
    )

    if my_credentials:
        print("\nSuccessfully obtained credentials...token.pickle")
        gmail_service = build_api_service(
            api_name='gmail',
            api_version='v1',
            credentials=my_credentials
        )
    else:
        print("\nCould not obtain credentials.")

    if gmail_service:
        email_subject = "Test Email via Python."
        email_body = f"Hello,\n\nThis email is sent to {RECIPIENT_EMAIL}.\n\nRegards,\nScript"
        print(f"\n--- Attempting to send email to: {RECIPIENT_EMAIL} ---")

        send_result = send_email(service=gmail_service,
                   creds=my_credentials,
                   to_email=RECIPIENT_EMAIL,
                   subject=email_subject,
                   body_text=email_body)
        if send_result:
            print("--- Email sending process completed successfully. ---")
        else:
            print("--- Email sending process failed. ---")
    else:
        if not my_credentials:
            print("Failed to get credentials.")
        else:
            print("Failed to build Gmail service.")
    print("\n--- Script finished ---")
'''
if __name__ == '__main__':: Orchestrates the process:
Calls get_credentials.
If successful, calls build_api_service.
If successful, proceeds to use the service (calls send_email).
Includes checks at each stage (if my_credentials:, if gmail_service:).
'''
