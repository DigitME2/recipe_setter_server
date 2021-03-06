import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask.logging import default_handler
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config
from .extensions import db

# Set up logging handlers
if not os.path.exists('logs'):
    os.mkdir('logs')
file_handler = RotatingFileHandler(filename=getattr(Config, "FLASK_LOG_FILE", "server.log"),
                                   maxBytes=getattr(Config, "ROTATING_LOG_FILE_MAX_BYTES", 1024000),
                                   backupCount=getattr(Config, "ROTATING_LOG_FILE_COUNT", 10))
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
file_handler.setLevel(getattr(Config, "FILE_LOGGING_LEVEL", logging.INFO))


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)

    # Set up logging
    import logging
    app.logger.removeHandler(default_handler)
    app.logger.setLevel(logging.DEBUG)
    app.logger.addHandler(file_handler)

    print("Logging level:", logging.getLevelName(app.logger.getEffectiveLevel()))
    if getattr(Config, "ACCEPT_ANY_RFID", False):
        print("WARNING: ACCEPT_ANY_RFID is set to True. This will create a new ItemLog entry for ANY rfid tag scanned by a reader")
        print("This is not recommended for regular usage. It can be set to False in config.py")

    from app import android, rfid
    app.register_blueprint(android.bp)
    app.register_blueprint(rfid.bp)

    # To get client IP when using a proxy
    # This requires the following line in nginx config:
    # proxy_set_header   X-Real-IP            $remote_addr;
    app.wsgi_app = ProxyFix(app.wsgi_app)

    @app.before_first_request
    def initial_setup():
        db.create_all()

    @app.route('/')
    def default():
        return "Server is running"

    return app
