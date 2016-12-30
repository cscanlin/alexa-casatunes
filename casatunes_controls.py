# from flask import Flask
# from flask_ask import Ask
# import json
#
# app = Flask(__name__)
# ask = Ask(app, "/")
#
# @app.route('/test')
# def test():
#     return json.dumps({'hello': 'world!'})
#
# if __name__ == '__main__':
#     app.run(debug=True)

import logging

from flask import Flask, json, jsonify, render_template
from flask_ask import Ask, request, session, question, statement, context, audio, current_stream

import requests

app = Flask(__name__)
ask = Ask(app, '/')
logger = logging.getLogger('flask_ask')
logger.setLevel(logging.INFO)

HEADERS = {'Content-Type': 'application/json'}
with open('speechAssets/Rooms.json') as zone_file:
    ROOM_ZONE_MAP = {k.lower(): v for k, v in json.load(zone_file).items()}

@ask.intent('CasaPlay')
def play_song():
    speech_text = 'Playing casa tunes'
    requests.post(
        'http://192.168.1.20/CasaTunes/CasaService.svc/PlaySong',
        headers=HEADERS,
        data=json.dumps({"ZoneID": None})
    )
    logger.info(speech_text)
    return statement(speech_text).simple_card('ResumeIntent', speech_text)

@ask.intent('CasaPause')
def pause_song():
    speech_text = 'Pausing casa tunes'
    requests.post(
        'http://192.168.1.20/CasaTunes/CasaService.svc/PauseSong',
        headers=HEADERS,
        data=json.dumps({"ZoneID": None})
    )
    logger.info(speech_text)
    return statement(speech_text).simple_card('PauseIntent', speech_text)

@ask.intent('CasaPrevious')
def previous_song():
    speech_text = 'Playing previous Song on casa tunes'
    requests.post(
        'http://192.168.1.20/CasaTunes/CasaService.svc/PreviousSong',
        headers=HEADERS,
        data=json.dumps({"ZoneID": None})
    )
    logger.info(speech_text)
    return statement(speech_text).simple_card('PreviousIntent', speech_text)

@ask.intent('CasaNext')
def next_song():
    speech_text = 'Playing next Song on casa tunes'
    requests.post(
        'http://192.168.1.20/CasaTunes/CasaService.svc/NextSong',
        headers=HEADERS,
        data=json.dumps({"ZoneID": None})
    )
    logger.info(speech_text)
    return statement(speech_text).simple_card('NextIntent', speech_text)

@ask.intent('CasaTurnRoomOn', mapping={'room': 'Room'})
def turn_room_on(room):
    print(room, str(ROOM_ZONE_MAP[room]))
    speech_text = 'Turning on music in {room}'.format(room=room)
    requests.post(
        'http://192.168.1.20/CasaTunes/CasaService.svc/SetZonePower',
        headers=HEADERS,
        data=json.dumps({
            "Power": True,
            "ZoneID": str(ROOM_ZONE_MAP[room])
        })
    )
    logger.info(speech_text)
    return statement(speech_text).simple_card('CasaTurnRoomOn', speech_text)

@ask.intent('CasaTurnRoomOff', mapping={'room': 'Room'})
def turn_room_off(room):
    speech_text = 'Turning on music in {room}'.format(room=room)
    print(room, str(ROOM_ZONE_MAP[room]))
    requests.post(
        'http://192.168.1.20/CasaTunes/CasaService.svc/SetZonePower',
        headers=HEADERS,
        data=json.dumps({
            "Power": False,
            "ZoneID": str(ROOM_ZONE_MAP[room])
        })
    )
    logger.info(speech_text)
    return statement(speech_text).simple_card('CasaTurnRoomOff', speech_text)

# @ask.intent('AMAZON.StopIntent')
# def stop():
#     return "", 200

# # optional callbacks
# @ask.on_playback_started()
# def started(offset, token):
#     _infodump('STARTED Audio Stream at {} ms'.format(offset))
#     _infodump('Stream holds the token {}'.format(token))
#     _infodump('STARTED Audio stream from {}'.format(current_stream.url))
#
# @ask.on_playback_stopped()
# def stopped(offset, token):
#     _infodump('STOPPED Audio Stream at {} ms'.format(offset))
#     _infodump('Stream holds the token {}'.format(token))
#     _infodump('Stream stopped playing from {}'.format(current_stream.url))
#
#
# @ask.on_playback_nearly_finished()
# def nearly_finished():
#     _infodump('Stream nearly finished from {}'.format(current_stream.url))
#
# @ask.on_playback_finished()
# def stream_finished(token):
#     _infodump('Playback has finished for stream with token {}'.format(token))

@ask.session_ended
def session_ended():
    return "", 200

def _infodump(obj, indent=2):
    logger.info(json.dumps(obj, indent=indent))

if __name__ == '__main__':
    app.run(debug=True)
