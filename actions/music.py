from typing import Any, Dict, List, Text

from rasa_sdk import Action, FormValidationAction, Tracker
from rasa_sdk.events import AllSlotsReset, Restarted, SlotSet, EventType
from rasa_sdk.executor import CollectingDispatcher
from .apis.spotify import get_track
from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict

import logging

log = logging.getLogger(__name__)

class ValidateMusicPlayForm(FormValidationAction):
    def name(self):
        return "validate_music_play_form"

    def validate_artist(*args, **kwargs):
        """ any of these can be used on their own or together """
        return dict(requested_slot=None)

    def validate_genre(*args, **kwargs):
        return dict(requested_slot=None)

    def validate_genre(*args, **kwargs):
        return dict(requested_slot=None)

    def validate_playlist(*args, **kwargs):
        return dict(requested_slot=None)

    def validate_album(*args, **kwargs):
        return dict(requested_slot=None)

    def validate_song(*args, **kwargs):
        return dict(requested_slot=None)

class SubmitMusicPlayForm(Action):
    def name(self):
        return "submit_music_play_form"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        log.debug("submit_music_play form")
        
        reset = [
            SlotSet(x, None) for x in ["genre", "playlist", "artist", "album", "song"]
        ]
        # get song details from spotify
        genre = tracker.get_slot("genre")
        playlist = tracker.get_slot("playlist")
        album = tracker.get_slot("album")
        artist = tracker.get_slot("artist")
        song = tracker.get_slot("song")

        if genre:
            dispatcher.utter_message(text=f"playing genre {genre}")
            return reset
        if playlist:
            dispatcher.utter_message(text=f"playing playlist {playlist}")
            return reset

        res = get_track(album, artist, song)
        if res is None:
            dispatcher.utter_message("unable to locate song")
            return reset

        album, artist, song = res

        if not song:
            dispatcher.utter_message("unable to locate song")
            return reset

        if tracker.get_slot("album"):
            dispatcher.utter_message(
                response="utter_play_album", album=album, artist=artist, song=song
            )
        else:
            dispatcher.utter_message(
                response="utter_play_song", artist=artist, song=song
            )
        return reset
