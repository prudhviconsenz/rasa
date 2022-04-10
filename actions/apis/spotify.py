"""
setup:
    signup for spotify
    create app https://developer.spotify.com/dashboard/topics
    open app, edit settings, set redirect_url to http://localhost:11111 (any available port)
    
    auth required
        client_id, client_secret, redirect_url as keys in creds.yml
        ~/.spotify/creds.yml (local usage)
        /etc/rasa/credentials/.spotify/creds.yml (rasax server usage)
"""

import spotipy
import os
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
import yaml
import random
from ..defaultlog import log

try:
    # auth in rasa actions docker container
    with open("/app/credentials/.spotify/creds.yml") as f:
        creds = yaml.safe_load(f)
except FileNotFoundError:
    # auth locally using home folder
    log.warning("using creds from home folder")
    HOME = os.path.expanduser("~")
    with open(f"{HOME}/.spotify/creds.yml") as f:
        creds = yaml.safe_load(f)

# allows user details. slower rate limit. does not apepar to work on wsl2?
# sp = spotipy.Spotify(auth_manager=SpotifyOAuth(**creds, scope="user-library-read"))

# does not allow user details. does not have redirect_url
del creds["redirect_uri"]
auth_manager = SpotifyClientCredentials(**creds)
sp = spotipy.Spotify(auth_manager=auth_manager)


def search(q, type_):
    results = sp.search(q=q, type=type_)
    items = results["artists"]["items"]
    if len(items) > 0:
        artist = items[0]
        name, image, id = artist["name"], artist["images"][0]["url"], artist["id"]
    return name, image, id


def get_top(id):
    lz_uri = f"spotify:artist:{id}"
    results = sp.artist_top_tracks(lz_uri)
    for track in results["tracks"][:10]:
        print("track    : " + track["name"])
        print("audio    : " + track["preview_url"])
        print("cover art: " + track["album"]["images"][0]["url"])
        print()


def get_playlists():
    playlists = sp.user_playlists("spotify")
    while playlists:
        for i, playlist in enumerate(playlists["items"]):
            print(
                "%4d %s %s"
                % (i + 1 + playlists["offset"], playlist["uri"], playlist["name"])
            )
        if playlists["next"]:
            playlists = sp.next(playlists)
        else:
            playlists = None


def get_user_saved():
    results = sp.current_user_saved_tracks()
    for idx, item in enumerate(results["items"]):
        track = item["track"]
        print(idx, track["artists"][0]["name"], " – ", track["name"])


def get_track(album=None, artist=None, track=None):
    if album:
        album = album.lower()
    if artist:
        artist = artist.lower()
    if track:
        track = track.lower()

    items = []
    if track:
        results = sp.search(q=f"track:{track}", type="track")
        items = results["tracks"]["items"]
        if album:
            items = [x for x in items if x["album"]["name"].lower().find(album) >= 0]
        if artist:
            items = [x for x in items if x["artists"][0]["name"].lower() == artist]
    elif album:
        results = sp.search(q=f"album:{album}", type="track")
        items = results["tracks"]["items"]
        if artist:
            artists = [x["artists"][0]["name"].lower() for x in items]
            items = [x for x in items if x["artists"][0]["name"].lower() == artist]
    elif artist:
        results = sp.search(q=f"artist:{artist}", type="track")
        items = results["tracks"]["items"]
        if album:
            items = [x for x in items if x["album"][0]["name"].lower().find(album) >= 0]

    if len(items) == 0:
        return None
    track = random.choice(items)
    artist = track["artists"][0]["name"]
    if album:
        album = track["album"]["name"]
    track = track["name"]

    return album, artist, track


if __name__ == "__main__":

    # print(sp.current_user())
    # name, image, id = search("artist:bowie", "artist")
    # get_top(id)
    # print(name, image, id)
    # get_user_saved()

    # track = "eraser"
    # album, artist, track = get_track(track=track)
    # print(f" playing {track} by {artist}")

    # album = "The Dark Side of the Moon"
    # album, artist, track = get_track(album=album)
    # print(f" playing {track} from {album} by {artist}")

    # artist = "bowie"
    # album, artist, track = get_track(artist=artist)
    # print(f" playing {track} by {artist}")

    artist = "ed sheeeran"
    album = None
    track = "eraser"
    res = get_track(album, artist, track)
    if res is None:
        print("not found")
    else:
        album, artist, song = res
        message = f" playing {song} by {artist}"
        if album is not None:
            message = message + f" from {album}"
        print(message)

    # todo genre, playlist, dates
    # todo multiple inputs. how should they be combined?
    # artist = "the Beatles"
    # album = "Abbey Road"
    # results = sp.search(q=f"artist:{artist} album:{album}", type="track")
    # print(results["tracks"]["items"][0].keys())
    # # track = random.choice(results["tracks"])["name"]
    # print(track)
