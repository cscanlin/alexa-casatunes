import json

def load_casa_config(config_file):
    with open(config_file) as cf:
        config = json.load(cf)
        config['ROOM_ZONE_MAP'] = {k.lower(): v for k, v in config['ROOM_ZONE_MAP'].items()}
    return config
