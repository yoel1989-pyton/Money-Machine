"""
============================================================
MONEY MACHINE - CREDENTIAL SETUP HELPER
One-Time Setup to Get All Platform IDs & Tokens
============================================================
Run this script to get all the credentials you need.
============================================================
"""

import os
import webbrowser
import json
import asyncio
from urllib.parse import urlencode, parse_qs, urlparse
import http.server
import socketserver
import threading

# ============================================================
# YOUTUBE OAUTH SETUP
# ============================================================

def setup_youtube():
    """
    Step-by-step guide to get YouTube OAuth credentials.
    """
    print("\n" + "="*60)
    print("🎬 YOUTUBE SETUP")
    print("="*60)
    
    print("""
STEP 1: Create a Google Cloud Project
--------------------------------------
1. Go to: https://console.cloud.google.com/
2. Click "Select a project" → "New Project"
3. Name it: "Money Machine"
4. Click "Create"

STEP 2: Enable YouTube Data API v3
----------------------------------
1. Go to: https://console.cloud.google.com/apis/library
2. Search for "YouTube Data API v3"
3. Click it → Click "Enable"

STEP 3: Create OAuth Credentials
--------------------------------
1. Go to: https://console.cloud.google.com/apis/credentials
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure OAuth consent screen:
   - User Type: External
   - App name: "Money Machine"
   - User support email: (your email)
   - Developer contact: (your email)
   - Scopes: Add "youtube.upload" and "youtube.readonly"
   - Test users: Add your YouTube email
4. Back to Credentials → Create OAuth client ID:
   - Application type: "Web application"
   - Name: "Money Machine Uploader"
   - Authorized redirect URIs: http://localhost:8080/callback
5. Click "Create"
6. Copy the Client ID and Client Secret
""")
    
    input("Press Enter when you have your Client ID and Client Secret...")
    
    client_id = input("\nEnter your YouTube Client ID: ").strip()
    client_secret = input("Enter your YouTube Client Secret: ").strip()
    
    if not client_id or not client_secret:
        print("❌ Skipping YouTube setup - no credentials provided")
        return None
    
    # Now get refresh token
    print("\n" + "-"*40)
    print("STEP 4: Get Refresh Token")
    print("-"*40)
    
    # OAuth URL
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode({
        "client_id": client_id,
        "redirect_uri": "http://localhost:8080/callback",
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly",
        "access_type": "offline",
        "prompt": "consent"
    })
    
    print(f"\nOpening browser for authorization...")
    print(f"\nIf browser doesn't open, go to:\n{auth_url}\n")
    
    # Simple callback server
    auth_code = [None]
    
    class CallbackHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            query = parse_qs(urlparse(self.path).query)
            if "code" in query:
                auth_code[0] = query["code"][0]
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>Success! You can close this window.</h1>")
            else:
                self.send_response(400)
                self.end_headers()
        
        def log_message(self, format, *args):
            pass  # Suppress logging
    
    # Start server in background
    server = socketserver.TCPServer(("", 8080), CallbackHandler)
    server_thread = threading.Thread(target=server.handle_request)
    server_thread.start()
    
    # Open browser
    webbrowser.open(auth_url)
    
    print("Waiting for authorization...")
    server_thread.join(timeout=120)
    server.server_close()
    
    if not auth_code[0]:
        print("❌ Authorization timed out or failed")
        return None
    
    # Exchange code for tokens
    import urllib.request
    
    token_data = urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "code": auth_code[0],
        "redirect_uri": "http://localhost:8080/callback",
        "grant_type": "authorization_code"
    }).encode()
    
    try:
        req = urllib.request.Request(
            "https://oauth2.googleapis.com/token",
            data=token_data,
            method="POST"
        )
        with urllib.request.urlopen(req) as response:
            tokens = json.loads(response.read().decode())
            refresh_token = tokens.get("refresh_token")
            
            if refresh_token:
                print("\n✅ YouTube credentials obtained!")
                return {
                    "YOUTUBE_CLIENT_ID": client_id,
                    "YOUTUBE_CLIENT_SECRET": client_secret,
                    "YOUTUBE_REFRESH_TOKEN": refresh_token
                }
    except Exception as e:
        print(f"❌ Error getting tokens: {e}")
    
    return None


# ============================================================
# INSTAGRAM / META SETUP
# ============================================================

