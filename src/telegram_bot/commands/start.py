from __future__ import annotations
from typing import TYPE_CHECKING

from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext
from telegramify_markdown import markdownify

from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP

from src.utils.db_helper import DBHelper

if TYPE_CHECKING:
    from src.telegram_bot.commands import Commands


def start(command: Commands, update: Update, context: CallbackContext) -> None:
    user_exists = command.db.check_telegram_id(update.message.from_user.id)
    
    if not user_exists:
        command.db.create_user(update.message.from_user.username, update.message.from_user.id)
        message = markdownify(f"Welcome {update.message.from_user.mention_markdown_v2()}! 🎉\n\nI'm your new personal AI health assistant! 🤖✨\n\nI'm here to help with medical queries, appointments, and more! 🏥\n\nJust ask me anything or type /help to see what else I can do! 💫")
        
        update.message.reply_markdown_v2(message)
        
        return
        
    
    message = markdownify(f"Hey there {update.message.from_user.mention_markdown_v2()}! 👋 Great to see you again! 🌟\n\nI'm your friendly AI health assistant 🤖 Ready to help you stay healthy and happy! 💪\n\nWhat can I do for you today? 😊")
    
    update.message.reply_markdown_v2(message)
        

def help_cmd(self, update: Update, context: CallbackContext) -> None:
    message = markdownify(
        "✨ *Here's What I Can Do For You* ✨\n\n"
        "🚀 */start* \- Start a conversation with me\n"
        "❓ */help* \- Show this help message\n"
        "📅 */view_appointments* \- Check your scheduled appointments\n"
        "📝 */book_appointment* \- Schedule a new appointment\n\n"
        "Need assistance? Just ask me anything\! 😊"
    )
    update.message.reply_markdown_v2(message)
