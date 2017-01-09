from flask import Flask
from flask_ask import Ask

from casa_service import CasaService

app = Flask(__name__)
ask = Ask(app, '/')

class ControlsApp(object):
    """docstring for ControlsApp."""

    @staticmethod
    @ask.intent('AMAZON.ResumeIntent')
    @ask.intent('CasaPlay')
    def play_song():
        return CasaService.casa_command(
            endpoint='PlaySong',
            speech_text='Playing casa tunes'
        )

    @staticmethod
    @ask.intent('AMAZON.PauseIntent')
    def pause_song():
        return CasaService.casa_command(
            endpoint='PauseSong',
            speech_text='Pausing casa tunes'
        )

    @staticmethod
    @ask.intent('AMAZON.PreviousIntent')
    def previous_song():
        return CasaService.casa_command(
            endpoint='PreviousSong',
            speech_text='Playing previous Song on casa tunes'
        )

    @staticmethod
    @ask.intent('AMAZON.NextIntent')
    def next_song():
        return CasaService.casa_command(
            endpoint='NextSong',
            speech_text='Playing next Song on casa tunes'
        )

    @staticmethod
    @ask.intent('CasaTurnRoomOn', mapping={'room': 'Room'}, default={'room': 'kitchen 1'})
    def turn_room_on(room):
        return CasaService.casa_command(
            endpoint='SetZonePower',
            speech_text='Turning on music in {room}'.format(room=room),
            data={
                "Power": True,
                "ZoneID": str(CasaService.ROOM_ZONE_MAP[room])
            },
        )

    @staticmethod
    @ask.intent('CasaTurnRoomOff', mapping={'room': 'Room'})
    def turn_room_off(room):
        return CasaService.casa_command(
            endpoint='SetZonePower',
            speech_text='Turning off music in {room}'.format(room=room),
            data={
                "Power": False,
                "ZoneID": str(CasaService.ROOM_ZONE_MAP[room])
            },
        )

    @staticmethod
    @ask.intent('CasaSetRoomVolume', mapping={'room': 'Room', 'new_volume': 'Volume'})
    def set_room_volume(room, new_volume):
        return CasaService.casa_command(
            endpoint='SetZoneVolume',
            speech_text='Setting volume in {room} to {new_volume}'.format(
                room=room, new_volume=new_volume
            ),
            data={
                "Volume": new_volume,
                "ZoneID": str(CasaService.ROOM_ZONE_MAP[room])
            },
        )

if __name__ == '__main__':
    app.run(debug=True)
