from __future__ import annotations

import json
import ssl
import urllib.parse
import urllib.request


def ssl_context() -> ssl.SSLContext | None:
    """Build an SSL context backed by certifi when that package is installed."""
    try:
        import certifi
    except ImportError:
        return None

    return ssl.create_default_context(cafile=certifi.where())


def post_form(url: str, data: dict[str, str]) -> dict:
    """Send form-encoded POST data and parse the JSON response."""
    encoded = urllib.parse.urlencode(data).encode("utf-8")
    request = urllib.request.Request(url, data=encoded, method="POST")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    return send_json_request(request)


def send_json_request(request: urllib.request.Request) -> dict:
    """Execute an HTTP request and return its JSON response body."""
    try:
        with urllib.request.urlopen(request, context=ssl_context()) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Google API request failed: HTTP {error.code}\n{body}") from error
    except urllib.error.URLError as error:
        if "CERTIFICATE_VERIFY_FAILED" in str(error.reason):
            raise SystemExit(
                "HTTPS certificate verification failed. Run:\n"
                "  python3 -m pip install -r requirements.txt\n\n"
                "If you are using the macOS python.org installer, you can also run its "
                "'Install Certificates.command'."
            ) from error
        raise
