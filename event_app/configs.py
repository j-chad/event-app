# coding=utf-8
import os


class Config:
    """Base Configuration"""
    BCRYPT_LOG_ROUNDS = 14
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    DEBUG_TB_TEMPLATE_EDITOR_ENABLED = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 465
    MAIL_USERNAME = 'event.app.notifier@gmail.com'
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True

    APP_DIR = os.path.abspath(os.path.dirname(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, os.path.pardir))
    print(PROJECT_ROOT)


class ProductionConfig(Config):
    ENV = "Production"
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{ os.path.join(Config.PROJECT_ROOT, "prod.db") }'
    MAIL_DEFAULT_SENDER = "Event App Notifier"


class DevelopmentConfig(Config):
    ENV = "Development"
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{ os.path.join(Config.PROJECT_ROOT, "dev.db") }'
    MAIL_DEFAULT_SENDER = "Event App Notifier <Development>"


class TestingConfig(Config):
    ENV = "TESTING"
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    WTF_CSRF_ENABLED = False
    BCRYPT_LOG_ROUNDS = 4


config_map = {
    "ProductionConfig" : ProductionConfig,
    "DevelopmentConfig": DevelopmentConfig,
    "TestingConfig"    : TestingConfig
}
