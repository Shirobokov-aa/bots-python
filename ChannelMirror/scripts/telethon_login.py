#!/usr/bin/env python3
"""One-shot Telethon login → print StringSession for .env TELEGRAM_SESSION.

Usage (from ChannelMirror/):
  python scripts/telethon_login.py          # phone code (in-app / SMS)
  python scripts/telethon_login.py --qr     # QR: TG → Settings → Devices → Link Desktop
"""

from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

import qrcode
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.sessions import StringSession

QR_PNG = Path(__file__).resolve().parents[1] / "data" / "telethon_qr.png"


def show_qr(url: str) -> None:
    """Draw QR in terminal + PNG. Do NOT open tg:// on phone — scan this."""
    code = qrcode.QRCode(border=1)
    code.add_data(url)
    code.make(fit=True)
    print("\n── QR (scan THIS with phone) ──")
    code.print_ascii(invert=True)
    QR_PNG.parent.mkdir(parents=True, exist_ok=True)
    code.make_image(fill_color="black", back_color="white").save(QR_PNG)
    print(f"Also saved: {QR_PNG}")
    print("Phone: Settings → Devices → Link Desktop Device → camera on THIS screen")
    print("Do NOT open the tg:// link in Telegram — that breaks on many clients.\n")


async def login_qr(client: TelegramClient) -> None:
    await client.connect()
    if await client.is_user_authorized():
        return

    qr = await client.qr_login()
    show_qr(qr.url)

    while True:
        try:
            await qr.wait(timeout=35)
            return
        except asyncio.TimeoutError:
            await qr.recreate()
            print("QR expired — new one:")
            show_qr(qr.url)
        except SessionPasswordNeededError:
            password = input("2FA password: ")
            await client.sign_in(password=password)
            return


async def login_phone(client: TelegramClient) -> None:
    print("Tip: code usually arrives IN Telegram app (chat «Telegram»), not SMS.")
    await client.start()


async def main() -> None:
    parser = argparse.ArgumentParser(description="Telethon StringSession login")
    parser.add_argument(
        "--qr",
        action="store_true",
        help="Login via QR (no SMS / phone code)",
    )
    args = parser.parse_args()

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    api_id = int(os.getenv("TELEGRAM_API_ID") or "0")
    api_hash = os.getenv("TELEGRAM_API_HASH") or ""
    if not api_id or not api_hash:
        raise SystemExit("Set TELEGRAM_API_ID and TELEGRAM_API_HASH in .env first")

    client = TelegramClient(StringSession(), api_id, api_hash)
    if args.qr:
        await login_qr(client)
    else:
        await login_phone(client)

    if not await client.is_user_authorized():
        raise SystemExit("Login failed — not authorized")

    session = client.session.save()
    me = await client.get_me()
    print(f"logged in as @{me.username or me.id}")
    print("Put this into .env:")
    print(f"TELEGRAM_SESSION={session}")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
