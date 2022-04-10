import os
import json
from typing import Any, Dict, List, Text
from datetime import datetime, timedelta
from collections import defaultdict, Counter

from rasa_sdk import Action, FormValidationAction, Tracker
from rasa_sdk.events import AllSlotsReset, Restarted, SlotSet
from rasa_sdk.executor import CollectingDispatcher

import logging

log = logging.getLogger(__name__)

avg_lengths = defaultdict(int, {"Search_Places": 6.19, "navigate": 3.35})

# mock database for dev & testing
database = {
    "destinations": [
        ["5 main street", "17.50 23.11.21"],
        ["12 royal court drive", "17.45 16.11.21"],
        ["12 royal court drive", "17.51 09.11.21"],
        ["5 main street", "17.48 02.11.21"],
        ["5 main street", "17.49 26.10.21"],
    ]
}

# create dummy lists of speed limits and driving speed, assuming it's logged every minute
speed_limits = (
    [60] * 5
    + [20] * 5
    + [60] * 10
    + [80] * 10
    + [120] * 30
    + [60] * 10
    + [20] * 10
    + [60] * 5
)
actual_speed = [50] * 20 + [85] * 10 + [110] * 30 + [40] * 25

# DB is only used for testing. in production would likely use the postgres container.
os.makedirs("dbtest", exist_ok=True)
DB = "dbtest/navigate.json"
if not os.path.exists(DB):
    with open(DB, "w") as f:
        json.dump(database, f)

date_string_pattern = "%H.%M %d.%m.%y"

speed_zones = {"danger": 30, "town": 60}


def analyse_speed(speed_limits, actual_speed, speed_zones=speed_zones):
    speed_difference = []
    speed_difference_by_zones = defaultdict(list)
    for l, a in zip(speed_limits, actual_speed):
        speed_difference.append(a - l)
        if l <= speed_zones["danger"]:
            # schools, road works, etc.
            speed_difference_by_zones["danger"].append(a - l)
        elif l <= speed_zones["town"]:
            speed_difference_by_zones["town"].append(a - l)
        else:
            speed_difference_by_zones["highway"].append(a - l)
    average_diff = round(sum(speed_difference) / len(speed_difference))
    percent_correct_speed = round(
        len([1 for diff in speed_difference if diff <= 0])
        * 100
        / len(speed_difference),
        2,
    )
    average_diff_by_zones = defaultdict(int)
    percent_correct_speed_by_zones = defaultdict(float)
    for zone, speed_diffs in speed_difference_by_zones.items():
        if len(speed_diffs) > 0:
            average_diff_by_zones[zone] = round(sum(speed_diffs) / len(speed_diffs))
            percent_correct_speed_by_zones[zone] = round(
                len([1 for diff in speed_diffs if diff <= 0]) * 100 / len(speed_diffs),
                2,
            )
    return (
        average_diff,
        percent_correct_speed,
        average_diff_by_zones,
        percent_correct_speed_by_zones,
    )


class ActionCheckDistance(Action):
    def name(self) -> Text:
        return "action_check_distance_to_destination"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Here should be a call to maps API to calculate the distance.
        # Response needs to be updated to include the distance
        distance = "unknown"
        dispatcher.utter_message(text="Distance to destination is " + str(distance))
        return []


class ActionCheckTime(Action):
    def name(self) -> Text:
        return "action_check_time_to_destination"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Here should be a call to maps API to calculate the time
        # Response needs to be updated to include the time
        time = "unknown"
        dispatcher.utter_message(text="Time to destination is " + str(time))
        return []


class ActionStopNavigation(Action):
    def name(self) -> Text:
        return "action_stop_navigation"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(text="Navigation stopped.")
        return [dict(active_route=None)]


class ActionAnalyseSpeed(Action):
    def name(self) -> Text:
        return "action_analyse_speed"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        (
            average_diff,
            percent_correct_speed,
            average_diff_by_zones,
            percent_correct_speed_by_zones,
        ) = analyse_speed(speed_limits, actual_speed)
        if percent_correct_speed < 50:
            dispatcher.utter_message(
                text="You exceeded speed limits by more than half of the driving time. Could you drive more carefully next time?"
            )
        elif percent_correct_speed <= 80:
            dispatcher.utter_message(
                text="You drive with correct speed most of the time. Keep it up!"
            )
        else:
            dispatcher.utter_message(
                text="Congratulations! You are great at observing speed limits. Thanks for keeping yourself and others safe!"
            )

        for zone, percent in percent_correct_speed_by_zones.items():
            dispatcher.utter_message(
                text="In {0} zone, you drove correctly {1} percent of time today.".format(
                    zone, percent
                )
            )

        return []


