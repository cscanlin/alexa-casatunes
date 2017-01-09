import logging

from flask import json
from flask_ask import statement, request

import requests

logger = logging.getLogger('flask_ask')
logger.setLevel(logging.INFO)

def load_zone_map(zone_map_file_name):
    with open(zone_map_file_name) as zone_file:
        return {k.lower(): v for k, v in json.load(zone_file).items()}

class CasaService(object):
    CASA_SERVER_IP = 'http://192.168.1.20'
    CASA_SERVICE_ROUTE = 'CasaTunes/CasaService.svc'
    HEADERS = {'Content-Type': 'application/json'}
    ROOM_ZONE_MAP = load_zone_map('speechAssets/Rooms.json')

    @staticmethod
    def casa_route(endpoint):
        return '/'.join((
            CasaService.CASA_SERVER_IP, CasaService.CASA_SERVICE_ROUTE, endpoint
        ))

    @staticmethod
    def casa_command(endpoint, speech_text, data={"ZoneID": 0}):
        requests.post(
            CasaService.casa_route(endpoint),
            headers=CasaService.HEADERS,
            data=json.dumps(data)
        )
        logger.info(speech_text)
        return statement(speech_text).simple_card(request.type, speech_text)