def setup_instagram():
    """
    Step-by-step guide to get Instagram Graph API credentials.
    """
    print("\n" + "="*60)
    print("📸 INSTAGRAM SETUP")
    print("="*60)
    
    print("""
PREREQUISITES:
- Instagram Business or Creator account (not personal)
- Facebook Page connected to your Instagram account

STEP 1: Create Meta Developer App
---------------------------------
1. Go to: https://developers.facebook.com/apps/
2. Click "Create App"
3. Select "Business" type
4. App name: "Money Machine"
5. Click "Create App"

STEP 2: Add Instagram Graph API
-------------------------------
1. In your app dashboard, find "Add Products"
2. Find "Instagram Graph API" → Click "Set Up"
3. Go to Settings → Basic
4. Copy your App ID and App Secret

STEP 3: Get Access Token
------------------------
1. Go to: https://developers.facebook.com/tools/explorer/
2. Select your app from dropdown
3. Click "Generate Access Token"
4. Select permissions:
   - instagram_basic
   - instagram_content_publish
   - pages_read_engagement
   - pages_show_list
5. Click "Generate Access Token"
6. Authorize with your Facebook account

STEP 4: Get Instagram User ID
-----------------------------
1. In Graph API Explorer, make this call:
   GET /me/accounts
2. Find your Facebook Page, copy the 'id'
3. Then call: GET /{page-id}?fields=instagram_business_account
4. Copy the instagram_business_account.id

STEP 5: Extend Token (IMPORTANT!)
---------------------------------
Short-lived tokens expire in 1 hour.
1. Go to: https://developers.facebook.com/tools/debug/accesstoken/
2. Paste your token → Debug
3. Click "Extend Access Token"
4. Copy the new long-lived token (60 days)

For permanent token, set up token refresh in the system.
""")
    
    input("\nPress Enter when ready to enter credentials...")
    
    app_id = input("\nEnter Meta App ID: ").strip()
    app_secret = input("Enter Meta App Secret: ").strip()
    access_token = input("Enter Access Token (long-lived): ").strip()
    user_id = input("Enter Instagram Business Account ID: ").strip()
    
    if not all([app_id, access_token, user_id]):
        print("❌ Skipping Instagram setup - missing credentials")
        return None
    
    print("\n✅ Instagram credentials obtained!")
    return {
        "IG_APP_ID": app_id,
        "IG_APP_SECRET": app_secret,
        "IG_ACCESS_TOKEN": access_token,
        "IG_USER_ID": user_id
    }


# ============================================================
# TIKTOK SETUP
# ============================================================

def setup_tiktok():
    """
    Step-by-step guide to get TikTok Content Posting API credentials.
    """
    print("\n" + "="*60)
    print("🎵 TIKTOK SETUP")
    print("="*60)
    
    print("""
NOTE: TikTok Content Posting API pushes videos as DRAFTS.
You tap "Post" once in the TikTok app. This is compliant.

STEP 1: Create TikTok Developer App
-----------------------------------
1. Go to: https://developers.tiktok.com/
2. Click "Manage apps" → "Connect an app"
3. App name: "Money Machine"
4. Category: "Content Creation"
5. Platform: Web

STEP 2: Configure App
---------------------
1. Add these scopes:
   - video.publish (for posting)
   - video.upload (for uploading)
2. Add redirect URI: http://localhost:8080/callback
3. Submit for review (may take 1-3 days)

STEP 3: Get Access Token
------------------------
Once approved:
1. Go to your app → "Sandbox/Test Users"
2. Add your TikTok account as test user
3. Use OAuth to get access token

Authorization URL format:
https://www.tiktok.com/v2/auth/authorize/?
  client_key=YOUR_CLIENT_KEY&
  scope=video.publish,video.upload&
  response_type=code&
  redirect_uri=http://localhost:8080/callback

STEP 4: Get Open ID
-------------------
After authorization, call:
GET https://open.tiktokapis.com/v2/user/info/
Headers: Authorization: Bearer YOUR_ACCESS_TOKEN

The response contains your open_id.
""")
    
    input("\nPress Enter when ready to enter credentials...")
    
    client_key = input("\nEnter TikTok Client Key: ").strip()
    client_secret = input("Enter TikTok Client Secret: ").strip()
    access_token = input("Enter Access Token: ").strip()
    open_id = input("Enter Open ID: ").strip()
    
    if not access_token:
        print("❌ Skipping TikTok setup - no access token")
        return None
    
    print("\n✅ TikTok credentials obtained!")
    return {
        "TIKTOK_CLIENT_KEY": client_key,
        "TIKTOK_CLIENT_SECRET": client_secret,
        "TIKTOK_ACCESS_TOKEN": access_token,
        "TIKTOK_OPEN_ID": open_id
    }


