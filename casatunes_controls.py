import logging
import os

from flask import Flask, json, abort, g
from flask_ask import Ask, statement, request, session

from casa_service import CasaSSHService
from utils import match_room_input, parse_app_status, parse_search_request, parse_search_response, search_speech_text

logger = logging.getLogger('flask_ask')
logger.setLevel(logging.DEBUG)

app = Flask(__name__)
ask = Ask(app, '/')

app.url_map.strict_slashes = False

DEBUG = os.getenv('ALEXA_CASA_ENV') == 'dev'

DEFAULT_ZONE = 0

DEFAULT_QUEUE_TYPE = 'ADD_AND_PLAY'

QUEUE_SPOT_MAP = {
    'ADD_AND_PLAY': 2,
}

ALEXA_CASA_TYPE_MAP = {
    'artist': 'Artists',
    'album': 'Albums',
    'song': 'Tracks',
    'track': 'Tracks',
    'genre': 'Playlists',
    'playlist': 'Playlists',
}

def speech_response(speech_text):
    logger.info(speech_text)
    return statement(speech_text).simple_card(request.type, speech_text) if request else speech_text

def require_allowed_user(f):
    def wrapped(*args, **kwargs):
        if DEBUG or (session and session.user.userId in os.getenv('ALEXA_USER_ID').split(';')):
            return f(*args, **kwargs)
        else:
            abort(403)
    return wrapped

@app.before_request
def before_request():
    g.ssh = CasaSSHService()
    g.ssh.start()

@app.after_request
def after_request(response):
    g.ssh.close()
    return response

@app.route('/')
@ask.intent('HelloIntent')
def hello():
    speech_text = 'Hello, welcome to Alexa Casa Tunes'
    return speech_response(speech_text)

# PLAYBACK

@require_allowed_user
@ask.intent('AMAZON.ResumeIntent')
@ask.intent('CasaPlay')
def play_song():
    g.ssh.casa_command(endpoint='PlaySong')
    speech_text = 'Playing casa tunes'
    return speech_response(speech_text)

@require_allowed_user
@ask.intent('AMAZON.PauseIntent')
def pause_song():
    g.ssh.casa_command(endpoint='PauseSong')
    speech_text = 'Pausing casa tunes'
    return speech_response(speech_text)

@require_allowed_user
@ask.intent('AMAZON.PreviousIntent')
def previous_song():
    g.ssh.casa_command(endpoint='PreviousSong')
    speech_text = 'Playing previous song on casa tunes'
    return speech_response(speech_text)

@require_allowed_user
@ask.intent('AMAZON.NextIntent')
def next_song():
    g.ssh.casa_command(endpoint='NextSong')
    speech_text = 'Playing next song on casa tunes'
    return speech_response(speech_text)

# ROOM POWER

@require_allowed_user
@ask.intent('CasaTurnRoomOn', mapping={'room': 'Room'}, default={'room': DEFAULT_ZONE})
def turn_room_on(room):
    room, zone_id = match_room_input(room)

    g.ssh.casa_command(
        endpoint='SetZonePower',
        data={
            'Power': True,
            'ZoneID': zone_id,
        },
    )
    speech_text = 'Turning on music in {room}'.format(room=room)
    return speech_response(speech_text)

@require_allowed_user
@ask.intent('CasaTurnRoomOff', mapping={'room': 'Room'})
def turn_room_off(room):
    room, zone_id = match_room_input(room)

    g.ssh.casa_command(
        endpoint='SetZonePower',
        data={
            'Power': False,
            'ZoneID': zone_id,
        },
    )
    speech_text = 'Turning off music in {room}'.format(room=room)
    return speech_response(speech_text)

# ROOM VOLUME

@require_allowed_user
@ask.intent('CasaSetRoomVolume', mapping={'room': 'Room', 'new_volume': 'Volume'})
def set_room_volume(room, new_volume):
    room, zone_id = match_room_input(room)

    g.ssh.casa_command(
        endpoint='SetZoneVolume',
        data={
            'Volume': new_volume,
            'ZoneID': zone_id,
        },
    )
    speech_text = 'Setting volume in {room} to {new_volume}'.format(
        room=room, new_volume=new_volume
    )
    return speech_response(speech_text)

@require_allowed_user
@ask.intent('CasaIncreaseRoomVolume', mapping={'room': 'Room'})
def increase_room_volume(room):
    room, zone_id = match_room_input(room)

    parsed_status = parse_app_status(g.ssh.casa_command(endpoint='GetAppStatus'))
    current_volume = parsed_status['zones'][zone_id]['Volume']
    new_volume = current_volume + 10
    g.ssh.casa_command(
        endpoint='SetZoneVolume',
        data={
            'Volume': new_volume,
            'ZoneID': zone_id,
        },
    )
    speech_text = 'Setting volume in {room} to {new_volume}'.format(
        room=room, new_volume=new_volume
    )
    return speech_response(speech_text)

@require_allowed_user
@ask.intent('CasaDecreaseRoomVolume', mapping={'room': 'Room'})
def decrease_room_volume(room):
    room, zone_id = match_room_input(room)

    parsed_status = parse_app_status(g.ssh.casa_command(endpoint='GetAppStatus'))
    current_volume = parsed_status['zones'][zone_id]['Volume']
    new_volume = current_volume - 10
    g.ssh.casa_command(
        endpoint='SetZoneVolume',
        data={
            'Volume': new_volume,
            'ZoneID': zone_id,
        },
    )
    speech_text = 'Setting volume in {room} to {new_volume}'.format(
        room=room, new_volume=new_volume
    )
    return speech_response(speech_text)

# NOW PLAYING

@require_allowed_user
@ask.intent('AMAZON.SearchAction<object@MusicRecording[byArtist]>')
@ask.intent('AMAZON.SearchAction<object@MusicRecording[inAlbum]>')
def now_playing_info():
    parsed_status = parse_app_status(g.ssh.casa_command(endpoint='GetAppStatus'))
    speech_text = 'This song is called {title} by {artists} from the album {album}'.format(**parsed_status)
    return speech_response(speech_text)

# SEARCH

@require_allowed_user
@ask.intent('AMAZON.SearchAction<object@MusicCreativeWork>')
def find_and_play_song():
    parsed_request = parse_search_request(request)
    casa_creative_type = ALEXA_CASA_TYPE_MAP[parsed_request['creative_type']]
    logger.debug(json.dumps(parsed_request))

    search_response_data = g.ssh.casa_command(
        endpoint='SearchMediaCollectionByZone',
        data={
            'ZoneID': DEFAULT_ZONE,
            'SearchCurrentMusicServiceOnly': True,
            'Searchtext': parsed_request['search_text'],
        },
    )
    parsed_search_response = parse_search_response(search_response_data)
    first_requested_item_id = parsed_search_response[casa_creative_type][0]['ID']

    g.ssh.casa_command(
        endpoint='PlayMediaCollectionOrItem2',
        data={
            'ZoneID': DEFAULT_ZONE,
            'ItemID': first_requested_item_id,
            'Filter': None,
            'AddToQueue': QUEUE_SPOT_MAP[DEFAULT_QUEUE_TYPE],
        },
    )

    return speech_response(search_speech_text(parsed_request))

if __name__ == '__main__':
    app.run(debug=DEBUG)
