import nest_asyncio
nest_asyncio.apply()

import discord
import asyncio
import pendulum
from dotenv import load_dotenv
import os
import json
import traceback
import random

load_dotenv()

TOKEN = os.getenv("Knox_Drayke")
FRIEND_USER_ID = 1029977851463745577

# Choose what the bot should do: "check" or "send" or "delete"
MODE = "send"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)

BOT_NAME = "knox-drayke"

script_dir = os.path.dirname(os.path.abspath(__file__))
base_path = os.path.join(script_dir, "..", "messages", BOT_NAME)


# Safe loading of messages
def safe_load_json(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON error in {file_path}: {e}")
    except Exception as e:
        print(f"⚠️ Failed to load {file_path}: {e}")
    return []

messages = safe_load_json(os.path.join(base_path, "message.json"))


# Check if DMs are open
async def check_dms():
    try:
        user = await client.fetch_user(FRIEND_USER_ID)
        test_msg = await user.send("🧪 Test message to check if DMs are open (will delete in 7 seconds)...")
        await asyncio.sleep(7)
        await test_msg.delete()
        print("✅ DMs are OPEN! You can send the messages later.")
    except discord.Forbidden:
        print("❌ DMs are closed. Cannot message this user.")
    except Exception as e:
        print(f"⚠️ Error during DM check: {e}")
        traceback.print_exc()
        
PROGRESS_FILE = "progress.json"

# Load progress
def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f).get("last_index", 0)
    return 0

# Save progress
def save_progress(index):
    with open(PROGRESS_FILE, "w") as f:
        json.dump({"last_index": index}, f)
        
LAST_SENT_FILE = "last_sent.json"

def load_last_sent():
    if os.path.exists(LAST_SENT_FILE):
        with open(LAST_SENT_FILE, "r") as f:
            return json.load(f).get("date")
    return None

def save_last_sent(date):
    with open(LAST_SENT_FILE, "w") as f:
        json.dump({"date": date}, f)
        
MAX_LENGTH = 2000

def split_message(message):
    """Split message into chunks under Discord's 2000 char limit."""
    return [message[i:i+MAX_LENGTH] for i in range(0, len(message), MAX_LENGTH)]

# Send birthday messages
async def send_messages():
    try:
        user = await client.fetch_user(FRIEND_USER_ID)

        last_index = load_progress()

        for i, msg in enumerate(messages[last_index:], start=last_index):

            try:
                msg_type = msg.get("type")

                # =========================
                # TEXT MESSAGE
                # =========================
                if msg_type == "text":

                    for part in split_message(msg.get("content", "")):
                        await user.send(part)
                        await asyncio.sleep(random.randint(2, 5))

                # =========================
                # SINGLE MEDIA
                # =========================
                elif msg_type == "media":

                    file_path = os.path.join(base_path, msg.get("file", ""))

                    if not os.path.isfile(file_path):
                        print(f"❌ File not found: {file_path}")
                        continue

                    caption = msg.get("caption", "")

                    with open(file_path, "rb") as f:
                        await user.send(
                            content=caption,
                            file=discord.File(f)
                        )

                    await asyncio.sleep(random.randint(3, 7))

                # =========================
                # MULTIPLE MEDIA GROUP
                # =========================
                elif msg_type == "media_group":

                    files = msg.get("files", [])

                    for media in files:

                        file_name = media.get("name")
                        caption = media.get("caption", "")

                        file_path = os.path.join(base_path, file_name)

                        if not os.path.isfile(file_path):
                            print(f"❌ File not found: {file_path}")
                            continue

                        with open(file_path, "rb") as f:
                            await user.send(
                                content=caption,
                                file=discord.File(f)
                            )

                        # small delay between uploads
                        await asyncio.sleep(random.randint(4, 8))

                # =========================
                # DELAY
                # =========================
                elif msg_type == "delay":

                    min_time = msg.get("min", 60)
                    max_time = msg.get("max", 120)

                    wait_time = random.randint(min_time, max_time)

                    print(f"⏳ Waiting {wait_time} seconds...")

                    await asyncio.sleep(wait_time)

                # =========================
                # LINK
                # =========================
                elif msg_type == "link":

                    text = msg.get("text", "")
                    url = msg.get("url", "")

                    await user.send(f"{text}\n{url}")

                    await asyncio.sleep(random.randint(2, 5))

                # save progress AFTER success
                save_progress(i + 1)

            except Exception as e:
                print(f"❌ Failed at index {i}")
                print(f"Message data: {msg}")
                print(e)

    except Exception as e:
        print(f"⚠️ Error during sending messages: {e}")
        traceback.print_exc()

# Delete old messages
async def delete_old_bot_messages():
    try:
        user = await client.fetch_user(FRIEND_USER_ID)
        dm = await user.create_dm()

        deleted_count = 0
        async for msg in dm.history(limit=96):
            if msg.author == client.user:
                try:
                    await msg.delete()
                    deleted_count += 1
                    await asyncio.sleep(1)
                except Exception as e:
                    print(f"⚠️ Failed to delete message: {e}")

        print(f"✅ Deleted {deleted_count} old messages sent by the bot.")
    except Exception as e:
        print(f"⚠️ Error during message deletion: {e}")
        traceback.print_exc()
        

@client.event
async def on_ready():
    print(f"🔗 Logged in as {client.user}")

    try:
        if MODE == "check":
            await check_dms()

        elif MODE == "send":
            timezone = pendulum.timezone("Asia/Karachi")
            now = pendulum.now(timezone)
            
            # Target date: Update this dynamically or structurally if needed 
            target_time = pendulum.datetime(2026, 5, 24, 0, 0, 0, tz=timezone)
            
            # Calculate remaining time safely
            wait_time = (target_time - now).total_seconds()

            if wait_time > 0:
                print(f"⌛ Waiting {wait_time / 60:.2f} minutes until birthday message is sent...")
                await asyncio.sleep(wait_time)
                
            today = pendulum.now(timezone).to_date_string()
            last_sent = load_last_sent()
            
            if last_sent == today:
                print("🛑 Messages already sent today. Exiting safely.")
                await client.close()
                return

            print("🎉 Time reached! Sending messages...")
            await send_messages()
            save_last_sent(today)
            
            # Reset progress after successful completion
            save_progress(0)
            print("✅ All messages have been sent successfully! 💯")

        elif MODE == "delete":
            await delete_old_bot_messages()

    except Exception as e:
        print(f"❌ An unexpected error occurred in on_ready: {e}")
        traceback.print_exc()

    await client.close()
client.run(TOKEN)