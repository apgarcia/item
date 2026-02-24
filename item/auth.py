import google.auth.exceptions
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from .config import CONFIG_DIR

SCOPES = ["https://www.googleapis.com/auth/tasks"]
CREDENTIALS_FILE = CONFIG_DIR / "credentials.json"
TOKEN_FILE = CONFIG_DIR / "token.json"


def get_credentials() -> Credentials:
    """Return valid Google OAuth2 credentials, running the auth flow if needed.

    Expects an OAuth client secrets file at ~/.config/item/credentials.json.
    Download it from Google Cloud Console → APIs & Services → Credentials
    → Create OAuth 2.0 Client ID (Desktop app) → Download JSON.
    """
    creds: Credentials | None = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except google.auth.exceptions.RefreshError:
                creds = None

        if not creds:
            if not CREDENTIALS_FILE.exists():
                raise SystemExit(
                    f"Missing OAuth credentials: {CREDENTIALS_FILE}\n\n"
                    "To set up:\n"
                    "  1. Go to https://console.cloud.google.com/\n"
                    "  2. Create a project and enable the Google Tasks API\n"
                    "  3. Create an OAuth 2.0 Client ID (Desktop app)\n"
                    f"  4. Download the JSON and save it as {CREDENTIALS_FILE}"
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)

        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.write_text(creds.to_json())

    return creds
