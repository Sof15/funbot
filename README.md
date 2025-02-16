# Funbot  

## Installation
1. Create virtual environment  
`python3.10 -m venv env`  
2. Activate virtual environment  
`source env/bin/activate`
3. Install dependencies  
`pip install -r requirements.txt`

## Necessary Setup

1. Follow the instructions [here](https://developer.ticketmaster.com/products-and-docs/apis/getting-started/) to get the ticketmaster API access key
2. Follow the instructions [here](https://developer.spotify.com/documentation/web-api/tutorials/getting-started) to create a set of client id and secret
3. Create a `.env` file and set `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET` AND `TICKETMASTER_KEY` accordingly.
4. docker run -p 8000:8000 rasa/duckling
5. rasa actions run
6. rasa train 
7. rasa shell [for chatting]

## Domain
Funbot is an entertainment assistant that integrates data from ticketmaster
and also spotify.  
The motivation behind the choice of this bot development lies in the need of 
the users to communicate using their natural language.   
It also, makes it easier for older people and generally people not familiar with technology to have a better exposure to the available events.  

## Scenarios:
1. List of available events. Converts natural language to API requests to extract relevant information.
2. Ask for further information on one or more specific event(s). For the set of selected events that are of type "Music", further information are given using the Spotify API.
3. Bookmarks. Users are allowed to save and display their favourite events. 

## Challenges:
- time entity extraction: 
Sometimes there is relevant time information given by the user e.g. this month, this summer, today, tonight, tomorrow at 4pm etc. This is sometimes handled automatically but some other times a special handling is required. We implemented some cases. However further QA is required to make sure a good coverage of cases is covered.
- multi slot scenarios:  
Scenarios like the first one (list events) has a lot of slots. Two of them are considered required (location, time). Location is expressed as either city or country or even both. We had to make sure this requirement is respected, so we used a form. Also, this dynamic slots behavior should be carefully managed with respective validation class. In addition, since we are talking about a multi-turn conversation with the bot, sudden interruption was also considered.
- entity recognition from more than one extractors:  
This happened with numbers and time, that were both extracted by Duckling and DIET. We had to remove annotations from training examples to allow only Duckling to extract these entities and prevent DIET to train on these entities recognition.

## Examples:
More details about specific scenarios and demostration can be found in the [presentation](https://docs.google.com/presentation/d/15C5OOdT-BOARI1JrkiIYJA_xAy4SDlWAOGJZaxZDHCg/edit?usp=sharing)