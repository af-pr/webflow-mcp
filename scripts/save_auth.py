"""
Save browser authentication session to auth/{name}.json

Usage:
    python scripts/save_auth.py --url https://example.com --name example

The script opens a visible browser window and navigates to the given URL.
Log in manually, then press Enter in the terminal to save the session.
The saved session can be referenced in workflow YAML files via the `auth` field.
"""

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright

AUTH_DIR = Path(__file__).parent.parent / "auth"


def save_auth(url: str, name: str) -> None:
    """Open a browser for manual login and save the resulting session.

    Args:
        url: URL to navigate to for login
        name: Name for the auth file (saved as auth/{name}.json)
    """
    auth_path = AUTH_DIR / f"{name}.json"
    AUTH_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(url)

        while True:
            input(
                f"\nComplete login in the browser window, then press Enter to save session..."
            )
            cookies = context.cookies()
            if cookies:
                context.storage_state(path=str(auth_path))
                print(f"Session saved to {auth_path}")
                break
            else:
                print("No cookies found — login may be incomplete.")
                retry = input("Retry? [y/N]: ")
                if retry.strip().lower() != "y":
                    print("Aborted. No session was saved.")
                    break

        browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Save a browser session for webflow-mcp authentication"
    )
    parser.add_argument(
        "--url",
        required=True,
        help="URL to navigate to for login (e.g. https://example.com)",
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Name for the auth file (e.g. 'example' → auth/example.json)",
    )
    args = parser.parse_args()
    save_auth(args.url, args.name)


if __name__ == "__main__":
    main()
