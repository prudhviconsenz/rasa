from collections import defaultdict
from typing import Any, Dict, List, Text
from rasa_sdk import Action, FormValidationAction, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import EventType, SlotSet, AllSlotsReset, Restarted
from rasa_sdk.forms import REQUESTED_SLOT
from .defaultlog import log
import random
from difflib import SequenceMatcher as SM
import logging
import pandas as pd
import os

log = logging.getLogger(__name__)

# text matches must exceed to be considered a match
MATCH_THRESHOLD = 0.7

# sample list of restaurants from kaggle zomato (see nbs/restaurants.ipynb)
path = os.path.join(os.path.dirname(__file__), "zomato200.csv")
df = pd.read_csv(path)


class ValidateNavigateSearchForm(FormValidationAction):
    """ 
    form slots
        search=pizza (location_type)
        choice=second (number, ordinal or text)
    working slots
        choices=["pizza1", "pizza2", "pizza3"]
        destination=pizza2
    output slots
        active_route (inserts destination at start)
    """

    def name(self):
        return "validate_navigate_search_form"

    def validate_search(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        log.debug("validate search")

        log.debug(value)
        log.debug(tracker.slots)

        # todo select by cuisine rather than just prefix the search location_type
        # simulate getting choice of locations e.g restaurant, pizza
        rests = df.sample(random.randint(0, 5)).name.values.tolist()
        choices = [f"{x}" for x in rests]

        log.debug(choices)

        if len(choices) == 0:
            dispatcher.utter_message(response="utter_not_found")
            return dict(
                destination=None, choices=None, choice=None, requested_slot=None
            )
        elif len(choices) == 1:
            dispatcher.utter_message(response="utter_only_option", choice=choices[0])
            return dict(
                destination=choices[0],
                choices=None,
                choice=None,
                requested_slot="confirm_destination",
            )
        elif len(choices) >= 2:
            return dict(
                destination=None, choices=choices, choice=None, requested_slot="choice"
            )

    def validate_choice(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:

        log.debug("validate choice")

        # Only need to make a choice if there are choices
        choices = tracker.get_slot("choices")

        # get ordinal or number
        number_entities = [
            e
            for e in tracker.latest_message["entities"]
            if e["entity"] in ["ordinal", "number"]
        ]
        log.debug(number_entities)

        # ordinal/number for multiple choices
        if len(number_entities) > 0:
            # use last and convert text => number e.g. first => 1 one => 1
            index = number_entities[-1]["additional_info"]["value"] - 1
            log.debug(index)
            try:
                log.debug(choices[index])
                return dict(
                    destination=choices[index], requested_slot="confirm_destination"
                )
            except IndexError:
                # reprompt
                dispatcher.utter_message(response="utter_invalid_choice")
                return dict(choice=None)
        # fuzzy match for text choice
        elif len(number_entities) == 0:
            text = tracker.latest_message["text"]
            # TODO this is a hack. how can you cancel from a text field
            if text.lower().find("cancel") >= 0:
                dispatcher.utter_message(response="utter_cancel")
                return dict(destination=None, requested_slot=None)
            scores = [
                SM(None, choice.lower(), text.lower()).ratio() for choice in choices
            ]
            index = scores.index(max(scores))
            if scores[index] > MATCH_THRESHOLD:
                return dict(
                    destination=choices[index], requested_slot="confirm_destination"
                )
            else:
                # reprompt
                dispatcher.utter_message(response="utter_invalid_choice")
                return dict(choice=None, requested_slot="choice")

    def validate_confirm_destination(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        log.debug("validate confirm_destination")
        return dict(confirm_destination=value, requested_slot=None)


class SubmitNavigateSearchForm(Action):
    def name(self):
        return "submit_navigate_search_form"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        log.debug("submit navigate search form")

        active_route = tracker.get_slot("active_route")
        if tracker.get_slot("confirm_destination"):
            dispatcher.utter_message(response="utter_navigation_started")

            # insert into active_route
            active_route.insert(0, tracker.get_slot("destination"))

        return [
            SlotSet("search", None),
            SlotSet("active_route", active_route),
            SlotSet("destination", None),
            SlotSet("choices", None),
            SlotSet("choice", None),
            SlotSet("confirm_destination", None),
        ]


############################################################


class ValidateNavigateForm(FormValidationAction):
    def name(self):
        return "validate_navigate_form"

    def validate_destination(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        log.debug("validate destination")

        log.debug(tracker.latest_message["entities"])

        if isinstance(value, list):
            value = value[-1]

        return dict(requested_slot="confirm_destination", destination=value)

    def validate_confirm_destination(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        log.debug("validate confirm_destination")
        return dict(confirm_destination=value, requested_slot=None)


class SubmitNavigateForm(Action):
    def name(self):
        return "submit_navigate_form"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        log.debug("submit navigation form")

        entities = tracker.latest_message["entities"]
        log.debug("***************************************")
        log.debug(entities)
        log.debug("***************************************")
        log.debug(tracker.slots)
        log.debug("***************************************")

        if tracker.get_slot("confirm_destination"):
            # single shot form but there are options that could be captured

            dispatcher.utter_message(response="utter_navigation_started")

            via = tracker.get_slot("via")
            if isinstance(via, list):
                via = via[-1]
            if via:
                dispatcher.utter_message(text=f"include points are {via}")
            avoiding = tracker.get_slot("avoiding")
            if isinstance(avoiding, list):
                avoiding = avoiding[-1]
            if avoiding:
                dispatcher.utter_message(text=f"exclude points are {avoiding}")
            active_route = [tracker.get_slot("destination")]

        else:
            active_route = None

        # save active_route and reset the rest
        return [
            SlotSet("active_route", active_route),
            SlotSet("destination", None),
            SlotSet("from_location", None),
            SlotSet("via", None),
            SlotSet("avoiding", None),
            SlotSet("confirm_destination", None),
        ]
