import nest_asyncio
nest_asyncio.apply()

import discord
import asyncio
import pendulum
from dotenv import load_dotenv
import os
import json
import traceback

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
        print("✅ DMs are OPEN! You can send the birthday messages later.")
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
                save_progress(i + 1)  # ✅ progress saved BEFORE sending to avoid repeats
                
                if msg.get("type") == "text":
                    for part in split_message(msg["content"]):
                        await user.send(part)
                        await asyncio.sleep(1)

                elif msg.get("type") == "media":
                    file_path = os.path.join(base_path, msg.get("file", ""))
                    if not os.path.isfile(file_path):
                        print(f"❌ File not found: {file_path}")
                        continue
                    with open(file_path, "rb") as f:
                        await user.send(content=msg.get("text", ""), file=discord.File(f))
                    await asyncio.sleep(2)

                save_progress(i + 1)  # ✅ progress saved AFTER success, so it resumes at next index
            except Exception as e:
                print(f"❌ Failed to send message: {msg}\n{e}")
                
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
            target_time = pendulum.datetime(2025, 5, 21, 16, 5, 0, tz=timezone)
            wait_time = (target_time - now).total_seconds()

            if wait_time > 0:
                print(f"⌛ Waiting {wait_time / 60:.2f} minutes until birthday message is sent...")
                await asyncio.sleep(wait_time)

            print("🎉 Time reached! Sending birthday messages...")
            await send_messages()
            print("✅ All messages have been sent successfully! 💯")

        elif MODE == "delete":
            await delete_old_bot_messages()

    except Exception as e:
        print(f"❌ An unexpected error occurred in on_ready: {e}")
        traceback.print_exc()

    await client.close()

try:
    client.run(TOKEN)
except Exception as e:
    print(f"❌ Failed to run the Discord bot: {e}")
    traceback.print_exc()
