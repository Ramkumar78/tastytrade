import requests
import os
import urllib.parse
from dotenv import load_dotenv

# Load existing env vars to pre-fill prompts
load_dotenv()

def get_input(prompt, default=None):
    if default:
        user_input = input(f"{prompt} [{default}]: ")
        return user_input.strip() or default
    return input(f"{prompt}: ").strip()

def main():
    print("--- Tastytrade Refresh Token Generator ---")
    print("This script helps you obtain a Refresh Token for your .env file.")
    print("You need your App's Client ID, Client Secret, and Redirect URI.")
    print("If you haven't created an App yet, visit https://developer.tastyworks.com/\n")

    # Try to pick up ID from TT_CLIENT_ID or TT_REFRESH_TOKEN (if user put ID there)
    default_id = os.getenv("TT_CLIENT_ID") or os.getenv("TT_REFRESH_TOKEN")
    # If default_id looks like a JWT, it's not a client ID.
    if default_id and "." in default_id:
        default_id = None

    client_id = get_input("Client ID", default_id)
    client_secret = get_input("Client Secret", os.getenv("TT_SECRET"))
    redirect_uri = get_input("Redirect URI", "http://localhost:3000")

    # Step 1: Authorization URL
    base_url = "https://api.tastyworks.com/oauth/authorize"
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri
    }

    auth_url = f"{base_url}?{urllib.parse.urlencode(params)}"

    print(f"\n1. Open this URL in your browser:\n\n{auth_url}\n")
    print("2. Login and approve the application.")
    print(f"3. You will be redirected to {redirect_uri} with a '?code=...' parameter.")

    code = get_input("Paste the full Redirect URL or just the code value")

    # Extract code if URL is pasted
    if "code=" in code:
        parsed = urllib.parse.urlparse(code)
        qs = urllib.parse.parse_qs(parsed.query)
        code = qs.get("code", [None])[0]

    if not code:
        print("Error: Could not extract code.")
        return

    # Step 2: Exchange for Token
    print("\nExchanging code for Refresh Token...")
    token_url = "https://api.tastyworks.com/oauth/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri
    }

    try:
        response = requests.post(token_url, json=payload)
        data = response.json()

        if response.status_code == 200:
            refresh_token = data.get("refresh_token")
            print("\nSUCCESS! Here is your Refresh Token:\n")
            print(f"{refresh_token}\n")
            print("Update your .env file:")
            print(f"TT_REFRESH_TOKEN={refresh_token}")
        else:
            print(f"\nError exchanging code: {response.status_code}")
            print(data)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
