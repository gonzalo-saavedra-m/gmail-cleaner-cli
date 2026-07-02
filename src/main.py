#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

from gmail import (
    batch_delete_messages,
    get_access_token,
    get_profile,
    list_matching_message_ids,
    print_refresh_token_help,
)
from libs.env_loader import env, load_dotenv, update_dotenv_value
from libs.secret_store import generate_encryption_key, has_encryption_key, has_refresh_token
from libs.script_utils import DEFAULT_QUERY


def selected_account_label() -> str:
    if not has_refresh_token():
        return "No Gmail account selected"

    try:
        access_token = get_access_token()
        profile = get_profile(access_token)
    except SystemExit as error:
        return f"Encrypted token found, but account could not be verified ({error})"
    except Exception as error:
        return f"Encrypted token found, but account could not be verified ({error})"

    email_address = profile.get("emailAddress")
    if email_address:
        return f"Selected account: {email_address}"

    return "Encrypted token found, but Gmail did not return an email address"


def fetch_and_delete_matching_emails(query: str) -> None:
    if not has_refresh_token():
        print("\nNo encrypted Gmail token found. Choose option 1 first.")
        return

    access_token = get_access_token()
    message_ids = list_matching_message_ids(access_token, query)

    if not message_ids:
        print(f"\nNo messages matched query: {query}")
        return

    print(f"\nMatched {len(message_ids)} messages for query: {query}")

    confirmation = input("Permanently delete these messages? Type y to continue [y/N]: ").strip()
    if confirmation != "y":
        print("Cancelled.")
        return

    batch_delete_messages(access_token, message_ids)
    print("Done.")


def print_menu(query: str) -> None:
    print("\nGmail cleanup")
    print(selected_account_label())
    print(f"Query: {query}")
    print("\n1. Get code from a Gmail account")
    print("2. Fetch emails that match the query")
    print("3. Change query")
    print("4. Exit")


def ensure_encryption_key(env_file: Path) -> None:
    if has_encryption_key():
        return

    update_dotenv_value(env_file, "TOKEN_ENCRYPTION_KEY", generate_encryption_key())
    print("Generated TOKEN_ENCRYPTION_KEY in .env.")


def connect_gmail_account(env_file: Path) -> None:
    ensure_encryption_key(env_file)
    print_refresh_token_help()


def change_query(current_query: str) -> str:
    new_query = input(f"New Gmail query [{current_query}]: ").strip()
    if not new_query:
        print("Query unchanged.")
        return current_query

    print(f"Query changed to: {new_query}")
    return new_query


def run_menu(env_file: Path, query: str) -> None:
    while True:
        print_menu(query)
        choice = input("\nChoose an option [1-4]: ").strip()

        if choice == "4":
            print("Bye.")
            return

        try:
            if choice == "1":
                connect_gmail_account(env_file)
            elif choice == "2":
                fetch_and_delete_matching_emails(query)
            elif choice == "3":
                query = change_query(query)
            else:
                print("Choose 1, 2, 3, or 4.")
        except SystemExit as error:
            print(error)
        except KeyboardInterrupt:
            raise
        except Exception as error:
            print(f"Unexpected error: {error}")


def main() -> None:
    env_file = Path(".env")
    load_dotenv(env_file)
    query = env("DEFAULT_QUERY", required=False, default=DEFAULT_QUERY)

    run_menu(env_file, query)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\nCancelled.")
