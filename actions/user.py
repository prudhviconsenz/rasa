import random
from collections import defaultdict
from typing import Any, Dict, List, Text

from rasa_sdk import Action, FormValidationAction, Tracker
from rasa_sdk.events import SlotSet, AllSlotsReset, Restarted
from rasa_sdk.executor import CollectingDispatcher
from collections import defaultdict

import logging

log = logging.getLogger(__name__)

avg_lengths = defaultdict(int, {"Search_Places": 6.19, "navigate": 3.35})


class Cancel(Action):
    """ generic cancel for any form """

    def name(self) -> Text:
        return "cancel"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        log.debug("cancelling")

        log.debug(tracker)
        log.debug(tracker.active_form)

        form = tracker.active_form.get("name")

        # reset specific slots for each form
        if form == "navigate_form":
            slots = [
                "destination",
                "from_location",
                "via",
                "avoiding",
                "active_route",
                "confirm_destination",
            ]
        elif form == "navigate_search_form":
            slots = [
                "search",
                "choice",
                "destination",
                "choices",
                "confirm_destination",
            ]
        elif form == "call_make_form":
            slots = ["contact_name", "contact_number"]
        elif form == "call_message_form":
            slots = ["contact_name", "contact_number", "message", "confirm_destination"]
        elif form == "music_play_form":
            slots = ["artist", "genre", "playlist", "album", "song"]
        else:
            log.error(f"Unknown form: {form}")
            return

        # todo does this reset to default or None? ideally want default.
        return [SlotSet(slot, None) for slot in slots]


class ActionSetUserFeats(Action):
    def name(self) -> Text:
        return "action_set_user_feats"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        user_message = tracker.latest_message["text"]
        entities = tracker.latest_message["entities"]
        entity_length = sum([len(e["value"].split()) for e in entities])

        intent = tracker.latest_message["intent"].get("name")
        l = (
            len(user_message.split()) - entity_length + len(entities)
        )  # count each entity as one word
        if l > avg_lengths[intent]:
            is_talkative = True
        else:
            is_talkative = False
        return [SlotSet("is_talkative", is_talkative)]


class ActionReprompt(Action):
    """Executes the fallback action and goes back to the previous state
    of the dialogue"""

    def name(self) -> Text:
        return "action_reprompt"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        reprompts = [
            "I'm sorry, I didn't quite understand that. Could you rephrase?",
            "Sorry, I didn't catch that, can you rephrase?",
            "Apologies, I didn't understand. Could you please rephrase it?",
        ]

        last_reprompt = tracker.get_slot("last_reprompt")
        if last_reprompt in reprompts:
            reprompts.remove(last_reprompt)
        reprompt = random.choice(reprompts)

        dispatcher.utter_message(text=reprompt)

        # Revert user message which led to fallback.
        return [SlotSet("last_reprompt", reprompt)]  # , UserUtteranceReverted()

