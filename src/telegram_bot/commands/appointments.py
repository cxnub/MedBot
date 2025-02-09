from __future__ import annotations
from typing import TYPE_CHECKING

from datetime import datetime, date, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext, ConversationHandler

from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from telegramify_markdown import markdownify

from src.utils.db_helper import DBHelper
from src.telegram_bot.utils.helpers import create_button_layout


if TYPE_CHECKING:
    from src.telegram_bot.commands import Commands


def view_appointments(commands: Commands, update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_appointments = commands.db.fetch_all_upcoming_appointments(user_id)
    
    if not user_appointments:
        text = "🎉 Looks like your schedule is as clear as a summer sky! ✨\n\nWant to change that? Just ask me or use the /book_appointment command and I'll help you find the perfect time to see a doctor! 🏥👨‍⚕️"
        update.message.reply_text(text)
        return
    
    text = "📅 **Your Upcoming Appointments**\n\n"
    buttons = []
    
    # show appointment ID and date only
    for appointment in user_appointments:
        appointment_date = appointment['datetime'].strftime("%d %B %Y at %I %p").lstrip('0').replace(' 0', ' ')
        text += f"🆔 **Appointment ID:** {appointment['id']}\n📅 **Date:** {appointment_date}\n\n"
        
        buttons.append([f"🆔 {appointment['id']}", f"show_appointment+{appointment['id']}"])
        
    buttons = create_button_layout(buttons, 2)
    
    text += "Drop me the appointment ID or click any of the buttons below and I'll show more details or help you cancel it! ✨"
    update.message.reply_markdown_v2(markdownify(text), reply_markup=InlineKeyboardMarkup(buttons))
    
    
def show_appointment_template(appointment):
    date_str = appointment['datetime'].strftime("%d %B %Y")
    time_str = appointment['datetime'].strftime("%I %p").lstrip('0').replace(' 0', ' ')
    
    message = "Here are the details of your appointment:\n"
    message += f"===\n"
    message += f"🆔 **Appointment ID:** {appointment['id']}\n"
    message += f"👨‍⚕️ **Doctor:** {appointment['doctor']}\n"
    message += f"🏥 **Hospital:** {appointment['hospital']}\n"
    message += f"📅 **Date:** {date_str}\n"
    message += f"⏰ **Time Slot:** {time_str}\n"
    message += f"===\n"
    
    return message
    
def show_appointment(commands: Commands, update: Update, context: CallbackContext, appointment_id: int = None) -> None:
    user_id = update.callback_query.from_user.id if update.callback_query else update.message.from_user.id
    
    if not appointment_id and not update.callback_query:
        update.effective_chat.send_message("Oopsie daisy! 🌟 I need the appointment ID to fetch the details for you. Could you please provide it? 🆔", parse_mode='MarkdownV2')
        return
    
    if update.callback_query:
        appointment_id = update.callback_query.data.split('+')[1]
        update.callback_query.answer()
    
    appointment = commands.db.get_appointment(user_id, appointment_id)
    if not appointment:
        update.effective_chat.send_message("Oopsie daisy! 🌟 It seems like you don't have an appointment with the provided ID. Could you double-check it for me? 🧐", parse_mode='MarkdownV2')
        return
    
    appointment = appointment[0]
    message = show_appointment_template(appointment)
    message += "Would you like to cancel this appointment? Just click the button below if you want to free up some time in your schedule! 🗑️"
    
    cancel_button = InlineKeyboardButton(text="🗑️ Cancel Appointment", callback_data=f"cancel_appointment+{appointment['id']}")
    
    update.effective_chat.send_message(markdownify(message), reply_markup=InlineKeyboardMarkup([[cancel_button]]), parse_mode='MarkdownV2')


def cancel_appointment(commands: Commands, update: Update, context: CallbackContext) -> None:
    appointment_id = update.callback_query.data.split('+')[1]
    user_id = update.callback_query.from_user.id
    
    appointment = commands.db.get_appointment(user_id, appointment_id)
    
    if not appointment:
        text = "Oopsie daisy! 🌟 It seems like you already cancelled this appointment. 🧐"
        update.callback_query.edit_message_text(markdownify(text), parse_mode='MarkdownV2')
        return
    
    commands.db.cancel_appointment(user_id, appointment_id)
    message = "❌ **APPOINTMENT CANCELLED** ❌\n\n"
    message += show_appointment_template(appointment[0])
    message += "This appointment has been cancelled."
    update.callback_query.edit_message_text(markdownify(message), parse_mode='MarkdownV2')
    update.callback_query.answer("Appointment cancelled successfully. ✅", show_alert=True)
    

def pick_hospital(commands: Commands, update: Update, context: CallbackContext) -> int:
    # check if there already is a conversation in progress
    if context.user_data and context.user_data.get('booking', False):
        text = f"**Whoa** calm down, multitasker! 🏃‍♂️ Looks like you\'re trying to book multiple appointments at once. Even doctors can\'t be in two places at the same time!"
        text += "\n\nPlease finish your current booking first or /cancel to cancel it. 😅"
        text = markdownify(text)

        update.message.reply_markdown_v2(text)
        return ConversationHandler.END
    
    # check if user has more than 5 appointments
    user_id = update.message.from_user.id
    user_appointments = commands.db.fetch_all_upcoming_appointments(user_id)
    
    if len(user_appointments) >= 5:
        text = "🏥 **Hold on there, healthcare champion!** 🌟"
        text += "\n\nLooks like you're trying to set a world record with 5+ medical appointments! While we admire your enthusiasm for staying healthy, let's keep it to 5 at a time. 🎯"
        text += "\n\nTip: Eat an apple a day to keep the doctors away! 🍎✨"
        text = markdownify(text)
        update.message.reply_markdown_v2(text)
        
        return ConversationHandler.END
    
    context.user_data['booking'] = True
    
    hospitals = commands.db.get_hospitals()
    buttons = []
    
    # split the hospitals into groups of 2
    for i in range(0, len(hospitals), 2):
        group = hospitals[i:i+2]
        buttons.append([InlineKeyboardButton(text=group[0]['name'], callback_data=f"{group[0]['id']}_{group[0]['name']}")])
        
        if len(group) == 2:
            buttons[-1].append(InlineKeyboardButton(text=group[1]['name'], callback_data=f"{group[1]['id']}_{group[1]['name']}"))
        
    context.user_data['booking_msg'] = update.message.reply_text(
        markdownify('Please select a **hospital** from the list below to proceed.\n\nYou may use the /cancel command to cancel the booking anytime.'),
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode='MarkdownV2'
    )
    
    return commands.SELECT_HOSPITAL
    

def handle_hospital(commands: Commands, update: Update, context: CallbackContext) -> int:
    hospital = update.callback_query.data
    hospital_id, hospital_name = hospital.split('_')
    context.user_data['hospital'] = hospital_id
    context.user_data['hospital_name'] = hospital_name
    return pick_doctor(commands, update, context)
    
    
def pick_doctor(commands: Commands, update: Update, context: CallbackContext) -> int:
    hospital_id = context.user_data['hospital']
    doctors = commands.db.get_doctors(hospital_id)

    buttons = []
    
    # split the doctors into groups of 2
    for i in range(0, len(doctors), 2):
        group = doctors[i:i+2]
        buttons.append([InlineKeyboardButton(text=group[0]['name'], callback_data=f"{group[0]['id']}_{group[0]['name']}")])
        
        if len(group) == 2:
            buttons[-1].append(InlineKeyboardButton(text=group[1]['name'], callback_data=f"{group[1]['id']}_{group[1]['name']}"))
        
    text = format_appointment(hospital=context.user_data['hospital_name'], item='doctor')
    update.callback_query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode='MarkdownV2'
    )
    
    return commands.SELECT_DOCTOR
    
    
