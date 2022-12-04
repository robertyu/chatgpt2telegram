import requests
import json
import uuid
import logging
from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, ContextTypes, CommandHandler, CallbackContext
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import InlineQueryHandler
import logging
from logging.handlers import RotatingFileHandler
import sys


class Chatbot:
    def __init__(self, logger, conversation_id=None):
        self.logger = logger
        self.authorization_key = None
        self.conversation_id = conversation_id
        self.parent_id = str(uuid.uuid4())

    def get_chat_response(self, prompt):
        headers = {
            "Accept": "application/json",
            "Authorization": "Bearer " + self.authorization_key,
            "Content-Type": "application/json"
        }
        data = {
            "action": "next",
            "messages": [
                {"id": str(uuid.uuid4()),
                 "role": "user",
                 "content": {"content_type": "text", "parts": [prompt]}
                 }],
            "conversation_id": self.conversation_id,
            "parent_message_id": self.parent_id,
            "model": "text-davinci-002-render"
        }
        response = requests.post(
            "https://chat.openai.com/backend-api/conversation", headers=headers, data=json.dumps(data))
        try:
            response = response.text.splitlines()[-4]
        except:
            self.logger.error(response.text)
            return ValueError("Error: Response is not a text/event-stream")
        try:
            response = response[6:]
        except:
            self.logger.error(response.text)
            return ValueError("Response is not in the correct format")
        response = json.loads(response)
        self.parent_id = response["message"]["id"]
        self.conversation_id = response["conversation_id"]
        message = response["message"]["content"]["parts"][0]
        return {'message': message, 'conversation_id': self.conversation_id, 'parent_id': self.parent_id}


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%m-%d %H:%M:%S')
handler.setFormatter(formatter)
handler2 = RotatingFileHandler('./gptchatbot.log', maxBytes=15*1024*1024, backupCount=5)
handler2.setFormatter(formatter)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logger.addHandler(handler)
logger.addHandler(handler2)
cb = Chatbot(logger)


async def echo(update: Update, context: CallbackContext.DEFAULT_TYPE):
    if not cb.authorization_key:
        if update.message.text.startswith('auth'):
            gpt_token = update.message.text[5:]
            cb.authorization_key = gpt_token
            reply_message = 'good, now gptchat ready'
        else:
            reply_message = 'please using auth <authcode> to init chatgpt'
    else:
        reply_message = cb.get_chat_response(update.message.text)['message']
    await context.bot.send_message(chat_id=update.effective_chat.id, text=reply_message)

    
if __name__ == "__main__":
    telegram_token = 'your_telegram_bot_token'
    application = ApplicationBuilder().token(telegram_token).build()
    
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    application.add_handler(echo_handler)

    application.run_polling()
