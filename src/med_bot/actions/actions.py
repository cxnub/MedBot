# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

# from typing import Any, Text, Dict, List
#
# from rasa_sdk import Action, Tracker
# from rasa_sdk.executor import CollectingDispatcher
#
#
# class ActionHelloWorld(Action):
#
#     def name(self) -> Text:
#         return "action_hello_world"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         dispatcher.utter_message(text="Hello World!")
#
#         return []

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

from typing import Any, Text, Dict, List

from dotenv import load_dotenv
import os

import requests

from src.utils.db_helper import DBHelper

load_dotenv("../../.env", override=True)

RAG_SERVER_URL = os.getenv('RAG_SERVER_URL')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
DB_NAME = os.getenv('DB_NAME', 'med_bot')
db = DBHelper(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)

class ActionAnswerWithLLM(Action):
    def name(self) -> Text:
        return "action_answer_with_llm"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        intent = tracker.latest_message['intent']['name']
        
        user = db.get_user(tracker.sender_id)[0]
        fun_mode = True if user.get('fun_mode', False) == 1 else False
        
        url = RAG_SERVER_URL + "/query"
        
        query = tracker.latest_message['text']
        
        if fun_mode:
            query += "\n\n(Please reply using singlish and use markdown if neccessary and do not exceed 3 paragraphs)"
        else:
            query += "\n\n(Please reply with markdown if neccessary and do not exceed 3 paragraphs)"
            
        data = {"query": query}

        try:
            response = requests.post(url, json=data).json()
            reply_text = response['answer']
            
        except Exception as e:
            print(e)
            reply_text = "Sorry, I am unable to answer your query at the moment. Please try again later."
        
        if intent == 'nlu_fallback':
            dispatcher.utter_message(
                text=reply_text + " (NLU Fallback)"
            )
            return
        
        dispatcher.utter_message(
            text=reply_text
        )
            
        return []
    
    
class ActionBookAppointment(Action):
    def name(self) -> Text:
        return "action_book_appointment"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="Amazing! Your appointment has been booked successfully and will receive a confirmation shortly. Hope you feel better soon!")
        return []
    

class ActionAskHospital(Action):
    def name(self) -> Text:
        return "action_ask_hospital"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # check if intent is affirm or yes_to_booking_appointment
        intent = tracker.latest_message['intent']['name']
        print(intent)
        
        if intent == 'affirm' or intent == 'yes_to_booking_appointment':
            dispatcher.utter_message(text="show_hospital_picker")
            return []
        
        dispatcher.utter_message(text="Okay, no problem. Let me know if you need any more help!")
        return []
    

class ActionAskDateTime(Action):
    def name(self) -> Text:
        return "action_ask_date_time"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # check if hospital is provided
        hospital = tracker.get_slot('hospital')
        
        # if hospital is not provided, ask for hospital
        if not hospital:
            dispatcher.utter_message(text="Sorry, only the following hospitals are available:\n")
            return []
        
        dispatcher.utter_message(text="show_date_time_picker")
        

class ActionShowAppointments(Action):
    def name(self) -> Text:
        return "action_show_appointments"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="show_appointments")
        return []
    
class ActionShowMoreDetails(Action):
    def name(self) -> Text:
        return "action_show_more_details"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        appointment_id = tracker.get_slot('appointment_id')
        
        if not appointment_id:
            dispatcher.utter_message(text="Please provide me the appointment ID you want to view.")
            return []
        
        appointment = db.get_appointment(tracker.sender_id, appointment_id)
        
        if not appointment or len(appointment) == 0:
            dispatcher.utter_message(text="You do not have an appointment with the provided ID.")
            return []
        
        appointment = appointment[0]
        
        dispatcher.utter_message(text="show_appointment+{}".format(appointment_id))
        return []
    
class ActionCancelAppointment(Action):
    def name(self) -> Text:
        return "action_cancel_appointment"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="I am sorry, I am unable to cancel your appointment at the moment. Please try again later.")
        return []
    
    
class ActionHelp(Action):
    def name(self) -> Text:
        return "action_help"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="show_help")
        return []
    
class ActionOnFunMode(Action):
    def name(self) -> Text:
        return "action_on_fun_mode"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        db.change_fun_mode(tracker.sender_id, fun_mode=1)
        dispatcher.utter_message(text="Fun mode is now enabled, I will reply to you in Singlish now!")
        return []
    
class ActionOffFunMode(Action):
    def name(self) -> Text:
        return "action_off_fun_mode"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        db.change_fun_mode(tracker.sender_id, fun_mode=0)
        dispatcher.utter_message(text="Fun mode is now disabled, I will reply to you formally now.")
        return []
