class Config(object):
    DEBUG = False

    DEFAULT_ZONE = 0

    DEFAULT_QUEUE_TYPE = 'ADD_AND_PLAY'

    QUEUE_SPOT_MAP = {
        'ADD_AND_PLAY': 2,
    }

    ALEXA_CASA_TYPE_MAP = {
        'artist': 'Artists',
        'album': 'Albums',
        'song': 'Tracks',
        'track': 'Tracks',
        'genre': 'Playlists',
        'playlist': 'Playlists',
    }

class DevConfig(object):
    DEBUG = True
