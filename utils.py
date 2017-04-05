import json
import xml.etree.ElementTree as ET

from collections import defaultdict
from functools import reduce

def deep_get(dictionary, *keys):
    # http://stackoverflow.com/a/40675868/1883900
    return reduce(lambda d, key: d.get(key, None) if hasattr(d, '__getitem__') else None, keys, dictionary)

def load_casa_config(config_file):
    with open(config_file) as cf:
        config = json.load(cf)
        config['ROOM_ZONE_MAP'] = {k.lower(): v for k, v in config['ROOM_ZONE_MAP'].items()}
    return config

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
    if parsed_req['creative_type'] in ('music', None):
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

    if parsed_req['owner_name'] and parsed_req['owner_name'].lower().startswith('playlist'):
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
        parsed_resp[item_creative_type].append(item)
    return parsed_resp

def search_speech_text(parsed_request):
    speech_text = 'playing the {creative_type} {creative_name}'.format(**parsed_request)
    if parsed_request['artist'] and parsed_request['creative_type'] != 'artist':
        speech_text += ' by {}'.format(parsed_request['artist'])
    return speech_text
