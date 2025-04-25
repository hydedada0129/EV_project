import os
from dotenv import load_dotenv
import base64
from email.message import EmailMessage
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


load_dotenv()
RECIPIENT_EMAIL = os.getenv('GMAIL_RECIPIENT')

CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send"
]

# Function 1: Get Credentials (token.json, credentials.json, SCOPES)
def get_credentials(token_path, credentials_path, SCOPES):
    creds = None
    #if token.json already generated
    if os.path.exists(token_path):
        try:
            #loads previously saved OAUth 2.0 credentials from a JSON file,
            #and create a Credentials object for API authentication
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            print(f"Loaded credentials from {token_path}")
        except Exception as e:
            print(f"Error loading credentials from JSON: {e}")
            creds = None
    #if token.json doesn't exist, or expired
    if not creds or not creds.valid:
        #if exists, but expired and refresh token available
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired credentials...")
            try:
                #refresh an expired access token(after 1 hour) using a refresh token
                creds.refresh(Request())
                #saves the token in token.json
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
                print("Refreshed and saved credentials.")
            except Exception as e:
                print(f"Error refreshing token: {e}")
                creds = None
        if not creds:
            print("No valid credentials found. Starting authentication flow...")
            if not os.path.exists(credentials_path):
                print(f"ERROR: Credentials file '{credentials_path}' not found.")
                return None
            try:
                #InstalledAppFlow: loads client credentials.json, scopes
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                #auto-opens browser for authorization flow, user login
                creds = flow.run_local_server(port=8080)
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
                print(f"New credentials saved to {token_path}")
            except Exception as e:
                print(f"Error during OAuth flow: {e}")
                return None
    #return creds if token.json already exists
    if creds and creds.valid:
        print("Credentials are valid.")
        print("Granted Scopes:", creds.scopes)
        return creds
    else:
        print("Failed to obtain valid credentials.")
        return None

# Function 2: Build Service Object (gmail, v1, credentials)
def build_api_service(api_name, api_version, credentials):
    #if token.json is invalid, or expired (either one can cause failed building object)
    if not credentials or not credentials.valid:
        print("Cannot build service: Invalid or missing credentials provided.")
        return None
    #build service object
    try:
        service = build(api_name, api_version, credentials=credentials)
        print(f"{api_name.capitalize()} API service ({api_version}) created successfully.")
        return service
    #if HTTP request fails (invalid creds, api name/version, timeouts or connectivity issues
    except HttpError as error:
        print(f'HTTP error occurred building {api_name} service: {error}')
        return None
    except Exception as e:
        print(f'Unexpected error building {api_name} service: {e}')
        return None

# Function 3: Send Email
def send_email(service, creds, to_email, subject, body_text):
    send_scope = 'https://www.googleapis.com/auth/gmail.send'
    #get scopes from creds
    granted_scopes = getattr(creds, 'scopes', [])
    if send_scope not in granted_scopes:
        print(f"ERROR: Credentials lack '{send_scope}' scope.")
        return None
    try:
        message = EmailMessage()        #email message object
        message.set_content(body_text)  #assign the plain text body content, MIME type(text/plain)
                                        #MIME: Multipurpose Internet Mail Extensions
        message['To'] = to_email
        message['Subject'] = subject

        #encoding process is required when using Gmail’s API to send emails programmatically
        #message.as_bytes(): object(structured object) to "raw bytes" for email standard(RFC 5322/MIME format)->
        #base64.urlsafe_b64encode(): encodes the raw bytes to "binary-safe transmission"(base64 url-safe string)->
        #.decode(): convert base64 bytes into a utf-8 "string" for JSON/APIs (text-based)
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': encoded_message}   #dictionary, text-based

        #Sends an email using the API and returns the send message details.
        #service.users().messages().send(): #Accesses the Gmail API's "send email" function.
        #1.converts body (dictionary) to JSON
        #2.sends an HTTP POST request to Gmail API endpoint
        #3.response format: Python dict(parsed from JSON)
        send_message = service.users().messages().send(
            userId="me", body=create_message
        ).execute()
        print(f"Message Id: {send_message['id']} sent successfully to {to_email}.")
        return send_message
    #error handling: http or unexpected error.
    except HttpError as error:
        print(f'HTTP error occurred sending email: {error}')
        return None
    except Exception as e:
        print(f'Unexpected error sending email: {e}')
        return None
# Main Execution
if __name__ == '__main__':
    # if recipient email is not set
    if not RECIPIENT_EMAIL:
        print("Error: GMAIL_RECIPIENT not set in .env file or environment.")
        exit()
    print("--- Attempting to get credentials ---")
    my_credentials = get_credentials(
        token_path=TOKEN_FILE,
        credentials_path=CREDENTIALS_FILE,
        SCOPES=SCOPES
    )

    # if credentials is valid, build service object (api name, version, creds)
    if my_credentials:
        print("\nSuccessfully obtained credentials...")
        gmail_service = build_api_service(
            api_name='gmail',
            api_version='v1',
            credentials=my_credentials
        )
    else:
        print("\nCould not obtain credentials.")
        exit()

    #if gmail service object has created, send email!
    if gmail_service:
        email_subject = "Test Email via Python."
        email_body = f"Hello,\n\nThis email is sent to {RECIPIENT_EMAIL}.\n\nRegards,\nScript"
        print(f"\n--- Attempting to send email to: {RECIPIENT_EMAIL} ---")

        send_result = send_email(
            service=gmail_service,  #gmail service object
            creds=my_credentials,
            to_email=RECIPIENT_EMAIL,
            subject=email_subject,
            body_text=email_body
        )
        if send_result:
            print("--- Email sending process completed successfully. ---")
        else:
            print("--- Email sending process failed. ---")
    else:
        print("Failed to build Gmail service.")
    print("\n--- Script finished ---")