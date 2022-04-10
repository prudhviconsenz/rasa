from typing import Any, Dict, List, Text
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import logging
from .contactValidation import validate_contact_name, phonebook

log = logging.getLogger(__name__)

class ValidateCallMakeForm(FormValidationAction):
    def name(self):
        return "validate_call_make_form"

    def validate_contact_name(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        log.debug("validate contact_name in call make form")
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
        log.debug("validate contact_number in call make form")

        if isinstance(value, list):
            log.warning(f"duplicate values {value}")
            value = value[-1]

        contact_name = tracker.get_slot("contact_name")
        if contact_name is None:
            return dict(contact_name = "number", contact_number=value)

        return dict(contact_name = contact_name, contact_number=value)


class SubmitCallMakeForm(Action):
    def name(self):
        return "submit_call_make_form"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        log.debug("submitcallmakeform.run")

        contact_name = tracker.get_slot("contact_name")
        contact_number = tracker.get_slot("contact_number")
        dispatcher.utter_message(response="utter_calling",
                        contact_name=contact_name,
                        contact_number=contact_number)
            
        return [SlotSet("contact_name", None),SlotSet("contact_number", None)]
