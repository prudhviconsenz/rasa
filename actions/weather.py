from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher

import os
import requests as req
from datetime import datetime
from ctparse import ctparse
import logging

log = logging.getLogger(__name__)


# OPEN WEATHER MAP --> https://openweathermap.org/api/one-call-api
# create your own account, get your api key
# subscribe: Current Weather Data and One Call API
OPEN_WEATHER_MAP_API_KEY = os.environ["OPEN_WEATHER_MAP_API_KEY"]
OPEN_WEATHER_MAP_API_ENDPOINT = "https://api.openweathermap.org/data/2.5/onecall"

# https://positionstack.com/documentation
# get the Geo-coordinates from city or place name
POSITION_STACK_API_KEY = os.environ["POSITION_STACK_API_KEY"]
POSITION_STACK_API_ENDPOINT = "http://api.positionstack.com/v1/forward"


def api_connector(location, unit):
    parameters_long_let = {
        "access_key": POSITION_STACK_API_KEY,
        "query": str(location),
    }

    res_long_let = req.get(url=POSITION_STACK_API_ENDPOINT, params=parameters_long_let)

    lon = res_long_let.json()["data"][0]["longitude"]
    lat = res_long_let.json()["data"][0]["latitude"]

    parameters_owm = {
        "lat": lat,
        "lon": lon,
        "exclude": "minutely,hourly",
        "appid": OPEN_WEATHER_MAP_API_KEY,
        "units": unit,
    }

    res_owm = req.get(url=OPEN_WEATHER_MAP_API_ENDPOINT, params=parameters_owm)
    return res_owm


def time_delta(time):
    today = datetime.today()
    try:
        date = datetime.strptime(time[:10], "%Y-%m-%d")
    except:
        parser = ctparse(time, ts=today, latent_time=False)
        date = datetime.strptime(str(parser.resolution).split(" ")[0], "%Y-%m-%d")
    delta = (date.date() - today.date()).days
    return delta


def get_time_text(time, tracker):
    """ return original text from time 
    value from duckling is date string. may need original text such as "tomorrow"
    """
    try:
        time_ent = [
            e for e in tracker.latest_message["entities"] if e["entity"] == "time"
        ][-1]
        time = time_ent.get("text", "time")
        # TODO can remove time from diet training and ctparse above if this warning does not heppen
        if time_ent["extractor"] != "DucklingEntityExtractor":
            log.warning("time was not extracted by duckling")
    except IndexError:
        pass

    return time


class Weather(Action):
    def name(self) -> Text:
        return "weather_handler"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        defaults = dict(location="London", time="today")

        location = tracker.get_slot("location")
        unit = tracker.get_slot("unit")
        time = tracker.get_slot("time")

        # connect to APIs
        response = api_connector(location, unit)
        if response.status_code != 200:
            dispatcher.utter_message("Sorry, I can't connect to the weather API")
            return defaults
        # retrieve exact day difference from today's date
        delta = time_delta(time)
        time = get_time_text(time, tracker)

        # today
        if delta == 0:
            temp = round(response.json()["current"]["temp"])
            dispatcher.utter_message(
                text=f"current temperature in {location} is {temp} Celsius"
            )
            return defaults

        # forecasting
        # only one-call api works for 7 days forecasting
        elif (delta > 0) and (delta <= 7):
            temp = round(response.json()["daily"][delta]["temp"]["day"])
            dispatcher.utter_message(
                text=f"The temperature in {location} {time} will be {temp} Celsius"
            )
            return defaults

        dispatcher.utter_message(
            text=f"api only works for 7 days forecasting, please try again"
        )


class WeatherTemperature(Action):
    def name(self) -> Text:
        return "weather_handler_temperature"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        location = tracker.get_slot("location")
        unit = tracker.get_slot("unit")
        time = tracker.get_slot("time")
        hotcold = tracker.get_slot("hotcold")

        response = api_connector(location, unit)

        delta = time_delta(time)
        time = get_time_text(time, tracker)

        if delta == 0:
            temp = round(response.json()["current"]["temp"])
            # check cold or not
            if hotcold.lower() == "cold":
                if temp <= 15:
                    dispatcher.utter_message(
                        text=f"Current temperature in {location} is {temp} Celsius, it's cold"
                    )
                else:
                    dispatcher.utter_message(
                        text=f"Current temperature in {location} is {temp} Celsius, it's not cold"
                    )
                return []

            # check warm or not
            if hotcold.lower() == "warm":
                if temp >= 20:
                    dispatcher.utter_message(
                        text=f"Current temperature in {location} is {temp} Celsius, it's warm"
                    )
                else:
                    dispatcher.utter_message(
                        text=f"Current temperature in {location} is {temp} Celsius, it's not warm"
                    )
                return []

            # check hot or not
            if hotcold.lower() == "hot":
                if temp >= 30:
                    dispatcher.utter_message(
                        text=f"Current temperature in {location} is {temp} Celsius, it's hot"
                    )
                else:
                    dispatcher.utter_message(
                        text=f"Current temperature in {location} is {temp} Celsius, it's not hot"
                    )
                return []

        # only one-call api works for 7 days forecasting
        elif delta > 0:
            temp = round(response.json()["daily"][delta]["temp"]["day"])
            # check cold or not
            if hotcold.lower() == "cold":
                if temp <= 8:
                    dispatcher.utter_message(
                        text=f"Temperature in {location} {time} will be {temp}, it's will be cold"
                    )
                else:
                    dispatcher.utter_message(
                        text=f"Temperature in {location} {time} will be {temp}, it's will not cold"
                    )
                return []
            return []

        dispatcher.utter_message(
            text=f"api only works for 7 days forecasting, please try again"
        )
