import configparser
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Read token from config.ini file
config = configparser.ConfigParser()
config.read('config.ini')
API_KEY = config['DEFAULT']['API_KEY']
ADMIN_ID = int(config['DEFAULT']['ADMIN_ID']) # Convert ADMIN_ID to integer

# Local cache file storage, record the association between forwarded messages and their senders, create the file if
# it does not exist
try:
    with open('forwarded_messages.json', 'r') as f:
        forwarded_messages = json.load(f)
        forwarded_messages = {int(k): set(v) for k, v in forwarded_messages.items()} # Convert the key to an integer
except FileNotFoundError:
    forwarded_messages = {}


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name} Your ID is {update.effective_user.id}')


async def reply_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    sender_id = update.message.from_user.id

    if sender_id == ADMIN_ID:
        # Process the administrator's reply message
        reply_message = update.message.reply_to_message
        if reply_message:
            unique_id = int(update.message.reply_to_message.message_id) - 1
            for user_id, message_ids in forwarded_messages.items():
                if unique_id in message_ids:
                    await context.bot.copy_message(chat_id=user_id, from_chat_id=ADMIN_ID,
                                                   message_id=update.message.message_id)
                    break
            else:
                await update.message.reply_text('No original message found to reply to.')
    else:
        # Handle non-administrator messages
        message_id = update.message.message_id

        # Record the sender of the forwarded message
        if sender_id in forwarded_messages:
            forwarded_messages[sender_id].add(message_id)
        else:
            forwarded_messages[sender_id] = {message_id}

        # 保存记录到文件
        with open('forwarded_messages.json', 'w') as f:
            json.dump({k: list(v) for k, v in forwarded_messages.items()}, f)

        # Forward the message to the administrator and keep the original format of the message, in the form of
        # forwarding, rather than copying
        await context.bot.forward_message(chat_id=ADMIN_ID, from_chat_id=update.message.chat_id, message_id=message_id)


def main() -> None:
    app = ApplicationBuilder().token(API_KEY).build()

    # Add command processor
    app.add_handler(CommandHandler("hello", hello))

    # Add a message handler to process messages from non-ADMIN_ID users and forward them to ADMIN_ID
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, reply_messages))

    app.run_polling()


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
