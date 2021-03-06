import json
import os
import xml.etree.ElementTree as ET

from collections import defaultdict
from functools import reduce
from fuzzywuzzy import fuzz, process

from alexa_casatunes import app

def deep_get(dictionary, *keys):
    # http://stackoverflow.com/a/40675868/1883900
    return reduce(lambda d, key: d.get(key, '') if isinstance(d, dict) else '', keys, dictionary).lower()

def load_room_zone_map(mapping_file):
    with open(mapping_file) as mf:
        return {room.lower(): zone_id for room, zone_id in json.load(mf).items()}

def match_room_input(interpreted_room):
    rz_map = load_room_zone_map(os.path.join(app.root_path, 'data', 'room_zone_map.json'))
    interpreted_room = str(interpreted_room).lower()
    if interpreted_room in rz_map.keys():
        room_name = interpreted_room
    else:
        room_name = process.extractOne(interpreted_room, rz_map.keys(), scorer=fuzz.token_sort_ratio)[0]
    return room_name, rz_map[room_name]

def parse_app_status(status_data):
    parsed_status_data = {}

    parsed_status_data['zones'] = {zone_info['ZoneID']: zone_info for zone_info in status_data['d']['Zones']}

    now_playing_xml = status_data['d']['NowPlayingInfo'][0]['MediaItem']['DisplayXML']
    now_playing_root = ET.fromstring(now_playing_xml)
    for elem in now_playing_root.findall('line'):
        parsed_status_data[elem[0].tag] = elem[0].text
    return parsed_status_data

def parse_search_request(search_request):
    slot_data = search_request['intent']['slots']
    parsed_req = {
        'creative_name': deep_get(slot_data, 'object.name', 'value'),
        'artist': deep_get(slot_data, 'object.byArtist.name', 'value'),
        'creative_type': deep_get(slot_data, 'object.type', 'value'),
        'owner_name': deep_get(slot_data, 'object.owner.name', 'value'),
    }
    # find creative type if none
    if parsed_req['creative_type'] in ('music', ''):
        if parsed_req['artist']:
            parsed_req['creative_type'] = 'artist'
            parsed_req['creative_name'] = parsed_req['artist']
        else:
            parsed_req['creative_type'] = 'song'

    if parsed_req['creative_name']:
        if parsed_req['creative_name'].startswith('artist'):
            parsed_req['creative_name'] = parsed_req['creative_name'].replace('artist', '')
            parsed_req['creative_type'] = 'artist'
            parsed_req['artist'] = parsed_req['creative_name']

        if parsed_req['creative_name'].startswith('playlist'):
            parsed_req['creative_name'] = parsed_req['creative_name'].replace('playlist', '')
            parsed_req['creative_type'] = 'playlist'

    if parsed_req['owner_name'] and parsed_req['owner_name'].startswith('playlist'):
        parsed_req['creative_name'] = parsed_req['owner_name'].replace('playlist', '')
        parsed_req['creative_type'] = 'playlist'

    parsed_req['search_text'] = parsed_req['creative_name']
    if parsed_req['artist'] and parsed_req['creative_type'] != 'artist':
        parsed_req['search_text'] += ' ' + parsed_req['artist']

    return parsed_req

def parse_search_response(search_data):
    parsed_resp = defaultdict(list)
    media_items = search_data['d']['MediaItems'][1:]
    for item in media_items:
        item_creative_type = next(a for a in item['Attributes'] if a['Key'] == 'GroupName')['Value']
        item_creative_type = item_creative_type.replace('Windows Music ', '')
        parsed_resp[item_creative_type].append(item)
    return parsed_resp

def search_speech_text(parsed_request):
    speech_text = 'playing the {creative_type} {creative_name}'.format(**parsed_request)
    if parsed_request['artist'] and parsed_request['creative_type'] != 'artist':
        speech_text += ' by {}'.format(parsed_request['artist'])
    return speech_text
