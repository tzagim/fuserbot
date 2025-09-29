from telethon import TelegramClient, events
from telethon.sessions import StringSession
import json, asyncio, re, time, logging

# Configure logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger('telethon').setLevel(logging.WARNING)

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
lock = asyncio.Lock()


async def send_with_retry(destination, message, media=None, retries=3):
    for attempt in range(retries):
        try:
            if media:
                caption = message if message.strip() else "Media attached."
                return await client.send_file(destination, media, caption=caption, link_preview=False)
            else:
                if message.strip():
                    return await client.send_message(destination, message, link_preview=False)
        except Exception as e:
            logging.error(f"Attempt {attempt + 1}: Failed to send message to {destination}: {e}")
            await asyncio.sleep(0.5)
    return None


# Improved log messages for message forwarding
async def process_queue(original_message_text, media, destinations, original_message_id):
    original_message_text = re.sub(r'\*+', '', original_message_text).strip()

    for destination in destinations:
        sent_message = await send_with_retry(destination, original_message_text, media=media)
        if sent_message:
            async with lock:
                forwarded_messages[original_message_id] = (sent_message.id, destination, time.time())

def passes_filters(text, filters):
    text = text or ""
    required = filters.get("required", [])
    any_words = filters.get("any", [])
    blacklist = filters.get("blacklist", [])
    # blacklist
    for bad in blacklist:
        if bad in text:
            return False
    # required
    for word in required:
        if word not in text:
            return False
    # any
    if any_words and not any(word in text for word in any_words):
        return False
    return True


async def main():
    await client.start()
    logging.info("Forward started")

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
        text = event.raw_text.strip()
        source_chat = event.chat_id

       # Get user ID from username
        if text.startswith("/userid "):
            username = text.split(maxsplit=1)[1].lstrip("@")
            try:
                user = await client.get_entity(username)
                await event.reply(f"🔍 User ID for @{username} is: `{user.id}`")
            except Exception as e:
                await event.reply(f"⚠️ Error fetching user ID for @{username} - {e}")
            return

        for config in chat_config:
            if str(config["source"]) == str(source_chat):
                destinations = config.get("destination", [])
                filters = config.get("filters", {})
                original_message_text = event.message.text or ""
                original_message_id = event.message.id

                # Check filters
                if not passes_filters(original_message_text, filters):
                    logging.debug(f"Message skipped due to filters in chat {source_chat}")
                    return

                if event.message.reply_to_msg_id:
                    original_message = await event.get_reply_message()
                    if original_message:
                        original_sender = original_message.sender_id if original_message.sender_id else "Unknown"
                        original_message_text = (
                            f"Replying to {original_sender}: {original_message.text}\n\n{original_message_text}"
                        )
                await process_queue(original_message_text, event.message.media, destinations, original_message_id)


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

    logging.info("Listening for new messages...")
    try:
        await client.run_until_disconnected()
    except Exception as e:
        logging.error(f"Error while running the bot: {e}")
    except asyncio.CancelledError:
        logging.info("Shutting down gracefully...")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped by user.")
        forwarded_messages.clear()
