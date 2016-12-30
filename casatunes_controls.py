import logging
import os

from flask import Flask, json
from flask_ask import Ask, statement, request

import requests

app = Flask(__name__)
ask = Ask(app, '/')
logger = logging.getLogger('flask_ask')
logger.setLevel(logging.INFO)

def load_zone_map(zone_map_file_name):
    with open(zone_map_file_name) as zone_file:
        return {k.lower(): v for k, v in json.load(zone_file).items()}

class CasaControls(object):
    CASA_SERVER_IP = 'http://192.168.1.20'
    CASA_SERVICE_ROUTE = 'CasaTunes/CasaService.svc'
    HEADERS = {'Content-Type': 'application/json'}
    ROOM_ZONE_MAP = load_zone_map('speechAssets/Rooms.json')

    @staticmethod
    def casa_route(endpoint):
        return os.path.join(
            CasaControls.CASA_SERVER_IP, CasaControls.CASA_SERVICE_ROUTE, endpoint
        )

    @staticmethod
    def casa_command(endpoint, speech_text, data={"ZoneID": None}):
        requests.post(
            CasaControls.casa_route(endpoint),
            headers=CasaControls.HEADERS,
            data=json.dumps(data)
        )
        logger.info(speech_text)
        return statement(speech_text).simple_card(request.type, speech_text)

    @staticmethod
    @ask.intent('CasaPlay')
    def play_song():
        return CasaControls.casa_command(
            endpoint='PlaySong',
            speech_text='Playing casa tunes'
        )

    @staticmethod
    @ask.intent('CasaPause')
    def pause_song():
        return CasaControls.casa_command(
            endpoint='PauseSong',
            speech_text='Pausing casa tunes'
        )

    @staticmethod
    @ask.intent('CasaPrevious')
    def previous_song():
        return CasaControls.casa_command(
            endpoint='PreviousSong',
            speech_text='Playing previous Song on casa tunes'
        )

    @staticmethod
    @ask.intent('CasaNext')
    def next_song():
        return CasaControls.casa_command(
            endpoint='NextSong',
            speech_text='Playing next Song on casa tunes'
        )

    @staticmethod
    @ask.intent('CasaTurnRoomOn', mapping={'room': 'Room'})
    def turn_room_on(room):
        return CasaControls.casa_command(
            endpoint='SetZonePower',
            speech_text='Turning on music in {room}'.format(room=room),
            data={
                "Power": True,
                "ZoneID": str(CasaControls.ROOM_ZONE_MAP[room])
            },
        )

    @staticmethod
    @ask.intent('CasaTurnRoomOff', mapping={'room': 'Room'})
    def turn_room_off(room):
        return CasaControls.casa_command(
            endpoint='SetZonePower',
            speech_text='Turning off music in {room}'.format(room=room),
            data={
                "Power": False,
                "ZoneID": str(CasaControls.ROOM_ZONE_MAP[room])
            },
        )

if __name__ == '__main__':
    app.run(debug=True)
