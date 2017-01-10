import logging

from flask import Flask, json
from flask_ask import Ask, statement, request

import requests

from utils import load_casa_config, parse_app_status, parse_search_request, parse_search_response

from pprint import pprint

logger = logging.getLogger('flask_ask')
logger.setLevel(logging.INFO)

app = Flask(__name__)
ask = Ask(app, '/')

CASA_CONFIG = load_casa_config('casa_config.json')
DEFAULT_ZONE = str(CASA_CONFIG['ROOM_ZONE_MAP'][CASA_CONFIG['DEFAULT_ROOM'].lower()])

QUEUE_SPOT_MAP = {
    'ADD_AND_PLAY': 2,
}

ALEXA_CASA_TYPE_MAP = {
    'artist': 'Artists',
    'album': 'Albums',
    'song': 'Tracks',
}

def casa_route(endpoint):
    return '/'.join((
        CASA_CONFIG['SERVER_IP'], CASA_CONFIG['SERVICE_ROUTE'], endpoint
    ))

def casa_command(endpoint, data={'ZoneID': 0}):
    return requests.post(
        casa_route(endpoint),
        headers=CASA_CONFIG['HEADERS'],
        data=json.dumps(data)
    )

def speech_response(speech_text):
    logger.info(speech_text)
    return statement(speech_text).simple_card(request.type, speech_text)

@ask.intent('AMAZON.ResumeIntent')
@ask.intent('CasaPlay')
def play_song():
    r = casa_command(endpoint='PlaySong')
    speech_text = 'Playing casa tunes'
    return speech_response(speech_text)

@ask.intent('AMAZON.PauseIntent')
def pause_song():
    r = casa_command(endpoint='PauseSong')
    speech_text = 'Pausing casa tunes'
    return speech_response(speech_text)

@ask.intent('AMAZON.PreviousIntent')
def previous_song():
    r = casa_command(endpoint='PreviousSong')
    speech_text = 'Playing previous Song on casa tunes'
    return speech_response(speech_text)

@ask.intent('AMAZON.NextIntent')
def next_song():
    r = casa_command(endpoint='NextSong')
    speech_text = 'Playing next Song on casa tunes'
    return speech_response(speech_text)

@ask.intent('CasaTurnRoomOn', mapping={'room': 'Room'})
def turn_room_on(room):
    if room is None:
        room = CASA_CONFIG['DEFAULT_ROOM']
    r = casa_command(
        endpoint='SetZonePower',
        data={
            'Power': True,
            'ZoneID': str(CASA_CONFIG['ROOM_ZONE_MAP'][room.lower()]),
        },
    )
    speech_text = 'Turning on music in {room}'.format(room=room),
    return speech_response(speech_text)

@ask.intent('CasaTurnRoomOff', mapping={'room': 'Room'})
def turn_room_off(room):
    r = casa_command(
        endpoint='SetZonePower',
        data={
            'Power': False,
            'ZoneID': str(CASA_CONFIG['ROOM_ZONE_MAP'][room.lower()]),
        },
    )
    speech_text = 'Turning off music in {room}'.format(room=room),
    return speech_response(speech_text)

@ask.intent('CasaSetRoomVolume', mapping={'room': 'Room', 'new_volume': 'Volume'})
def set_room_volume(room, new_volume):
    r = casa_command(
        endpoint='SetZoneVolume',
        data={
            'Volume': new_volume,
            'ZoneID': str(CASA_CONFIG['ROOM_ZONE_MAP'][room.lower()])
        },
    )
    speech_text = 'Setting volume in {room} to {new_volume}'.format(
        room=room, new_volume=new_volume
    )
    return speech_response(speech_text)

# NOW PLAYING

@ask.intent('AMAZON.SearchAction<object@MusicRecording[byArtist]>')
@ask.intent('AMAZON.SearchAction<object@MusicRecording[inAlbum]>')
def now_playing_info():
    r = casa_command(endpoint='GetAppStatus')
    app_status = parse_app_status(casa_response=r)
    speech_text = 'This song is called {title} by {artists} from the album {album}'.format(**app_status)
    return speech_response(speech_text)

# SEARCH
@ask.intent('AMAZON.SearchAction<object@MusicCreativeWork>')
def find_and_play_song():
    search_data = parse_search_request(request)
    requested_object_type = ALEXA_CASA_TYPE_MAP[search_data['creative_type']]

    search_response = casa_command(
        endpoint='SearchMediaCollectionByZone',
        data={
            'ZoneID': DEFAULT_ZONE,
            'SearchCurrentMusicServiceOnly': True,
            'Searchtext': search_data['creative_name'],
        },
    )
    parsed_response = parse_search_response(search_response)
    first_requested_item_id = parsed_response[requested_object_type][0]['ID']

    casa_command(
        endpoint='PlayMediaCollectionOrItem2',
        data={
            'ZoneID': DEFAULT_ZONE,
            'ItemID': first_requested_item_id,
            'Filter': None,
            'AddToQueue': QUEUE_SPOT_MAP['ADD_AND_PLAY'],
        },
    )

    speech_text = 'playing'
    if search_data['creative_type']:
        speech_text += ' the {creative_type} {creative_name}'.format(**search_data)
        if search_data['artist']:
            speech_text += ' by'
    if search_data['artist']:
        speech_text += ' {}'.format(search_data['artist'])
    return speech_response(speech_text)

if __name__ == '__main__':
    app.run(debug=True)
