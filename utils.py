import json
import xml.etree.ElementTree as ET

def load_casa_config(config_file):
    with open(config_file) as cf:
        config = json.load(cf)
        config['ROOM_ZONE_MAP'] = {k.lower(): v for k, v in config['ROOM_ZONE_MAP'].items()}
    return config

def parse_app_status(casa_response):
    parsed_status_data = {}
    response_data = casa_response.json()['d']
    now_playing_xml = response_data['NowPlayingInfo'][0]['MediaItem']['DisplayXML']
    now_playing_root = ET.fromstring(now_playing_xml)
    for elem in now_playing_root.findall('line'):
        parsed_status_data[elem[0].tag] = elem[0].text
    return parsed_status_data

def parse_music_search_request(request):
    parsed_search_data = {}
    slot_data = request['intent']['slots']
    parsed_search_data['creative_name'] = slot_data['object.name']['value']
    parsed_search_data['creative_type'] = slot_data['object.type']['value']
    return parsed_search_data
