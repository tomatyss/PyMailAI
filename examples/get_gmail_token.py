"""Helper script to obtain Gmail OAuth2 refresh token."""

import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlencode, parse_qs
import webbrowser

import requests

# OAuth2 configuration
OAUTH_CONFIG = {
    'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
    'token_uri': 'https://oauth2.googleapis.com/token',
    'scope': 'https://mail.google.com/',
    'redirect_uri': 'http://localhost:8080',
    'response_type': 'code',
    'access_type': 'offline',
    'prompt': 'consent'
}

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth2 callback requests."""

    def do_GET(self):
        """Process OAuth2 callback and get refresh token."""
        # Parse the authorization code from query parameters
        query_components = parse_qs(self.path.split('?')[1])
        auth_code = query_components['code'][0]

        # Exchange authorization code for tokens
        token_params = {
            'client_id': os.getenv('GMAIL_CLIENT_ID'),
            'client_secret': os.getenv('GMAIL_CLIENT_SECRET'),
            'code': auth_code,
            'redirect_uri': OAUTH_CONFIG['redirect_uri'],
            'grant_type': 'authorization_code'
        }

        response = requests.post(OAUTH_CONFIG['token_uri'], data=token_params)
        tokens = response.json()

        if 'refresh_token' not in tokens:
            self.send_error(400, "No refresh token in response. Try revoking access and running again.")
            return

        # Save credentials
        creds_path = Path.home() / '.config' / 'pymailai' / 'gmail_creds.json'
        creds_path.parent.mkdir(parents=True, exist_ok=True)

        creds = {
            'client_id': os.getenv('GMAIL_CLIENT_ID'),
            'client_secret': os.getenv('GMAIL_CLIENT_SECRET'),
            'refresh_token': tokens['refresh_token'],
            'token_uri': OAUTH_CONFIG['token_uri'],
            'type': 'authorized_user'
        }

        with open(creds_path, 'w') as f:
            json.dump(creds, f, indent=2)

        # Send success response
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        success_message = f"""
        <html>
            <body>
                <h1>Success!</h1>
                <p>Gmail credentials have been saved to: {creds_path}</p>
                <p>You can now close this window and use the credentials in your PyMailAI applications.</p>
            </body>
        </html>
        """
        self.wfile.write(success_message.encode())

        # Signal the main thread to stop
        self.server.should_stop = True

def main():
    """Run the OAuth2 flow to get Gmail credentials."""
    # Check required environment variables
    required_vars = ['GMAIL_CLIENT_ID', 'GMAIL_CLIENT_SECRET']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print("Error: Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        sys.exit(1)

    # Start local server for OAuth callback
    server = HTTPServer(('localhost', 8080), OAuthCallbackHandler)
    server.should_stop = False

    # Build authorization URL
    auth_params = {
        'client_id': os.getenv('GMAIL_CLIENT_ID'),
        'redirect_uri': OAUTH_CONFIG['redirect_uri'],
        'scope': OAUTH_CONFIG['scope'],
        'response_type': OAUTH_CONFIG['response_type'],
        'access_type': OAUTH_CONFIG['access_type'],
        'prompt': OAUTH_CONFIG['prompt']
    }
    auth_url = f"{OAUTH_CONFIG['auth_uri']}?{urlencode(auth_params)}"

    # Open browser for authentication
    print("Opening browser for Gmail authentication...")
    webbrowser.open(auth_url)

    print("Waiting for OAuth callback...")
    while not server.should_stop:
        server.handle_request()

    print("\nSetup complete! You can now use Gmail credentials in your PyMailAI applications.")

if __name__ == "__main__":
    main()
