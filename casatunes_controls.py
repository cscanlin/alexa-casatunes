import boto3
import logging
import os
import paramiko

from flask import Flask, json, abort
from flask_ask import Ask, statement, request, session
from utils import load_casa_config, parse_app_status, parse_search_request, parse_search_response, search_speech_text

logger = logging.getLogger('flask_ask')
logger.setLevel(logging.DEBUG)

app = Flask(__name__)
ask = Ask(app, '/')

app.url_map.strict_slashes = False

CASA_CONFIG = load_casa_config('casa_config.json')

DEBUG = os.getenv('CASA_SERVER_IP') in CASA_CONFIG['LOCAL_SERVER_ROUTE']

SERVICE_ROUTE = 'CasaTunes/CasaService.svc'
CASA_HEADERS = {'Content-Type': 'application/json'}

DEFAULT_QUEUE_TYPE = 'ADD_AND_PLAY'

QUEUE_SPOT_MAP = {
    'ADD_AND_PLAY': 2,
}

ALEXA_CASA_TYPE_MAP = {
    'artist': 'Artists',
    'album': 'Albums',
    'song': 'Tracks',
    'genre': 'Playlists',
}

def casa_route(endpoint):
    return '/'.join((
        CASA_CONFIG['LOCAL_SERVER_ROUTE'], SERVICE_ROUTE, endpoint
    ))

def casa_command(endpoint, data=None):
    # if request is not None:
    #     logger.debug(json.dumps(request))

    if DEBUG or (session and session.user.userId in os.getenv('ALEXA_USER_ID').split(';')):
        pass
    else:
        abort(403)

    data = data if data else {'ZoneID': 0}

    s3_client = boto3.client('s3')
    s3_client.download_file('alexa-casatunes', 'keys/casa_rsa', '/tmp/casa_rsa')

    with paramiko.SSHClient() as ssh:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=os.getenv('CASA_SERVER_IP'),
            username='casa',
            password=os.getenv('CASA_SSH_PASSWORD'),
            key_filename='/tmp/casa_rsa',
            port=22222,
        )
        headers = ' '.join(['-H "{}: {}"'.format(k, v) for k, v in CASA_HEADERS.items()])
        command = 'curl -X POST {headers} -d \'{data}\' {route}'.format(
            headers=headers,
            data=json.dumps(data),
            route=casa_route(endpoint),
        )
        _, stdout, stderr = ssh.exec_command(command)
        response_data = json.loads(stdout.read())

        logger.debug(json.dumps(response_data))
        return response_data

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

@ask.intent('CasaTurnRoomOn', mapping={'room': 'Room'}, default={'room': CASA_CONFIG['DEFAULT_ZONE']})
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
            'ZoneID': str(CASA_CONFIG['ROOM_ZONE_MAP'][room.lower()]),
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
    parsed_request = parse_search_request(request)
    casa_creative_type = ALEXA_CASA_TYPE_MAP[parsed_request['creative_type']]
    logger.debug(json.dumps(parsed_request))

    search_response_data = casa_command(
        endpoint='SearchMediaCollectionByZone',
        data={
            'ZoneID': str(CASA_CONFIG['DEFAULT_ZONE']),
            'SearchCurrentMusicServiceOnly': True,
            'Searchtext': parsed_request['search_text'],
        },
    )
    parsed_search_response = parse_search_response(search_response_data)
    first_requested_item_id = parsed_search_response[casa_creative_type][0]['ID']

    casa_command(
        endpoint='PlayMediaCollectionOrItem2',
        data={
            'ZoneID': str(CASA_CONFIG['DEFAULT_ZONE']),
            'ItemID': first_requested_item_id,
            'Filter': None,
            'AddToQueue': QUEUE_SPOT_MAP[DEFAULT_QUEUE_TYPE],
        },
    )

    return speech_response(search_speech_text(parsed_request))

if __name__ == '__main__':
    app.run(debug=DEBUG)
