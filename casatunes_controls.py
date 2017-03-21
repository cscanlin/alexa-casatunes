import boto3
import logging
import os
import requests

from flask import Flask, json
from flask_ask import Ask, statement, request
from sshtunnel import SSHTunnelForwarder
from utils import load_casa_config, parse_app_status, parse_search_request, parse_search_response

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
        'localhost', CASA_CONFIG['SERVICE_ROUTE'], endpoint
    ))

def casa_command(endpoint, data=None):
    data = data if data else {'ZoneID': 0}

    s3_client = boto3.client('s3')
    s3_client.download_file('alexa-casatunes', 'keys/id_rsa', '/tmp/id_rsa')

    with SSHTunnelForwarder(
        (os.getenv('CASA_SERVER_IP'), 22222),
        ssh_username='casa',
        ssh_password=os.getenv('CASA_SSH_PASSWORD'),
        remote_bind_address=('localhost', 25)
    ):
        data = data if data else {'ZoneID': 0}
        return requests.post(
            casa_route(endpoint),
            headers=CASA_CONFIG['HEADERS'],
            data=json.dumps(data)
        )

def speech_response(speech_text):
    logger.info(speech_text)
    return statement(speech_text).simple_card(request.type, speech_text) if request else speech_text

@app.route('/')
@ask.intent('HelloIntent')
def hello():
    speech_text = 'Hello Chris'
    logger.info(speech_text)
    return speech_response(speech_text)

@app.route('/play')
@ask.intent('AMAZON.ResumeIntent')
@ask.intent('CasaPlay')
def play_song():
    casa_command(endpoint='PlaySong')
    speech_text = 'Playing casa tunes'
    return speech_response(speech_text)

@app.route('/pause')
@ask.intent('AMAZON.PauseIntent')
def pause_song():
    casa_command(endpoint='PauseSong')
    speech_text = 'Pausing casa tunes'
    return speech_response(speech_text)

@ask.intent('AMAZON.PreviousIntent')
def previous_song():
    casa_command(endpoint='PreviousSong')
    speech_text = 'Playing previous song on casa tunes'
    return speech_response(speech_text)

@ask.intent('AMAZON.NextIntent')
def next_song():
    casa_command(endpoint='NextSong')
    speech_text = 'Playing next song on casa tunes'
    return speech_response(speech_text)

@ask.intent('CasaTurnRoomOn', mapping={'room': 'Room'}, default={'room': CASA_CONFIG['DEFAULT_ROOM']})
def turn_room_on(room):
    casa_command(
        endpoint='SetZonePower',
        data={
            'Power': True,
            'ZoneID': str(CASA_CONFIG['ROOM_ZONE_MAP'][room.lower()]),
        },
    )
    speech_text = 'Turning on music in {room}'.format(room=room)
    return speech_response(speech_text)

@ask.intent('CasaTurnRoomOff', mapping={'room': 'Room'})
def turn_room_off(room):
    casa_command(
        endpoint='SetZonePower',
        data={
            'Power': False,
            'ZoneID': str(CASA_CONFIG['ROOM_ZONE_MAP'][room.lower()]),
        },
    )
    speech_text = 'Turning off music in {room}'.format(room=room)
    return speech_response(speech_text)

@ask.intent('CasaSetRoomVolume', mapping={'room': 'Room', 'new_volume': 'Volume'})
def set_room_volume(room, new_volume):
    casa_command(
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
    status_response = casa_command(endpoint='GetAppStatus')
    app_status = parse_app_status(status_response)
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
    parsed_search_response = parse_search_response(search_response)
    first_requested_item_id = parsed_search_response[requested_object_type][0]['ID']

    casa_command(
        endpoint='PlayMediaCollectionOrItem2',
        data={
            'ZoneID': DEFAULT_ZONE,
            'ItemID': first_requested_item_id,
            'Filter': None,
            'AddToQueue': QUEUE_SPOT_MAP[CASA_CONFIG['DEFAULT_QUEUE_TYPE']],
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
