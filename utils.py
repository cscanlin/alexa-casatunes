import json
import xml.etree.ElementTree as ET

def load_casa_config(config_file):
    with open(config_file) as cf:
        config = json.load(cf)
        config['ROOM_ZONE_MAP'] = {k.lower(): v for k, v in config['ROOM_ZONE_MAP'].items()}
    return config

def parse_app_status(casa_response):
    parsed_data = {}
    response_data = casa_response.json()['d']
    now_playing_xml = response_data['NowPlayingInfo'][0]['MediaItem']['DisplayXML']
    now_playing_root = ET.fromstring(now_playing_xml)
    for elem in now_playing_root.findall('line'):
        print(elem[0].tag, elem[0].text)
        print(parsed_data)
        parsed_data[elem[0].tag] = elem[0].text
    return parsed_data
