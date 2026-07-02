from __future__ import annotations

import http.server
import json
import socketserver
import threading
import urllib.parse
import urllib.request
import webbrowser

from libs.env_loader import env
from libs.http_utils import post_form, send_json_request
from libs.secret_store import load_refresh_token, save_refresh_token
from libs.script_utils import chunks


GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GMAIL_DELETE_SCOPE = "https://mail.google.com/"
BATCH_DELETE_LIMIT = 1000
DEFAULT_REDIRECT_URI = "http://127.0.0.1:8765/callback"


class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    auth_code = ""
    auth_error = ""

    def do_GET(self) -> None:
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        OAuthCallbackHandler.auth_code = params.get("code", [""])[0]
        OAuthCallbackHandler.auth_error = params.get("error", [""])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()

        if OAuthCallbackHandler.auth_code:
            self.wfile.write(b"Authorization received. You can close this tab.")
        else:
            self.wfile.write(b"No authorization code found. Return to the terminal.")

    def log_message(self, format: str, *args: object) -> None:
        return


def get_access_token() -> str:
    response = post_form(
        GOOGLE_TOKEN_URL,
        {
            "client_id": env("GOOGLE_CLIENT_ID"),
            "client_secret": env("GOOGLE_CLIENT_SECRET"),
            "refresh_token": load_refresh_token(),
            "grant_type": "refresh_token",
        },
    )
    return response["access_token"]


def gmail_request(access_token: str, method: str, path: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(f"{GMAIL_API_BASE}{path}", data=data, method=method)
    request.add_header("Authorization", f"Bearer {access_token}")
    request.add_header("Accept", "application/json")

    if body is not None:
        request.add_header("Content-Type", "application/json")

    return send_json_request(request)


def get_profile(access_token: str) -> dict:
    return gmail_request(access_token, "GET", "/users/me/profile")


def list_matching_message_ids(access_token: str, query: str) -> list[str]:
    message_ids: list[str] = []
    page_token = ""

    while True:
        params = {"q": query, "maxResults": "500"}
        if page_token:
            params["pageToken"] = page_token

        response = gmail_request(
            access_token,
            "GET",
            f"/users/me/messages?{urllib.parse.urlencode(params)}",
        )
        message_ids.extend(message["id"] for message in response.get("messages", []))

        page_token = response.get("nextPageToken", "")
        if not page_token:
            return message_ids


def batch_delete_messages(access_token: str, message_ids: list[str]) -> None:
    for batch in chunks(message_ids, BATCH_DELETE_LIMIT):
        gmail_request(access_token, "POST", "/users/me/messages/batchDelete", {"ids": batch})
        print(f"Deleted {len(batch)} messages")


def extract_authorization_code(raw_value: str) -> str:
    value = raw_value.strip()
    parsed = urllib.parse.urlparse(value)

    if parsed.query:
        params = urllib.parse.parse_qs(parsed.query)
        if params.get("code"):
            return params["code"][0]

    if value.startswith("code="):
        return urllib.parse.parse_qs(value)["code"][0]

    if "&code=" in value:
        params = urllib.parse.parse_qs(value.lstrip("&"))
        if params.get("code"):
            return params["code"][0]

    return value


def build_authorization_url(redirect_uri: str) -> str:
    client_id = env("GOOGLE_CLIENT_ID")
    auth_params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": GMAIL_DELETE_SCOPE,
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(auth_params)}"


def get_authorization_code_manually(redirect_uri: str) -> str:
    auth_url = build_authorization_url(redirect_uri)

    print("Open this URL, approve access, then paste either the full redirect URL or just the code below:\n")
    print(auth_url)
    return extract_authorization_code(input("\nAuthorization code or redirect URL: "))


def get_authorization_code_from_callback(redirect_uri: str) -> str:
    parsed_redirect = urllib.parse.urlparse(redirect_uri)
    host = parsed_redirect.hostname or "127.0.0.1"
    port = parsed_redirect.port

    if port is None:
        raise SystemExit(
            "GOOGLE_REDIRECT_URI must include a port for automatic callback capture.\n"
            f"Use {DEFAULT_REDIRECT_URI} in .env, then run this command again."
        )

    OAuthCallbackHandler.auth_code = ""
    OAuthCallbackHandler.auth_error = ""
    auth_url = build_authorization_url(redirect_uri)

    with socketserver.TCPServer((host, port), OAuthCallbackHandler) as server:
        print("Opening Google authorization in your browser...")
        print(auth_url)
        webbrowser.open(auth_url)

        thread = threading.Thread(target=server.handle_request)
        thread.start()
        thread.join(timeout=180)

    if OAuthCallbackHandler.auth_error:
        raise SystemExit(f"Google authorization failed: {OAuthCallbackHandler.auth_error}")

    if not OAuthCallbackHandler.auth_code:
        raise SystemExit("No authorization code received before timeout.")

    return OAuthCallbackHandler.auth_code


def print_refresh_token_help() -> None:
    client_id = env("GOOGLE_CLIENT_ID")
    client_secret = env("GOOGLE_CLIENT_SECRET")
    redirect_uri = env("GOOGLE_REDIRECT_URI", default=DEFAULT_REDIRECT_URI)

    code = get_authorization_code_from_callback(redirect_uri)

    response = post_form(
        GOOGLE_TOKEN_URL,
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        },
    )

    refresh_token = response["refresh_token"]
    token_path = save_refresh_token(refresh_token)

    print(f"\nSaved encrypted refresh token to {token_path}.")