# ============================================================
# TELEGRAM SETUP (for notifications)
# ============================================================

def setup_telegram():
    """
    Get Telegram Chat ID for notifications.
    """
    print("\n" + "="*60)
    print("📱 TELEGRAM CHAT ID SETUP")
    print("="*60)
    
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "8592641897:AAHvqPbO7eCrRJAQ4mX519kjl478ISGfMM4")
    
    print(f"""
You already have a bot token configured.

To get your Chat ID:
1. Open Telegram
2. Search for your bot: @MoneyMachineBot (or whatever you named it)
3. Send it a message: /start
4. Open this URL in your browser:
   https://api.telegram.org/bot{bot_token}/getUpdates
5. Find "chat": {{"id": YOUR_CHAT_ID}}
6. Copy that number (including the minus if negative)
""")
    
    chat_id = input("\nEnter your Telegram Chat ID: ").strip()
    
    if not chat_id:
        print("❌ Skipping Telegram setup")
        return None
    
    print("\n✅ Telegram Chat ID obtained!")
    return {"TELEGRAM_CHAT_ID": chat_id}


# ============================================================
# MAIN SETUP RUNNER
# ============================================================

def update_env_file(credentials: dict):
    """Update .env file with new credentials."""
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    
    # Read existing .env
    env_lines = []
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            env_lines = f.readlines()
    
    # Update or add each credential
    for key, value in credentials.items():
        if not value:
            continue
            
        # Find and replace existing line
        found = False
        for i, line in enumerate(env_lines):
            if line.startswith(f"{key}="):
                env_lines[i] = f"{key}={value}\n"
                found = True
                break
        
        # Add if not found
        if not found:
            env_lines.append(f"{key}={value}\n")
    
    # Write back
    with open(env_path, "w") as f:
        f.writelines(env_lines)
    
    print(f"\n✅ Updated {env_path}")


def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║         MONEY MACHINE - CREDENTIAL SETUP                 ║
║         One-Time Platform Configuration                  ║
╚══════════════════════════════════════════════════════════╝

This script will help you obtain all the API credentials
needed for automated uploads.

Platforms:
  🎬 YouTube   - Full auto-upload (OAuth)
  📸 Instagram - Full auto-upload (Meta Graph API)
  🎵 TikTok    - Draft push (tap Post in app)
  📱 Telegram  - Notifications (optional)

""")
    
    all_credentials = {}
    
    # YouTube
    choice = input("Set up YouTube? (Y/n): ").strip().lower()
    if choice != "n":
        yt_creds = setup_youtube()
        if yt_creds:
            all_credentials.update(yt_creds)
    
    # Instagram
    choice = input("\nSet up Instagram? (Y/n): ").strip().lower()
    if choice != "n":
        ig_creds = setup_instagram()
        if ig_creds:
            all_credentials.update(ig_creds)
    
    # TikTok
    choice = input("\nSet up TikTok? (Y/n): ").strip().lower()
    if choice != "n":
        tt_creds = setup_tiktok()
        if tt_creds:
            all_credentials.update(tt_creds)
    
    # Telegram
    choice = input("\nSet up Telegram notifications? (Y/n): ").strip().lower()
    if choice != "n":
        tg_creds = setup_telegram()
        if tg_creds:
            all_credentials.update(tg_creds)
    
    # Summary
    print("\n" + "="*60)
    print("📋 CREDENTIAL SUMMARY")
    print("="*60)
    
    if all_credentials:
        for key, value in all_credentials.items():
            masked = value[:8] + "..." if len(value) > 12 else value
            print(f"  {key}={masked}")
        
        # Save to .env
        choice = input("\n\nSave to .env file? (Y/n): ").strip().lower()
        if choice != "n":
            update_env_file(all_credentials)
        
        # Also print for Railway
        print("\n" + "="*60)
        print("🚂 FOR RAILWAY DEPLOYMENT")
        print("="*60)
        print("\nAdd these as environment variables in Railway:\n")
        for key, value in all_credentials.items():
            print(f"{key}={value}")
    else:
        print("No credentials configured.")
    
    print("\n" + "="*60)
    print("✅ SETUP COMPLETE")
    print("="*60)
    print("""
Next steps:
1. Run: python run.py --continuous --no-confirm
2. The machine handles everything else
3. Collect money

The machine runs. You collect. 💰
""")


if __name__ == "__main__":
    main()
