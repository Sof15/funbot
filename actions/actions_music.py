# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import requests
from dotenv import load_dotenv
import os 

load_dotenv()

class ActionGetSpotifyInfo(Action):
    def name(self) -> Text:
        return "action_display_spotify_info"

    def _get_spotify_info(self, dispatcher, artist: Text) -> Dict[Text, Any]:
        data = {
            'grant_type': 'client_credentials',
            'client_id': os.environ.get('SPOTIFY_CLIENT_ID'),
            'client_secret': os.environ.get('SPOTIFY_CLIENT_SECRET'),
        }
        res = requests.post(
            "https://accounts.spotify.com/api/token", 
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )

        url = 'https://api.spotify.com/v1/search'
        headersAPI = {
            'accept': 'application/json',
            'Authorization': "Bearer {}".format(res.json()['access_token']),
        }
        params = {
            **{
                'q':artist,
                'type':"playlist",
            }
        }
        res = requests.get(url, params, headers=headersAPI)
        if res.status_code == 401:
            dispatcher.utter_message(text="Not authorized to use Spotify API")
            return []
      
        if res.status_code == 200:
            results = res.json()
            try:
                dispatcher.utter_message(text=f"Here is a spotify playlist for the event: {artist} --> {results['playlists']['items'][0]['external_urls']['spotify']}:")
                tracks = requests.get(results['playlists']['items'][0]['tracks']['href'], headers=headersAPI)
                if tracks.status_code == 200:
                    tracks = tracks.json()
                    tracks = [track['track']['name'] for track in tracks['items']]
                    tracks_str = '\n'.join(tracks)
                    dispatcher.utter_message(text=f"Here is the list of tracks in the playlist:\n{tracks_str}")
                else:
                    dispatcher.utter_message(text=f"Sorry, I could not find the tracks for the playlist")
                    return []
            except:
                dispatcher.utter_message(text=f"Sorry, I could not find a playlist for the event: {artist}")
                return []
        else:
            dispatcher.utter_message(text="Sorry, I could not find a playlist for the event")
            return []
            


    def run(self, 
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]
        ) -> List[Dict[Text, Any]]:
 
        events_selected = tracker.get_slot("is_music")

        for event in events_selected:
            self._get_spotify_info(dispatcher, event)
        
        return []
    