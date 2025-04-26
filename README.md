Summary of Structure:
get_credentials(...): Handles only authentication (pickle load/refresh/flow) and returns the Credentials object or None. 
build_api_service(...): Takes credentials and only builds the service object using build(), returning the service or None.
send_email(...): Takes the built service object and handles only composing and sending the email via the API.
if __name__ == '__main__':: Orchestrates the process:
Calls get_credentials.
If successful, calls build_api_service.
If successful, proceeds to use the service (calls send_email).
Includes checks at each stage (if my_credentials:, if gmail_service:).

Step 1: App loads client_secret.json
Step 2: App redirects user to Google login page
Step 3: User approves permission (send email, read inbox, etc.)
Step 4: Google sends Authorization Code
Step 5: App uses Authorization Code + client_secret to get Access Token
Step 6: App saves Access Token + Refresh Token into token.pickle

Step | Action
1 | Prepare your client_secret.json
2 | Set correct SCOPES (example: gmail.send)
3 | Open browser login via InstalledAppFlow
4 | User approves access
5 | Google sends back an Access Token + a Refresh Token
6 | Save both tokens into your token.pickle or token.json file

.pickle file:
You get a Credentials object (contains Access Token, Refresh Token, expiry time, etc.)