#### all this replaced by forms
#### some parts not included in forms e.g. excluded stops, frequent destinations
#### these removed to simplify but can be added back when tested

# class ActionSearchPlaces(Action):
#     def name(self) -> Text:
#         return "action_search_places"

#     def run(
#         self,
#         dispatcher: CollectingDispatcher,
#         tracker: Tracker,
#         domain: Dict[Text, Any],
#     ) -> List[Dict[Text, Any]]:
#         entity_to = next(
#             tracker.get_latest_entity_values(entity_type="location_type"), None
#         )

#         # Here should be a call to a maps API searching for entity_to
#         options = ["option1", "option2", "option3"]
#         if len(options) == 1:
#             dispatcher.utter_message(text="One option found: " + options[0])
#         else:
#             dispatcher.utter_message(text="Options found: " + " and ".join(options))

#         return [
#             SlotSet("search_results", options),
#             SlotSet("search_results_count", len(options) == 1),
#         ]
#
#
# class ActionSelectPlace(Action):
#     def name(self) -> Text:
#         return "action_select_place"

#     def run(
#         self,
#         dispatcher: CollectingDispatcher,
#         tracker: Tracker,
#         domain: Dict[Text, Any],
#     ) -> List[Dict[Text, Any]]:
#         options = tracker.get_slot("search_results")
#         option = options[0]

#         entity_number = next(
#             tracker.get_latest_entity_values(entity_type="number"), None
#         )
#         if entity_number == "one":
#             option = options[0]
#         elif entity_number == "two":
#             option = options[1]
#         elif entity_number == "three":
#             option = options[2]

#         entity_to = tracker.get_slot("active_route")
#         slot_via = tracker.get_slot("via")

#         if slot_via is None:
#             slot_via = []

#         if entity_to is not None:
#             slot_via.append(option)
#             dispatcher.utter_message(text="Stop added: " + option)
#             return [SlotSet("via", option)]

#         else:
#             dispatcher.utter_message(text="Navigating to " + option)
#             return [SlotSet("active_route", option)]


# class ActionFindDestinaton(Action):
#     def name(self) -> Text:
#         return "action_find_destination"

#     def run(
#         self,
#         dispatcher: CollectingDispatcher,
#         tracker: Tracker,
#         domain: Dict[Text, Any],
#     ) -> List[Dict[Text, Any]]:
#         entity_to = next(
#             tracker.get_latest_entity_values(entity_type="location", entity_role="to"),
#             None,
#         )
#         entity_from = next(
#             tracker.get_latest_entity_values(
#                 entity_type="location", entity_role="from"
#             ),
#             None,
#         )
#         entity_via = next(
#             tracker.get_latest_entity_values(
#                 entity_type="location", entity_role="via"
#             ),
#             None,
#         )
#         entity_avoid = next(
#             tracker.get_latest_entity_values(
#                 entity_type="location", entity_role="avoid"
#             ),
#             None,
#         )
#         entity_road_type = next(tracker.get_latest_entity_values("road_type"), None)
#         entity_route_type = next(tracker.get_latest_entity_values("route_type"), None)

#         slot_active_route = tracker.get_slot("active_route")
#         slot_via = tracker.get_slot("via")

#         if entity_from is None:
#             entity_from = tracker.get_slot("from")

#         if slot_via is not None:
#             entity_via = slot_via.append(entity_via)

#         with open(DB, "r", encoding="utf-8") as db:
#             database = json.load(db)

#         if entity_to in database:
#             entity_to = database[entity_to]

