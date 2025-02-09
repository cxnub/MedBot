from __future__ import annotations
from typing import TYPE_CHECKING

from telegram import Update
from telegram.ext import CallbackContext

from src.telegram_bot.commands.start import start, help_cmd
from src.telegram_bot.commands.appointments import *
if TYPE_CHECKING:
    from src.utils.db_helper import DBHelper


class Commands:
    def __init__(self, db: DBHelper):
        self.db: DBHelper = db
        self.SELECT_HOSPITAL, self.SELECT_DOCTOR, self.SELECT_DATE, self.SELECT_SLOT, self.CONFIRM_APPOINTMENT = range(5)
        
    def check_user(self, update: Update, context: CallbackContext) -> bool:
        # check if update has a message
        if update.message is None:
            user_id = update.callback_query.from_user.id
            username = update.callback_query.from_user.username
            
        else:
            user_id = update.message.from_user.id
            username = update.message.from_user.username
        
        if not self.db.check_telegram_id(user_id):
            self.db.create_user(username, user_id)
    
    def start(self, update: Update, context: CallbackContext) -> None:
        return start(self, update, context)
    
    def help(self, update: Update, context: CallbackContext) -> None:
        return help_cmd(self, update, context)
    
    def view_appointments(self, update: Update, context: CallbackContext) -> None:
        return view_appointments(self, update, context)
    
    def show_appointment(self, update: Update, context: CallbackContext, id: int=None) -> None:
        return show_appointment(self, update, context, id)
    
    def cancel_appointment(self, update: Update, context: CallbackContext) -> None:
        return cancel_appointment(self, update, context)
    
    def book_appointment(self, update: Update, context: CallbackContext) -> int:
        self.check_user(update, context)
        return pick_hospital(self, update, context)
    
    def handle_hospital(self, update: Update, context: CallbackContext) -> int:
        return handle_hospital(self, update, context)
    
    def show_date_picker(self, update: Update, context: CallbackContext) -> None:
        return pick_date(self, update, context)
    
    def handle_date_picker(self, update: Update, context: CallbackContext) -> None:
        return handle_date(self, update, context)
    
    def handle_doctor(self, update: Update, context: CallbackContext) -> int:
        return handle_doctor(self, update, context)
    
    def handle_date(self, update: Update, context: CallbackContext) -> int:
        return handle_date(self, update, context)
    
    def handle_slot(self, update: Update, context: CallbackContext) -> int:
        return handle_slot(self, update, context)
    
    def confirm_appointment(self, update: Update, context: CallbackContext) -> int:
        return handle_confirm_appointment(self, update, context)
    
    def cancel(self, update: Update, context: CallbackContext) -> int:
        return cancel(update, context)
