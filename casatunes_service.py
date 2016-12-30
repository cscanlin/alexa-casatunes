import json
import os
import requests

from flask_ask import statement

def load_zone_map(zone_map_file_name):
    with open(zone_map_file_name) as zone_file:
        return {k.lower(): v for k, v in json.load(zone_file).items()}

class CasaService(object):
    CASA_SERVER_IP = 'http://192.168.1.20'
    CASA_SERVICE_ROUTE = 'CasaTunes/CasaService.svc'
    HEADERS = {'Content-Type': 'application/json'}
    ROOM_ZONE_MAP = load_zone_map('speechAssets/Rooms.json')

    def __init__(self, logger):
        self.logger = logger

    def casa_route(self, endpoint):
        return os.path.join(self.CASA_SERVER_IP, self.CASA_SERVICE_ROUTE, endpoint)

    def casa_command(self):
        speech_text = 'Playing casa tunes'
        requests.post(
            self.casa_route('PlaySong'),
            headers=self.HEADERS,
            data=json.dumps({"ZoneID": None})
        )
        self.logger.info(speech_text)
        return statement(speech_text).simple_card('CasaPlay', speech_text)
        pass

    def play_song(self, *args, **kwargs):
        speech_text = 'Playing casa tunes'
        requests.post(
            self.casa_route('PlaySong'),
            headers=self.HEADERS,
            data=json.dumps({"ZoneID": None})
        )
        self.logger.info(speech_text)
        return statement(speech_text).simple_card('CasaPlay', speech_text)

    def pause_song(self):
        speech_text = 'Pausing casa tunes'
        requests.post(
            self.casa_route('PauseSong'),
            headers=self.HEADERS,
            data=json.dumps({"ZoneID": None})
        )
        self.logger.info(speech_text)
        return statement(speech_text).simple_card('CasaPause', speech_text)

    def previous_song(self):
        speech_text = 'Playing previous Song on casa tunes'
        requests.post(
            self.casa_route('PreviousSong'),
            headers=self.HEADERS,
            data=json.dumps({"ZoneID": None})
        )
        self.logger.info(speech_text)
        return statement(speech_text).simple_card('CasaPrevious', speech_text)

    def next_song(self):
        speech_text = 'Playing next Song on casa tunes'
        requests.post(
            self.casa_route('NextSong'),
            headers=self.HEADERS,
            data=json.dumps({"ZoneID": None})
        )
        self.logger.info(speech_text)
        return statement(speech_text).simple_card('CasaNext', speech_text)

    def turn_room_on(self, room):
        speech_text = 'Turning on music in {room}'.format(room=room)
        requests.post(
            self.casa_route('SetZonePower'),
            headers=self.HEADERS,
            data=json.dumps({
                "Power": True,
                "ZoneID": str(self.ROOM_ZONE_MAP[room])
            })
        )
        self.logger.info(speech_text)
        return statement(speech_text).simple_card('CasaTurnRoomOn', speech_text)

    def turn_room_off(self, room):
        speech_text = 'Turning on music in {room}'.format(room=room)
        requests.post(
            self.casa_route('SetZonePower'),
            headers=self.HEADERS,
            data=json.dumps({
                "Power": False,
                "ZoneID": str(self.ROOM_ZONE_MAP[room])
            })
        )
        self.logger.info(speech_text)
        return statement(speech_text).simple_card('CasaTurnRoomOff', speech_text)
