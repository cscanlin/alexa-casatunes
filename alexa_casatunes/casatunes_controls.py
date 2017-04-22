import os

from flask import json, abort, g
from flask_ask import statement, request, session

from alexa_casatunes.casa_service import CasaSSHService
from alexa_casatunes.utils import (
    match_room_input,
    parse_app_status,
    parse_search_request,
    parse_search_response,
    search_speech_text,
)

from alexa_casatunes import app, ask

def speech_response(speech_text):
    app.logger.info(speech_text)
    return statement(speech_text).simple_card(request.type, speech_text) if request else speech_text

def require_allowed_user(f):
    def wrapped(*args, **kwargs):
        if app.config['DEBUG'] or (session and session.user.userId in os.getenv('ALEXA_USER_ID').split(';')):
            return f(*args, **kwargs)
        else:
            abort(403)
    return wrapped

@app.before_request
def before_request():
    g.ssh = CasaSSHService(logger=app.logger)
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
@ask.intent('CasaTurnRoomOn', mapping={'room': 'Room'}, default={'room': app.config['DEFAULT_ZONE']})
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
    casa_creative_type = app.config['ALEXA_CASA_TYPE_MAP'][parsed_request['creative_type']]
    app.logger.debug(json.dumps(parsed_request))

    search_response_data = g.ssh.casa_command(
        endpoint='SearchMediaCollectionByZone',
        data={
            'ZoneID': app.config['DEFAULT_ZONE'],
            'SearchCurrentMusicServiceOnly': True,
            'Searchtext': parsed_request['search_text'],
        },
    )
    parsed_search_response = parse_search_response(search_response_data)
    first_requested_item_id = parsed_search_response[casa_creative_type][0]['ID']

    g.ssh.casa_command(
        endpoint='PlayMediaCollectionOrItem2',
        data={
            'ZoneID': app.config['DEFAULT_ZONE'],
            'ItemID': first_requested_item_id,
            'Filter': None,
            'AddToQueue': 2,  # app.config['QUEUE_SPOT_MAP'][app.config['DEFAULT_QUEUE_TYPE']]
        },
    )

    return speech_response(search_speech_text(parsed_request))
