from typing import Any, Dict, List, Text

from rasa_sdk import Action, FormValidationAction, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, AllSlotsReset, Restarted

from .contactValidation import validate_contact_name, phonebook
import logging

log = logging.getLogger(__name__)


class ValidateMessageSendForm(FormValidationAction):
    def name(self):
        return "validate_message_send_form"

    def validate_contact_name(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        log.debug("validate contact name")
        if isinstance(value, list):
            log.warning(f"duplicate values {value}")
            value = value[-1]

        return validate_contact_name(value, dispatcher)

    def validate_contact_number(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        log.debug("validate contact_number in send message form")

        if isinstance(value, list):
            log.warning(f"duplicate values {value}")
            value = value[-1]

        contact_name = tracker.get_slot("contact_name")
        if contact_name is None:
            return dict(contact_name="number", contact_number=value)

        return dict(contact_name=contact_name, contact_number=value)

    def validate_message(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:

        log.debug("validate message")
        return {"message": value}


class SubmitMessageSendForm(Action):
    def name(self):
        return "submit_message_send_form"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        if tracker.get_slot("confirm_message"):
            contact_name = tracker.get_slot("contact_name")
            contact_number = tracker.get_slot("contact_number")

            dispatcher.utter_message(
                response="utter_message_send",
                contact_name=contact_name,
                contact_number=contact_number,
                message=tracker.get_slot("message"),
            )

        return [
            SlotSet("contact_name", None),
            SlotSet("contact_number", None),
            SlotSet("message", None),
            SlotSet("confirm_message", None),
        ]
