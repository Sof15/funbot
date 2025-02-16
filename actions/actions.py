# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa.core.tracker_store import InMemoryTrackerStore
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import requests
import pycountry
import calendar 
import json
from dotenv import load_dotenv
import os

load_dotenv()

CLASSIFICATION_MAP = {
    'Sports': "KZFzniwnSyZfZ7v7nE",
    'Music': "KZFzniwnSyZfZ7v7nJ",
    'Arts & Theatre': "KZFzniwnSyZfZ7v7na",
    'Film': "KZFzniwnSyZfZ7v7nn",
}

class ActionGetTimeWithGrain(Action):
    def name(self):
        return 'action_get_time_w_grain'

    def run(self, dispatcher, tracker, domain):
        # duckling extracted time 
        entity = [
            entity for entity in list(tracker.latest_message['entities']) 
            if (entity['entity']=='time' and entity['extractor']=='DucklingEntityExtractor')
        ][0]
        
        value = entity['value']
        
        if isinstance(value, str):
                return {"time": value}

        if isinstance(value, dict):
            return [SlotSet("time", {"from": value["from"], "to": value["to"]})]

        grain = entity['additional_info']['grain']
        
     
        if grain == "month":
            current_month = value.split('-')[1]
            if current_month == '12':
                end_value = str(int(value.split('-')[0])+1) + '-' + '01' + '-' + value.split('-')[2]
            else:
                end_value = value.split('-')[0] + '-' + str(int(value.split('-')[1])+1).zfill(2) + '-' + value.split('-')[2]
        elif grain == "day":
            current_day = int(value.split('-')[2].split('T')[0])
            _, max_days = calendar.monthrange(int(value.split('-')[0]),int(value.split('-')[1]))
            if current_day == max_days:
                end_value = value.split('-')[0] + '-' + str(int(value.split('-')[1])+1) + '-01' + value.split('-')[2].split('T')[1]
            else:
                end_value = value.split('-')[0] + '-' + value.split('-')[1] + '-' + str(current_day+1).zfill(2) + value.split('-')[2].split('T')[1]
            
        return [SlotSet("time", {"from": value, "to": end_value})]

class ValidateListEventsForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_list_events_form"

    async def required_slots(
        self,
        domain_slots: List[Text],
        dispatcher: "CollectingDispatcher",
        tracker: "Tracker",
        domain: "DomainDict",
    ) -> List[Text]:
        updated_slots = domain_slots.copy()

        if tracker.slots.get("city") is not None:
            updated_slots.remove("country")

        if tracker.slots.get("country") is not None:
            updated_slots.remove("city")
        
        return updated_slots

    def validate_time(
        self,
        slot_value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:

        if slot_value: 
            # duckling extracted time 
            entity = [
                entity for entity in list(tracker.latest_message['entities']) 
                if (entity['entity']=='time' and entity['extractor']=='DucklingEntityExtractor')
            ][0]
            
            value = entity['value']

            if isinstance(value, str):
                return {"time": value}

            if isinstance(value, dict):
                return {"time": {"from": value["from"], "to": value["to"]}}

            grain = entity['additional_info']['grain']
            
        
            if grain == "month":
                current_month = value.split('-')[1]
                if current_month == '12':
                    end_value = str(int(value.split('-')[0])+1) + '-' + '01' + '-' + value.split('-')[2]
                else:
                    end_value = value.split('-')[0] + '-' + str(int(value.split('-')[1])+1).zfill(2) + '-' + value.split('-')[2]
            elif grain == "day":
                current_day = int(value.split('-')[2].split('T')[0])
                _, max_days = calendar.monthrange(int(value.split('-')[0]),int(value.split('-')[1]))
                if current_day == max_days:
                    end_value = value.split('-')[0] + '-' + str(int(value.split('-')[1])+1) + '-01' + value.split('-')[2].split('T')[1]
                else:
                    end_value = value.split('-')[0] + '-' + value.split('-')[1] + '-' + str(current_day+1).zfill(2) + value.split('-')[2].split('T')[1]
                
            return {"time": {"from": value, "to": end_value}}
        dispatcher.utter_message(text="What date/time or date/time period are you interested in ?")
        return {"time": None}

    def validate_city(
        self,
        slot_value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:

        if slot_value: 
            return {"city": slot_value}
        if tracker.get_slot("country"):
            # we have a location entry 
            # so don't ask for further info
            return {"city": None}
        dispatcher.utter_message(text="Which location are you interested in?")
        return {"city": None}

    def validate_country(
        self,
        slot_value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:

        if slot_value: 
            return {"country": slot_value}
        if tracker.get_slot("city"):
            # we have a location entry 
            # so don't ask for further info
            return {"country": None}
        dispatcher.utter_message(text="Which location are you interested in?")
        return {"country": None}


class ActionGetEvents(Action):
    def name(self) -> Text:
        return "action_get_events"

    def _get_genres(self, classification_id) -> list:
        url = f'https://app.ticketmaster.com/discovery/v2/classifications/{classification_id}'
        params = {
            "apikey" : os.getenv('TICKETMASTER_KEY'),
            "locale" : "*"
        }
        res = requests.get(url, params)
        if res.status_code == 200:
            result = res.json()
            return {el['name']:el['id'] for el in result['segment']['_embedded']['genres']}
            

    def run(self, 
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]
        ) -> List[Dict[Text, Any]]:
 
        genre = tracker.get_slot("segment")
        classification = tracker.get_slot("classification")
        country = tracker.get_slot("country")
        city = tracker.get_slot("city")
        time = tracker.get_slot("time")

        if time is None:
            return []
       
        if isinstance(time, str):
            start_datetime = time.replace(':'.join(time.split(':')[1:]), '00:00Z')
            end_datetime = time.replace(':'.join(time.split(':')[1:]), '00:00Z')

        if isinstance(time, dict):
            start_datetime = time['from'].replace(':'.join(time['from'].split(':')[1:]), '00:00Z')            
            end_datetime = time['to'].replace(':'.join(time['to'].split(':')[1:]), '00:00Z')
        
        
        params = {}

        if classification is not None:

            for key, value in CLASSIFICATION_MAP.items():
                if classification.lower() == key.lower():
                    params['classificationName'] = key
                    if genre is not None:
                        genres = self._get_genres(value)
                        for genre_name, genre_id in genres.items():
                            if genre_name.lower() == genre.lower():
                                params['genreId'] = genre_id
        if country is not None:
            country = pycountry.countries.search_fuzzy(country)[0].alpha_2
            params['countryCode'] = country
        if city is not None:
            params['city'] = city

        url = 'https://app.ticketmaster.com/discovery/v2/events'
        params = {
            **params, 
            **{
                "apikey" : os.getenv('TICKETMASTER_KEY'),
                "locale" : "*",
                "startDateTime": start_datetime,
                "endDateTime": end_datetime,
                "page": 0
            }
        }
        res = requests.get(url, params)
        if res.status_code == 200:
            response = res.json()
            if response['page']['totalElements'] == 0:
                events_names = []
                dispatcher.utter_message(
                    f"No events found for the given parameters"
                )
            else:
                events = res.json()['_embedded']['events']
                events_names = [event['name'] for event in events]
                events_links = [event['url'] for event in events]
                events_ids = [event['id'] for event in events]
                events_names_str = '\n'.join([f'{ii+1}. '+tup[0]+' ---> '+tup[1] for ii,tup in enumerate(zip(events_names,events_links))])
                dispatcher.utter_message(
                    f"Here is the list of all events:\n\n{events_names_str}"
                )

        return [SlotSet("events", list({'id': events_ids[ii], 'name': events_names[ii], 'url': events_links[ii]} for ii in range(len(events_names))))]
    
class ActionClearListEventsSlots(Action):
    def name(self) -> Text:
        return "action_clear_list_events_slots"
            

    def run(self, 
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]
        ) -> List[Dict[Text, Any]]:
        
        return [SlotSet("city", None),
                SlotSet("time", None),
                SlotSet("country", None),
                SlotSet("classification", None),
                SlotSet("segment", None)]

class ActionSaveEvent(Action):
    def name(self) -> Text:
        return "action_save_event"
            

    def run(self, 
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]
        ) -> List[Dict[Text, Any]]:
        
        events = tracker.get_slot("events")
        identifiers = tracker.get_slot('number')
        save_events = [events[int(el)-1] for el in identifiers]

        # load already saved events
        try:
            with open('favorites.json', 'r') as f:
                favorites = json.load(f)
        except FileNotFoundError as e:
            favorites = {'events':[]}

        # store already saved events 
        # plus the new event
        with open('favorites.json', 'w') as f:
            json.dump({'events':save_events+favorites['events']}, f)
        dispatcher.utter_message(
            f"Events saved successfully."
        )
        return []

