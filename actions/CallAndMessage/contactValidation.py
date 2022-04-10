from typing import Any, Dict, List, Text
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import logging

log = logging.getLogger(__name__)

phonebook = {
    "home": "0873-888884",
    "office": "0873-567567",
    "work": "0873-34534534",
    "Vivek": "0725243567",
    "Farida": "01234546789",
    "Leo Trump": "0725243567",
    "Anders Watson": "01234546789",
    "Farida Watson": "01234546789",
    "Vivek Madhusan": "0756213131",
    "Anna": "0786754345",
}
phonebook = {k.lower(): v for k, v in phonebook.items()}

def validate_contact_name(value, dispatcher):
    log.debug("validate contact_name")

    if isinstance(value, list):
        value = value[-1]

    # all comparisons are case insensitive
    value = value.lower()

    # exact match in phonebook
    if value in phonebook:
        dispatcher.utter_message(response="utter_contact_found", contact_name=value)
        return {"contact_name": value, "contact_number": phonebook[value]}

    log.debug("validate contact_name: no match found")

    # first and surname match
    contacts = []
    for name in value.split():
        if len(name) < 3:
            continue
        found = [k for k, v in phonebook.items() if k.find(name) >= 0]
        contacts.extend(found)

        if len(contacts) == 0:
            dispatcher.utter_message(response="utter_contact_not_found", contact_name=name)
            return {"contact_name": None, "contact_number": None}

        if len(contacts) == 1:
            dispatcher.utter_message(
                response="utter_contact_found", contact_name=list(contacts)[0]
            )
            return {"contact_name": name, "contact_number": phonebook[name]}

        if len(contacts) >= 2:
            contacts = " and ".join(contacts)
            dispatcher.utter_message(response="utter_contacts_found", contacts=contacts)
            return {"contact_name": None}

    log.debug("validate contact_name: no partial match either")
    return {"contact_name": None}