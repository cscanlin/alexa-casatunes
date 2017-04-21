import os

from flask import Flask
from flask_ask import Ask

app = Flask(__name__)
ask = Ask(app, '/')

config_options = {
    "dev": "alexa_casatunes.config.DevConfig",
    "prod": "alexa_casatunes.config.Config",
    "default": "alexa_casatunes.config.Config",
}

config_name = os.getenv('ALEXA_CASA_ENV', 'default')
app.config.from_object(config_options[config_name])

app.url_map.strict_slashes = False


from alexa_casatunes import casa_service
