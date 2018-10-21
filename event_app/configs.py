# coding=utf-8
import datetime
import os


class Config:
    """Base Configuration"""

    # Instance Config
    MAPBOX_ACCESS_TOKEN = os.environ['MAPBOX_ACCESS_TOKEN']
    RECAPTCHA_PUBLIC_KEY = os.environ['RECAPTCHA_PUBLIC_KEY']
    REDIS_URL = os.environ['REDIS_URL']
    RQ_REDIS_URL = os.environ['REDIS_URL']
    RATELIMIT_STORAGE_URL = os.environ['REDIS_URL']
    MAIL_SERVER = os.environ['MAIL_SERVER']
    MAIL_PORT = os.environ['MAIL_PORT']
    MAIL_USERNAME = os.environ['MAIL_USERNAME']
    MAIL_USE_TLS = bool(os.environ['MAIL_USE_TLS'])
    MAIL_USE_SSL = bool(os.environ['MAIL_USE_SSL'])
    SQLALCHEMY_DATABASE_URI = os.environ['JAWSDB_URL']
    WEB_PUSH_PRIVATE_KEY = os.environ['WEB_PUSH_PRIVATE_KEY']
    WEB_PUSH_PUBLIC_KEY = os.environ['WEB_PUSH_PUBLIC_KEY']
    RECAPTCHA_PRIVATE_KEY = os.environ['RECAPTCHA_PRIVATE_KEY']
    MAIL_PASSWORD = os.environ['MAIL_PASSWORD']
    HASHID_SALT = os.environ['HASHID_SALT']
    SECRET_KEY = os.environ['SECRET_KEY']

    BCRYPT_LOG_ROUNDS = 14
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    DEBUG_TB_TEMPLATE_EDITOR_ENABLED = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    VERIFICATION_TOKEN_EXPIRY = 12 * 60 * 60  # 12 Hours
    RECOVERY_TOKEN_EXPIRY = 20 * 60  # 20 Minutes
    MINIMUM_PASSWORD_LENGTH = 8
    RATELIMIT_KEY_PREFIX = "RATELIMITER#"
    HUMANIZE_USE_UTC = True
    PREFERRED_URL_SCHEME = 'https'

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 Mb
    UPLOAD_FOLDER = "uploads"  # Relative to static folder
    ALLOWED_IMAGE_MIMETYPES = {'image/jpeg', 'image/png'}

    LOCKDOWN_AFTER_N_PASSWORD_ATTEMPTS = 10
    LOCKDOWN_FOR_N_SECONDS = 30 * 60  # 30 Minutes

    DEFAULT_EVENT_NEARBY_DISTANCE = 10  # Km
    DEFAULT_EVENT_MEDIUM_DISTANCE = 30  # Km
    DEFAULT_EVENT_MAXIMUM_DISTANCE = 50  # Km

    MESSAGE_BREAK_AFTER_DELTA = datetime.timedelta(days=1)

    APP_DIR = os.path.abspath(os.path.dirname(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, os.path.pardir))


class ProductionConfig(Config):
    ENV = "Production"
    DEBUG = False
    SERVER_NAME = os.environ['SERVER_NAME']
    MAIL_DEFAULT_SENDER = "Event App Notifier"
    SEND_EMAILS = True
    RATELIMIT_ENABLED = True


class DevelopmentConfig(Config):
    ENV = "Development"
    DEBUG = True
    MAIL_DEFAULT_SENDER = "Event App Notifier <Development>"
    SEND_EMAILS = True
    SERVER_NAME = "vent.local:8000"
    RATELIMIT_ENABLED = False
    SQLALCHEMY_POOL_SIZESQLALCHEMY_POOL_SIZE = 15


class TestingConfig(Config):
    ENV = "TESTING"
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    WTF_CSRF_ENABLED = False
    BCRYPT_LOG_ROUNDS = 4
    RATELIMIT_ENABLED = False
    RQ_ASYNC = False
    MAIL_DEFAULT_SENDER = "Event App Notifier <Testing>"


config_map = {
    "ProductionConfig": ProductionConfig,
    "DevelopmentConfig": DevelopmentConfig,
    "TestingConfig": TestingConfig
}
