import asyncio
import os
import json
from urllib.parse import unquote
from typing import List
from pyrogram import Client
from pyrogram.errors import (
    AuthKeyUnregistered,
    FloodWait,
    Unauthorized,
    UserDeactivated,
)
from pyrogram.raw.functions.messages import RequestWebView
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_ID = os.getenv('API_ID')  # Fetch from .env file
API_HASH = os.getenv('API_HASH')  # Fetch from .env file
SESSIONS_DIR = 'sessions/'  # Directory to store session files
BOT_INFO_FILE = 'bot_information.json'  # File containing bot information
DELAY = 5  # Delay between each request in seconds

banner = """
  banner = """
  __                .__                ___.                              
_/  |_  ____ ______ |  |   ____   _____\_ |__   ____   ____  ___________ 
\   __\/  _ \\____ \|  | _/ __ \ /  ___/| __ \ /  _ \_/ ___\/  _ \_  __ \
 |  | (  <_> )  |_> >  |_\  ___/ \___ \ | \_\ (  <_> )  \__(  <_> )  | \/
 |__|  \____/|   __/|____/\___  >____  >|___  /\____/ \___  >____/|__|   
             |__|             \/     \/     \/            \/                

Telegram Channel: https://t.me/JCAirdrops
Telegram Group: https://t.me/jcairdropdiskusi
"""

options = """
Select an action:

    1. Create session
    2. Run bot
"""

async def get_tg_web_data(tg_client: Client, session_name: str, bot_username: str, url: str) -> str:
    try:
        if not tg_client.is_connected:
            try:
                await tg_client.connect()
            except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
                print(f"Invalid session: {session_name}")
                return None

        web_view = await tg_client.invoke(
            RequestWebView(
                peer=await tg_client.resolve_peer(bot_username),
                bot=await tg_client.resolve_peer(bot_username),
                platform='android',
                from_bot_menu=False,
                url=url
            )
        )

        auth_url = web_view.url
        tg_web_data = unquote(
            string=auth_url.split('tgWebAppData=', maxsplit=1)[1].split('&tgWebAppVersion', maxsplit=1)[0])

        if tg_client.is_connected:
            await tg_client.disconnect()

        return tg_web_data

    except Exception as error:
        print(f"{session_name} | Error while getting Tg Web Data: {error}")
        await asyncio.sleep(3)
        return None


def read_bot_info(file_path: str) -> List[dict]:
    with open(file_path, 'r') as file:
        return json.load(file)['bots']


async def process_session(session_file: str, bot_usernames: List[str], web_bot_urls: List[str]):
    session_name = os.path.splitext(os.path.basename(session_file))[0]
    tg_client = Client(os.path.join(SESSIONS_DIR, session_name), api_id=API_ID, api_hash=API_HASH)

    for bot_username, url in zip(bot_usernames, web_bot_urls):
        tg_web_data = await get_tg_web_data(tg_client, session_name, bot_username, url)
        if tg_web_data:
            # Save tg_web_data to a file
            with open(f"{bot_username}_token.txt", 'a') as file:
                file.write(f"{tg_web_data}\n")

            # Print the data to the terminal
            print(f"Username: {session_name}, tg_web_data: {tg_web_data}")
        else:
            print(f"Failed to retrieve tg_web_data for {bot_username}")

        await asyncio.sleep(DELAY)


async def main():
    # Ensure the sessions directory exists
    if not os.path.exists(SESSIONS_DIR):
        os.makedirs(SESSIONS_DIR)

    print(banner)
    print(options)

    choice = input("Enter your choice (1/2): ").strip()

    bot_info = read_bot_info(BOT_INFO_FILE)
    bot_usernames = [bot['username'] for bot in bot_info]
    web_bot_urls = [bot['url'] for bot in bot_info]

    if choice == '1':
        phone_number = input("Enter your phone number (with country code): ").strip()
        session_name = input("Enter a name for the new session: ").strip()
        tg_client = Client(os.path.join(SESSIONS_DIR, session_name), api_id=API_ID, api_hash=API_HASH, phone_number=phone_number)
        await tg_client.start()
        print(f"New session '{session_name}' created and logged in.")
        await tg_client.stop()
    elif choice == '2':
        print("Available bots:")
        for i, bot_username in enumerate(bot_usernames, start=1):
            print(f"{i}. {bot_username}")

        bot_choice = int(input("Select a bot by number: ").strip()) - 1
        selected_bot_usernames = [bot_usernames[bot_choice]]
        selected_web_bot_urls = [web_bot_urls[bot_choice]]

        session_files = [os.path.join(SESSIONS_DIR, f) for f in os.listdir(SESSIONS_DIR) if f.endswith('.session')]
        for session_file in session_files:
            await process_session(session_file, selected_bot_usernames, selected_web_bot_urls)
    else:
        print("Invalid choice. Please enter '1' or '2'.")

if __name__ == '__main__':
    asyncio.run(main())