class ActionDisplaySavedEvents(Action):
    def name(self) -> Text:
        return "action_display_saved_events"
            

    def run(self, 
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]
        ) -> List[Dict[Text, Any]]:
        
        # load already saved events
        try:
            with open('favorites.json', 'r') as f:
                favorites = json.load(f)
                favorites_str = "\n".join([' ---> '.join([event['name'], event['url']]) for event in favorites['events']])
                dispatcher.utter_message(
                    f"Here is the list of saved events:\n{favorites_str}"
                )
        except FileNotFoundError as e:
            dispatcher.utter_message(
                f"No bookmarked events"
            )

        return []


class ActionGetEventInfo(Action):
    def name(self) -> Text:
        return "action_get_event_info"
            
    def _get_event_info(self, dispatcher, event_id):
        url = f'https://app.ticketmaster.com/discovery/v2/events/{event_id}'
        params = {
            **{
                "apikey" : os.getenv('TICKETMASTER_KEY'),
                "locale" : "*"
            }
        }
        res = requests.get(url, params)
        if res.status_code == 200:
            response = res.json()
            is_music = None
            try:
                display_info = f"Details for event:{response['name']} promoted by: {response['promoter']['name']}"
                dispatcher.utter_message(display_info)
            except:
                dispatcher.utter_message(f"Details for event:{response['name']} (promoter not available)")
            try:
                dispatcher.utter_message(f"Price: {response['priceRanges'][0]['min']} - {response['priceRanges'][0]['max']} {response['priceRanges'][0]['currency']}")
            except:
                dispatcher.utter_message(f"Price: Not available")
            
            dispatcher.utter_message(f"Here are the classifications for the event:")
            for clf in response['classifications']:
                if is_music is None:
                    if (clf['segment']['name'] == 'Music'):
                        is_music = response['_embedded']['attractions'][0]['name']
                display_dict = {
                    'Segment': clf['segment']['name'] if 'segment' in clf else None,
                    'Genre': clf['genre']['name'] if 'genre' in clf else None,
                    'Subgenre': clf['subGenre']['name'] if 'subGenre' in clf else None
                }
                dispatcher.utter_message("\t".join([f"{key}: {value}" for key, value in display_dict.items() if value is not None]))
            

            return is_music

        elif res.status_code == 404:
            dispatcher.utter_message(
                f"Event details not found."
            )
            return None
        else:
            dispatcher.utter_message(
                f"An error occurred while fetching event details."
            )
            return None
            

    def run(self, 
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]
        ) -> List[Dict[Text, Any]]:
        

        if tracker.latest_message['intent']['name'] != 'display_event_info':
            return []

        identifiers = tracker.get_slot("number")
        events = tracker.get_slot("events")

        if events is None:
            dispatcher.utter_message(text="No recent search on events. What kind of events are you interested in?")
            return []

        events_selected = [events[int(eid)-1] for eid in identifiers]

        if identifiers is None:
            dispatcher.utter_message(text="Please provide one or more events identifiers.")
            return []

        is_music_names = []
        for event in events_selected:
            is_music = self._get_event_info(dispatcher, event['id'])
            if is_music is not None:
                is_music_names.append(is_music)

        return [SlotSet("is_music", is_music_names)]