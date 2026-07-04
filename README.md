# Gmail Cleanup CLI

Small Python CLI for finding Gmail messages that match a Gmail search query and permanently deleting them after an explicit confirmation.

The default query is:

```text
is:unread older_than:6m
```

You can change the active query from the CLI menu during a run. That change is kept in memory only. The startup default lives in `.env` as `DEFAULT_QUERY`.

## What It Does

The CLI opens a simple menu:

```text
1. Get code from a Gmail account
2. Fetch emails that match the query
3. Change query
4. Exit
```

Option `1` connects a Gmail account through Google OAuth. The app stores the Gmail refresh token encrypted in `.secrets/google_refresh_token.enc`.

Option `2` searches Gmail with the current query, prints how many messages matched, and asks for confirmation before deleting anything.

Deletion only happens if you type exactly:

```text
y
```

Anything else cancels the deletion.

Important: this app uses Gmail `batchDelete`, so deleted emails are permanently removed rather than moved to Trash.

## Local Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Create your local `.env`:

```bash
cp .env.template .env
```

Then fill in:

```env
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
```

Leave these as-is unless you intentionally want different values:

```env
DEFAULT_QUERY=is:unread older_than:6m
GOOGLE_REFRESH_TOKEN_FILE=.secrets/google_refresh_token.enc
TOKEN_ENCRYPTION_KEY=your-generated-encryption-key
GOOGLE_REDIRECT_URI=http://127.0.0.1:8765/callback
```

`TOKEN_ENCRYPTION_KEY` is generated automatically the first time you connect a Gmail account from the menu.

Run the app:

```bash
python3 src/main.py
```

## Google Console Setup

Google requires OAuth for Gmail access. A plain API key is not enough because this app reads and deletes user mailbox data.

Official references:

- Gmail API Python quickstart: https://developers.google.com/workspace/gmail/api/quickstart/python
- OAuth consent configuration: https://developers.google.com/workspace/guides/configure-oauth-consent

### 1. Create Or Select A Google Cloud Project

Open Google Cloud Console:

https://console.cloud.google.com/

Create a project for this app, for example:

```text
Personal Gmail Cleanup
```

The project is only the OAuth app container. The actual Gmail account is selected later when the browser asks you to sign in.

### 2. Enable The Gmail API

In Google Cloud Console:

```text
APIs & Services -> Library -> Gmail API -> Enable
```

### 3. Configure OAuth Consent

In Google Cloud Console:

```text
Google Auth platform -> Branding
```

Configure the app name, support email, and contact email.

For a personal Gmail account, use an external/testing setup and add your own Gmail address as a test user if Google asks for test users.

### 4. Create OAuth Client Credentials

In Google Cloud Console:

```text
Google Auth platform -> Clients -> Create Client
```

Choose:

```text
Application type: Desktop app
```

Copy the generated client ID and client secret into `.env`:

```env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
```

### 5. Connect Your Gmail Account

Run:

```bash
python3 src/main.py
```

Choose:

```text
1. Get code from a Gmail account
```

The app opens a Google authorization page. Select the Gmail account you want to clean up and approve access.

After approval, the local callback receives the OAuth code, exchanges it for a refresh token, encrypts that token, and stores it at:

```text
.secrets/google_refresh_token.enc
```

The encrypted token file and `.env` are ignored by Git.

## Changing The Query

Choose:

```text
3. Change query
```

Examples:

```text
is:unread older_than:6m
from:newsletter@example.com older_than:1y
category:promotions older_than:6m
```

The changed query is used until you exit the program. It is not written back to `.env`.

To change the startup default, edit `DEFAULT_QUERY` in `.env`.

## Safety Checklist

Before confirming deletion:

- Check the printed query.
- Check the number of matched messages.
- Only type `y` if you really want permanent deletion.

If you are unsure, press Enter to cancel.
