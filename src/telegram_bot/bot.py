import requests
import os
from dotenv import load_dotenv

from telegram import Bot, Update
from telegram.utils.helpers import escape_markdown
from telegram.ext import (CallbackContext, CommandHandler, Filters,
                          MessageHandler, Updater, CallbackQueryHandler, ConversationHandler)

from src.utils.db_helper import DBHelper
from src.telegram_bot.commands import Commands

import telegramify_markdown


load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
DB_NAME = os.getenv('DB_NAME', 'med_bot')
db = DBHelper(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)


class MedBot:
    def __init__(self, token=None, rasa_token=None):
        self.TOKEN = token
        self.RASA_TOKEN = rasa_token

        if self.TOKEN is None:
            raise ValueError('Please set TELEGRAM_BOT_TOKEN in .env file')
        
        if self.RASA_TOKEN is None:
            raise ValueError('Please set RASA_TOKEN in .env file')

        self.bot = Bot(token=self.TOKEN)
        self.db = db
        self.updater = Updater(self.TOKEN)
        self.dispatcher = self.updater.dispatcher
        
        # Initialize the commands
        self.commands: Commands = Commands(self.db)

        self.dispatcher.add_handler(CommandHandler("start", self.commands.start))
        self.dispatcher.add_handler(CommandHandler("help", self.commands.help))
        self.dispatcher.add_handler(CommandHandler("view_appointments", self.commands.view_appointments))
        self.dispatcher.add_handler(CommandHandler("cancel", self.commands.cancel))
        self.dispatcher.add_handler(CallbackQueryHandler(self.commands.show_appointment, pattern='^show_appointment\+\d+$'))
        self.dispatcher.add_handler(CallbackQueryHandler(self.commands.cancel_appointment, pattern='^cancel_appointment\+\d+$'))
        self.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_message))
        
        # Add conversation handler for booking appointments
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler('book_appointment', self.commands.book_appointment),
                CallbackQueryHandler(self.commands.handle_hospital)
                ],
            states={
                self.commands.SELECT_HOSPITAL: [CallbackQueryHandler(self.commands.handle_hospital)],
                self.commands.SELECT_DOCTOR: [CallbackQueryHandler(self.commands.handle_doctor)],
                self.commands.SELECT_DATE: [CallbackQueryHandler(self.commands.handle_date)],
                self.commands.SELECT_SLOT: [CallbackQueryHandler(self.commands.handle_slot)],
                self.commands.CONFIRM_APPOINTMENT: [CallbackQueryHandler(self.commands.confirm_appointment)]
            },
            fallbacks=[
                CommandHandler('cancel', self.commands.cancel),
                CommandHandler('book_appointment', self.commands.book_appointment),
            ],
            run_async=True,
            per_user=True
        )
        self.dispatcher.add_handler(conv_handler)


    def handle_message(self, update: Update, context: CallbackContext) -> None:
        user_message = update.message.text
        
        if not self.db.check_telegram_id(update.message.from_user.id):
            self.commands.start(update, context)
            return
        
        try:
            response = requests.post(
                f'http://localhost:5005/webhooks/rest/webhook/?token={self.RASA_TOKEN}',
                json={"sender": update.effective_user.id,
                      "message": user_message},
                timeout=60 * 5
                )
            
            bot_response = response.json()
            print(f"User message: {user_message}")
            print(f"Response from Rasa: {bot_response}\n\n----------------------\n\n")
            
            if not bot_response or len(bot_response) == 0:
                raise Exception("No response from Rasa")
            
            # loop through the bot responses and send them to the user
            for response in bot_response:
                # check if response is show help
                if response['text'] == "show_help":
                    self.commands.help(update, context)
                    continue
                
                # check if the response is a date time picker
                if response['text'] == "show_date_picker":
                    self.commands.show_date_picker(update, context)
                    continue
                
                # check if response is show appointment
                if response['text'] == "show_appointments":
                    self.commands.view_appointments(update, context)
                    continue
                
                # check if response is show appointment details
                if response['text'].startswith("show_appointment+"):
                    appointment_id = response['text'].split("+")[1]
                    self.commands.show_appointment(update, context, int(appointment_id))
                    continue
                
                # check if response is handle appointment
                if response['text'] == "handle_appointment":
                    self.commands.book_appointment(update, context)
                    continue
                
                # reply to the user with the bot response
                update.message.reply_markdown_v2(telegramify_markdown.markdownify(response['text']))
                
            
        except Exception as e:
            print(e)
            update.message.reply_text("Sorry, I am unable to process your request at the moment. Please try again later.")

    def run(self) -> None:
        self.updater.start_polling()
        self.updater.idle()

if __name__ == '__main__':
    bot = MedBot()
    bot.run()
