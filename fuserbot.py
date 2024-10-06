from telethon import TelegramClient, events
from telethon.sessions import StringSession
import json, asyncio, re, time, logging

# Configure logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')

# Load configuration with error handling
try:
    with open('fuserbot_config.json', 'r') as f:
        config = json.load(f)
except Exception as e:
    logging.error(f"Failed to load configuration: {e}")
    exit(1)

api_id = config['api_id']
api_hash = config['api_hash']
session_string = config['session_string']

# Validate necessary fields
if not all([api_id, api_hash, session_string]):
    logging.error("Missing API credentials in configuration.")
    exit(1)

# Create the Telegram client
client = TelegramClient(StringSession(session_string), api_id, api_hash)

# Store message references to update later if edited
forwarded_messages = {}
lock = asyncio.Lock()  # Create an async lock

async def send_with_retry(destination, message, media=None, retries=3):
    for attempt in range(retries):
        try:
            if media:
                caption = message if message.strip() else "Media attached."
                return await client.send_file(destination, media, caption=caption, link_preview=False)
            else:
                if message.strip():  # Only send the message if it's not empty
                    return await client.send_message(destination, message, link_preview=False)
        except Exception as e:
            logging.error(f"Attempt {attempt + 1}: Failed to send message to {destination}: {e}")
            await asyncio.sleep(0.5)  # Increased wait before retrying
    return None  # Return None if all attempts fail

# Improved log messages for message forwarding
async def process_queue(source_chat, original_message_text, media, destinations, original_message_id):
    original_message_text = re.sub(r'\*+', '', original_message_text).strip()

    for destination in destinations:
        sent_message = await send_with_retry(destination, original_message_text, media=media)
        if sent_message:
            async with lock:
                forwarded_messages[original_message_id] = (sent_message.id, destination, time.time())  # Store timestamp

async def main():
    await client.start()
    logging.warning("Forward started")

    # Clear forwarded messages on startup
    forwarded_messages.clear()

    try:
        with open('chats.json', 'r') as f:
            chat_config = json.load(f)
    except Exception as e:
        logging.error(f"Failed to load chat configuration: {e}")
        return

    @client.on(events.NewMessage(incoming=True))
    async def handler(event):
        source_chat = event.chat_id

        for config in chat_config:
            if str(config["source"]) == str(source_chat):
                destinations = config.get("destination", [])

                original_message_text = event.message.text
                original_message_id = event.message.id

                if event.message.reply_to_msg_id:
                    original_message = await event.get_reply_message()
                    if original_message:
                        original_sender = original_message.sender_id if original_message.sender_id else "Unknown"
                        original_message_text = (
                            f"Replying to {original_sender}: {original_message.text}\n\n{original_message_text}"
                        )
                await process_queue(source_chat, original_message_text, event.message.media, destinations, original_message_id)

    @client.on(events.MessageEdited)
    async def edit_handler(event):
        async with lock:
            if event.message.id in forwarded_messages:
                sent_message_id, destination, _ = forwarded_messages[event.message.id]
                try:
                    original_message_text = event.message.text
                    await client.edit_message(destination, sent_message_id, original_message_text, link_preview=False)
                    forwarded_messages[event.message.id] = (sent_message_id, destination, time.time())
                except Exception as e:
                    logging.error(f"Failed to edit message in {destination}: {e}")

    logging.warning("Listening for new messages...")
    try:
        await client.run_until_disconnected()
    except Exception as e:
        logging.error(f"Error while running the bot: {e}")
    except asyncio.CancelledError:
        logging.warning("Shutting down gracefully...")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped by user.")
        forwarded_messages.clear()  # Clear forwarded messages on shutdown
