from __future__ import annotations

import argparse
import os
from getpass import getpass

from app.security import encrypt_text
from app.storage import init_storage, save_ai_settings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Save AI API key into data/settings.json"
    )
    parser.add_argument(
        "--provider", default="gemini", help="Provider name (default: gemini)"
    )
    parser.add_argument(
        "--model",
        default="gemini-2.5-flash",
        help="Model name (default: gemini-2.5-flash)",
    )
    parser.add_argument(
        "--api-key", dest="api_key", default=None, help="API key (optional)"
    )
    args = parser.parse_args()

    api_key = args.api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        api_key = getpass("Enter API key: ")
    if not api_key:
        print("[set_api_key] API key is empty; abort.")
        return 1

    app_secret = os.getenv("APP_SECRET")
    if not app_secret:
        print(
            "[set_api_key] Warning: APP_SECRET is not set. The key will be stored in plain text."
        )

    enc = encrypt_text(api_key, app_secret)
    init_storage()
    save_ai_settings(args.provider, args.model, enc)
    print("[set_api_key] Saved to data/settings.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