#         if slot_active_route is None:
#             if entity_to:
#                 return [
#                     SlotSet("active_route", entity_to),
#                     SlotSet("from", entity_from),
#                     SlotSet("via", entity_via),
#                     SlotSet("avoid", entity_avoid),
#                     SlotSet("route_type", entity_route_type),
#                     SlotSet("road_type", entity_road_type),
#                 ]
#             else:
#                 destination = get_frequent_destination(
#                     json.load(open(DB, "r", encoding="utf-8"))
#                 )
#                 return [
#                     SlotSet("destination", destination),
#                     SlotSet("via", entity_to),
#                     SlotSet("from", entity_from),
#                     SlotSet("avoid", entity_avoid),
#                     SlotSet("route_type", entity_route_type),
#                     SlotSet("road_type", entity_road_type),
#                 ]
#         else:
#             return [
#                 SlotSet("via", entity_to),
#                 SlotSet("from", entity_from),
#                 SlotSet("avoid", entity_avoid),
#                 SlotSet("route_type", entity_route_type),
#                 SlotSet("road_type", entity_road_type),
#             ]
# def get_frequent_destination(
#     database, weeks_limit=5, weekly_events_min_count=3, daily_events_min_count=10
# ):
#     time_now = datetime.strptime("15.30 30.11.21", "%H.%M %d.%m.%y")  # datetime.now()
#     weekday_now = time_now.weekday()
#     hour_now = time_now.hour
#     time_limit = time_now - timedelta(weeks=weeks_limit)
#     time_limit = time_limit
#     destinations_by_day_and_time = Counter()
#     destinations_by_time = Counter()

#     if "destinations" in database:
#         for destination in database["destinations"]:
#             address, trip_date = destination
#             address = address.lower()
#             trip_date = datetime.strptime(trip_date, date_string_pattern)
#             weekday = trip_date.weekday()
#             hour = trip_date.hour

#             if trip_date >= time_limit:
#                 if weekday == weekday_now and hour == hour_now:
#                     destinations_by_day_and_time[address] += 1
#                 if hour == hour_now:
#                     destinations_by_time[address] += 1

#     if len(destinations_by_day_and_time) > 0 or len(destinations_by_time) > 0:
#         top_destination, count = destinations_by_day_and_time.most_common(1)[0]
#         if count >= weekly_events_min_count:
#             return top_destination
#         else:
#             top_destination, count = destinations_by_time.most_common(1)[0]
#             if count >= daily_events_min_count:
#                 return top_destination
#     return
# class ActionStartNavigation(Action):
#     def name(self) -> Text:
#         return "action_start_navigation"

#     def run(
#         self,
#         dispatcher: CollectingDispatcher,
#         tracker: Tracker,
#         domain: Dict[Text, Any],
#     ) -> List[Dict[Text, Any]]:

#         # get the active_route slot and save it to a database with the day of week and time
#         slot_active_route = tracker.get_slot("active_route")

#         # if active_route has not been set but there is a destination, navigate there
#         if slot_active_route is None:
#             slot_destination = tracker.get_slot("destination")
#             intent = tracker.latest_message["intent"].get("name")
#             if slot_destination and intent == "affirm":
#                 slot_active_route = slot_destination

#         time_now = datetime.now()

#         # load the current content of database.json
#         with open(DB, "r", encoding="utf-8") as db:
#             database = json.load(db)

#         destinations = database.get("destinations", [])
#         destinations.append(
#             (slot_active_route, time_now.strftime(date_string_pattern))
#         )
#         database.update({"destinations": destinations})

#         with open(DB, "w", encoding="utf-8") as db:
#             json.dump(database, db)

#         return [
#             SlotSet("active_route", slot_active_route),
#             SlotSet("destination", None),
#         ]

# class ActionExcludeStop(Action):
#     def name(self) -> Text:
#         return "action_exclude_stop"

#     def run(
#         self,
#         dispatcher: CollectingDispatcher,
#         tracker: Tracker,
#         domain: Dict[Text, Any],
#     ) -> List[Dict[Text, Any]]:
#         return []
# class ActionAddToDatabase(Action):
#     def name(self) -> Text:
#         return "action_add_to_database"

#     def run(
#         self,
#         dispatcher: CollectingDispatcher,
#         tracker: Tracker,
#         domain: Dict[Text, Any],
#     ) -> List[Dict[Text, Any]]:
#         entity_location = next(
#             tracker.get_latest_entity_values(entity_type="location"), None
#         )
#         entity_db_item_name = next(
#             tracker.get_latest_entity_values(
#                 entity_type="location", entity_role="to_database"
#             ),
#             None,
#         )

#         with open(DB, "r", encoding="utf-8") as db:
#             database = json.load(db)

#         database.update({entity_db_item_name: entity_location})

#         with open(DB, "w", encoding="utf-8") as db:
#             json.dump(database, db)

#         return []
