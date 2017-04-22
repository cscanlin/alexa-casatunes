import json
import os
import requests
import sys

SERVICE_ROUTE = 'CasaTunes/CasaService.svc'
STATUS_ENDPOINT = 'GetAppStatus'
CASA_HEADERS = {'Content-Type': 'application/json'}

DEFAULT_ZONE_MAP_PATH = os.path.join('alexa_casatunes', 'data', 'room_zone_map.json')
DEFAULT_INTERACTION_MODEL_PATH = 'interaction_model.json'

def load_zone_data(local_casa_ip):
    status_path = os.path.join('http://', local_ip, SERVICE_ROUTE, STATUS_ENDPOINT)
    r = requests.post(status_path, headers=CASA_HEADERS, data=json.dumps({'ZoneID': 0}))
    return {zone_info['Name']: zone_info['ZoneID'] for zone_info in r.json()['d']['Zones']}

def write_room_zone_map(zone_data, zone_map_path=DEFAULT_ZONE_MAP_PATH):
    with open(zone_map_path, 'w') as f:
        json.dump(zone_data, f, indent=2)

def update_interaction_model(zone_data, interaction_model_path=DEFAULT_INTERACTION_MODEL_PATH):
    with open(interaction_model_path, 'r+') as f:
        interaction_model = json.load(f)
        interaction_model["types"] = [{
            "name": "Room",
            "values": [{'name': {'value': room_name}} for room_name in zone_data.keys()]
        }]
        f.seek(0)
        json.dump(interaction_model, f, indent=2)
        f.truncate()

if __name__ == '__main__':
    local_ip = sys.argv[1]
    zone_data = load_zone_data(local_ip)
    write_room_zone_map(zone_data)
    update_interaction_model(zone_data)
