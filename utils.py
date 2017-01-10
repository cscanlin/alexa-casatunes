from collections import defaultdict
import json
import xml.etree.ElementTree as ET

def load_casa_config(config_file):
    with open(config_file) as cf:
        config = json.load(cf)
        config['ROOM_ZONE_MAP'] = {k.lower(): v for k, v in config['ROOM_ZONE_MAP'].items()}
    return config

def parse_app_status(status_response):
    parsed_status_data = {}
    status_data = status_response.json()['d']
    now_playing_xml = status_data['NowPlayingInfo'][0]['MediaItem']['DisplayXML']
    now_playing_root = ET.fromstring(now_playing_xml)
    for elem in now_playing_root.findall('line'):
        parsed_status_data[elem[0].tag] = elem[0].text
    return parsed_status_data

def parse_search_request(search_request):
    parsed_request_data = {}
    slot_data = search_request['intent']['slots']
    parsed_request_data['creative_name'] = slot_data.get('object.name', {}).get('value')
    parsed_request_data['creative_type'] = slot_data.get('object.type', {}).get('value')
    parsed_request_data['artist'] = slot_data.get('object.byArtist.name', {}).get('value')
    return parsed_request_data

def parse_search_response(search_response):
    parsed_response_data = defaultdict(list)
    search_data = search_response.json()['d']['MediaItems']
    for item in search_data[1:]:
        item_creative_type = next(a for a in item['Attributes'] if a['Key'] == 'GroupName')['Value']
        parsed_response_data[item_creative_type].append(item)
    return parsed_response_data
