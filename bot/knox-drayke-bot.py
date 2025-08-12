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
MODE = "check"

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

messages = safe_load_json(os.path.join(base_path, "msg.json"))
media_messages = safe_load_json(os.path.join(base_path, "media_msg.json"))

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

# Send birthday messages
async def send_messages():
    try:
        user = await client.fetch_user(FRIEND_USER_ID)

        # Send text messages
        for msg in messages:
            try:
                await user.send(msg)
                await asyncio.sleep(1) # avoid spamming too fast
            except Exception as e:
                print(f"❌ Failed to send text message: {msg}\n{e}")

        # Send media messages
        for item in media_messages:
            try:
                file_path = os.path.join(base_path, item.get("file", ""))
                if not os.path.isfile(file_path):
                    print(f"❌ File not found: {file_path}")
                    continue

                with open(file_path, "rb") as f:
                    await user.send(content=item.get("text", ""), file=discord.File(f))
                await asyncio.sleep(2)
            except Exception as e:
                print(f"❌ Failed to send media message: {item}\n{e}")

    except Exception as e:
        print(f"⚠️ Error during sending messages: {e}")
        traceback.print_exc()

# Delete old messages
async def delete_old_bot_messages():
    try:
        user = await client.fetch_user(FRIEND_USER_ID)
        dm = await user.create_dm()

        deleted_count = 0
        async for msg in dm.history(limit=6):
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
