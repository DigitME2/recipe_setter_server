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
file_handler = RotatingFileHandler(filename=Config.FLASK_LOG_FILE,
                                   maxBytes=Config.ROTATING_LOG_FILE_MAX_BYTES,
                                   backupCount=Config.ROTATING_LOG_FILE_COUNT)
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
file_handler.setLevel(Config.FILE_LOGGING_LEVEL)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)


    # Add gunicorn logger
    # gunicorn_logger = logging.getLogger('gunicorn.error')
    # for handler in gunicorn_logger.handlers:
    #     app.logger.addHandler(handler)

    # Add waitress logger
    waitress_logger = logging.getLogger('waitress')
    waitress_logger.setLevel(logging.DEBUG)
    for handler in waitress_logger.handlers:
        app.logger.addHandler(handler)

    # Set up logging
    app.logger.setLevel(logging.DEBUG)
    app.logger.addHandler(file_handler)

    print("Logging level:", logging.getLevelName(app.logger.getEffectiveLevel()))

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