def handle_doctor(commands: Commands, update: Update, context: CallbackContext) -> int:
    doctor = update.callback_query.data
    doctor_id, doctor = doctor.split('_')
    context.user_data['doctor'] = doctor_id
    context.user_data['doctor_name'] = doctor
    return pick_date(commands, update, context) 


def pick_date(commands, update: Update, context: CallbackContext) -> int:
    now = datetime.now()
    calendar, step = DetailedTelegramCalendar(
            current_date=now,
            min_date=now,
            max_date=now.replace(year=now.year + 2),
        ).build()
    
    text = format_appointment(hospital=context.user_data['hospital_name'], doctor=context.user_data['doctor_name'], item='date', custom_item="You may book an appointment up to 2 years in advance! 📅✨")
    
    update.callback_query.edit_message_text(
        text,
        reply_markup=calendar,
        parse_mode='MarkdownV2'
    )
    
    return commands.SELECT_DATE
    

def handle_date(commands: Commands, update: Update, context: CallbackContext) -> int:
    result, key, step = DetailedTelegramCalendar().process(update.callback_query.data)
    
    if not result and key:
        text = format_appointment(hospital=context.user_data['hospital_name'], doctor=context.user_data['doctor_name'], item=LSTEP[step])
        
        update.callback_query.edit_message_text(text, reply_markup=key, parse_mode='MarkdownV2')
        
        return commands.SELECT_DATE
            
    elif result:
        # check if the date is today or in the past
        if result <= date.today():
            text = format_appointment(
                hospital=context.user_data['hospital_name'],
                doctor=context.user_data['doctor_name'],
                custom_item="⏰ Oops! Time Check ⏰\nLooks like you're trying to book an appointment in the past! While we'd love to help you time travel, we can only schedule future appointments.\n\nPlease pick an **upcoming** date! 📅✨"
            )
            
            now = datetime.now()
            calendar, step = DetailedTelegramCalendar(
                    current_date=now,
                    min_date=now,
                    max_date=now.replace(year=now.year + 2),
                ).build()
            
            update.callback_query.edit_message_text(text, reply_markup=calendar, parse_mode='MarkdownV2')
            
            return commands.SELECT_DATE
        
        context.user_data['date'] = result
        return pick_slot(commands, update, context)


