# coding=utf-8
from flask.helpers import get_debug_flag

from event_app.app import create_app
from event_app.configs import DevelopmentConfig, ProductionConfig

CONFIG = DevelopmentConfig if get_debug_flag() else ProductionConfig

app = create_app(CONFIG)
