# from flask import Flask
# from flask_ask import Ask
# import json
#
# app = Flask(__name__)
# ask = Ask(app, "/")
# class ClassName(object):
#     @app.route('/test')
#     def test():
#         return json.dumps({'hello': 'world!'})
#
# if __name__ == '__main__':
#     app.run(debug=True)

import logging
import os

from flask import Flask, json
from flask_ask import Ask, request, session, question, statement, context, audio, current_stream

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
    def casa_command(intent, endpoint, speech_text, data={"ZoneID": None}, **kwargs):
        speech_text = 'Playing casa tunes'
        requests.post(
            CasaControls.casa_route('PlaySong'),
            headers=CasaControls.HEADERS,
            data=json.dumps(data)
        )
        logger.info(speech_text)
        return statement(speech_text).simple_card('CasaPlay', speech_text)

    @staticmethod
    @ask.intent('CasaPlay')
    def play_song():
        speech_text = 'Playing casa tunes'
        requests.post(
            CasaControls.casa_route('PlaySong'),
            headers=CasaControls.HEADERS,
            data=json.dumps({"ZoneID": None})
        )
        logger.info(speech_text)
        return statement(speech_text).simple_card('CasaPlay', speech_text)

    @staticmethod
    @ask.intent('CasaPause')
    def pause_song():
        speech_text = 'Pausing casa tunes'
        requests.post(
            CasaControls.casa_route('PauseSong'),
            headers=CasaControls.HEADERS,
            data=json.dumps({"ZoneID": None})
        )
        logger.info(speech_text)
        return statement(speech_text).simple_card('CasaPause', speech_text)

    @staticmethod
    @ask.intent('CasaPrevious')
    def previous_song():
        speech_text = 'Playing previous Song on casa tunes'
        requests.post(
            CasaControls.casa_route('PreviousSong'),
            headers=CasaControls.HEADERS,
            data=json.dumps({"ZoneID": None})
        )
        logger.info(speech_text)
        return statement(speech_text).simple_card('CasaPrevious', speech_text)

    @staticmethod
    @ask.intent('CasaNext')
    def next_song():
        speech_text = 'Playing next Song on casa tunes'
        requests.post(
            CasaControls.casa_route('NextSong'),
            headers=CasaControls.HEADERS,
            data=json.dumps({"ZoneID": None})
        )
        logger.info(speech_text)
        return statement(speech_text).simple_card('CasaNext', speech_text)

    @staticmethod
    @ask.intent('CasaTurnRoomOn', mapping={'room': 'Room'})
    def turn_room_on(room):
        speech_text = 'Turning on music in {room}'.format(room=room)
        requests.post(
            CasaControls.casa_route('SetZonePower'),
            headers=CasaControls.HEADERS,
            data=json.dumps({
                "Power": True,
                "ZoneID": str(CasaControls.ROOM_ZONE_MAP[room])
            })
        )
        logger.info(speech_text)
        return statement(speech_text).simple_card('CasaTurnRoomOn', speech_text)

    @staticmethod
    @ask.intent('CasaTurnRoomOff', mapping={'room': 'Room'})
    def turn_room_off(room):
        speech_text = 'Turning on music in {room}'.format(room=room)
        requests.post(
            CasaControls.casa_route('SetZonePower'),
            headers=CasaControls.HEADERS,
            data=json.dumps({
                "Power": False,
                "ZoneID": str(CasaControls.ROOM_ZONE_MAP[room])
            })
        )
        logger.info(speech_text)
        return statement(speech_text).simple_card('CasaTurnRoomOff', speech_text)

if __name__ == '__main__':
    app.run(debug=True)