def pick_slot(commands: Commands, update: Update, context: CallbackContext) -> int:
    doctor_id = context.user_data['doctor']
    date = context.user_data['date']
    slots = commands.db.get_available_slots(doctor_id, date)
    buttons = []
    
    for slot in slots:
        slot_datetime = datetime.min + slot['slot_time']
        time_str = slot_datetime.strftime("%I %p").lstrip('0').replace(' 0', ' ') if slot['available'] == 1 else "🚫"
        
        buttons.append([time_str, slot_datetime.strftime("%H:%M") if slot['available'] == 1 else "taken"])
        
    buttons = create_button_layout(buttons, 4)

    text = format_appointment(hospital=context.user_data['hospital_name'], doctor=context.user_data['doctor_name'], date=context.user_data['date'], item='time slot')
    update.callback_query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode='MarkdownV2'
    )
    
    return commands.SELECT_SLOT
    

def handle_slot(commands: Commands, update: Update, context: CallbackContext) -> int:
    slot = update.callback_query.data
    
    if slot == "taken":
        update.callback_query.answer("Sorry, our doctors can't split themselves in half 👥", timeout=30)
        return commands.SELECT_SLOT
    
    context.user_data['slot'] = slot
    
    text = format_appointment(
        hospital=context.user_data['hospital_name'],
        doctor=context.user_data['doctor_name'],
        date=context.user_data['date'],
        slot=context.user_data['slot'],
        custom_item="🌟 Almost there! Just one last step to secure your spot! 🎯\n\nCheck your appointment booking details and confirm by pressing the button below! ⬇️"
    )
    
    buttons = [
        [InlineKeyboardButton(text='Confirm Booking', callback_data='confirm_appointment')],
        [InlineKeyboardButton(text='Cancel Booking', callback_data='cancel_appointment')]
    ]
    
    update.callback_query.edit_message_text(text=text, parse_mode='MarkdownV2', reply_markup=InlineKeyboardMarkup(buttons))
    
    return commands.CONFIRM_APPOINTMENT

def handle_confirm_appointment(commands: Commands, update: Update, context: CallbackContext) -> int:
    if update.callback_query.data == 'cancel_appointment':
        update.callback_query.edit_message_text('🚫 **Booking Cancelled!** 🚫\n\nYour appointment booking has been successfully cancelled. If you change your mind, feel free to start a new booking journey anytime! 🌟')
        
        context.user_data.clear()
        
        return ConversationHandler.END
        
    user_id = update.callback_query.from_user.id
    doctor_id = context.user_data['doctor']
    hospital_id = context.user_data['hospital']
    date = context.user_data['date']
    slot = context.user_data['slot']
    datetime = f"{date} {slot}"
    
    commands.db.create_appointment(user_id, doctor_id, hospital_id, datetime)
    
    text = format_appointment(
        hospital=context.user_data['hospital_name'],
        doctor=context.user_data['doctor_name'],
        date=context.user_data['date'],
        slot=context.user_data['slot'],
        custom_item="Your appointment has been booked successfully! 🎉"
    )
    
    update.callback_query.edit_message_text(text=text, parse_mode='MarkdownV2')
    update.callback_query.answer("Appointment booked successfully! 🎉", show_alert=True)
    
    context.user_data.clear()
    
    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    if context.user_data:
        booking_msg = context.user_data.get('booking_msg')
    
        if booking_msg:
            booking_msg.delete()
    
        context.user_data.clear()
        
        text = '🌟 Your booking vanished into thin air! _*poof*_ 🪄\n\nFeel free to start a new booking journey whenever you\'re ready - just ask or use the magical /book_appointment command! ✨'
        text = markdownify(text)
        update.message.reply_markdown_v2(text)
        return
    
    update.message.reply_text('What are you trying to cancel? 🤔 You have no active bookings.')
        

def format_appointment(hospital=None, doctor=None, date: date=None, slot: str=None, item=None, custom_item=None):
    template = """
🏥 **Appointment Details**
======
🏢 **Hospital:** {hospital}
👨‍⚕️ **Doctor:** {doctor}
📅 **Date:** {date}
⏰ **Time Slot:** {slot}
======

{item}
    """
    
    item_str = ""
    
    if item:
        item_str = f"Type /cancel to cancel the booking anytime.\n\nPlease select a **{item}** with the buttons below to proceed ⬇️"
    
    if custom_item:
        item_str = custom_item
        
    if slot:
        slot = datetime.strptime(slot, "%H:%M").strftime("%I %p").lstrip('0').replace(' 0', ' ')
        
    if date:
        date = date.strftime("%d %B %Y")
    
    return markdownify(
        template.format(
            hospital=hospital,
            doctor=doctor,
            date=date,
            slot=slot,
            item=item_str
        )
    )
    
