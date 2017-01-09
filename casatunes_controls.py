import logging

from flask import Flask, json
from flask_ask import Ask, statement, request

import requests

from casa_utils import load_casa_config

logger = logging.getLogger('flask_ask')
logger.setLevel(logging.INFO)

app = Flask(__name__)
ask = Ask(app, '/')

CASA_CONFIG = load_casa_config('casa_config.json')

def casa_route(endpoint):
    print(CASA_CONFIG)
    return '/'.join((
        CASA_CONFIG['SERVER_IP'], CASA_CONFIG['SERVICE_ROUTE'], endpoint
    ))

def casa_command(endpoint, speech_text, data={"ZoneID": 0}):
    requests.post(
        casa_route(endpoint),
        headers=CASA_CONFIG['HEADERS'],
        data=json.dumps(data)
    )
    logger.info(speech_text)
    return statement(speech_text).simple_card(request.type, speech_text)

@ask.intent('AMAZON.ResumeIntent')
@ask.intent('CasaPlay')
def play_song():
    return casa_command(
        endpoint='PlaySong',
        speech_text='Playing casa tunes'
    )

@ask.intent('AMAZON.PauseIntent')
def pause_song():
    return casa_command(
        endpoint='PauseSong',
        speech_text='Pausing casa tunes'
    )

@ask.intent('AMAZON.PreviousIntent')
def previous_song():
    return casa_command(
        endpoint='PreviousSong',
        speech_text='Playing previous Song on casa tunes'
    )

@ask.intent('AMAZON.NextIntent')
def next_song():
    return casa_command(
        endpoint='NextSong',
        speech_text='Playing next Song on casa tunes'
    )

@ask.intent('CasaTurnRoomOn', mapping={'room': 'Room'})
def turn_room_on(room):
    print('!!!!!!!!!!', CASA_CONFIG)
    if room is None:
        room = CASA_CONFIG['DEFAULT_ROOM']
    return casa_command(
        endpoint='SetZonePower',
        speech_text='Turning on music in {room}'.format(room=room),
        data={
            "Power": True,
            "ZoneID": str(CASA_CONFIG['ROOM_ZONE_MAP'][room.lower()])
        },
    )

@ask.intent('CasaTurnRoomOff', mapping={'room': 'Room'})
def turn_room_off(room):
    return casa_command(
        endpoint='SetZonePower',
        speech_text='Turning off music in {room}'.format(room=room),
        data={
            "Power": False,
            "ZoneID": str(CASA_CONFIG['ROOM_ZONE_MAP'][room.lower()])
        },
    )

@ask.intent('CasaSetRoomVolume', mapping={'room': 'Room', 'new_volume': 'Volume'})
def set_room_volume(room, new_volume):
    return casa_command(
        endpoint='SetZoneVolume',
        speech_text='Setting volume in {room} to {new_volume}'.format(
            room=room, new_volume=new_volume
        ),
        data={
            "Volume": new_volume,
            "ZoneID": str(CASA_CONFIG['ROOM_ZONE_MAP'][room.lower()])
        },
    )

if __name__ == '__main__':
    app.run(debug=True)
