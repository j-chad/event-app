# coding=utf-8
import datetime
import os


class Config:
    """Base Configuration"""
    BCRYPT_LOG_ROUNDS = 14
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    DEBUG_TB_TEMPLATE_EDITOR_ENABLED = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 465
    MAIL_USERNAME = 'event.app.notifier@gmail.com'
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    REDIS_URL = "redis://localhost:6379/0"
    RQ_REDIS_URL = REDIS_URL
    RATELIMIT_STORAGE_URL = REDIS_URL
    VERIFICATION_TOKEN_EXPIRY = 12 * 60 * 60  # 12 Hours
    RECOVERY_TOKEN_EXPIRY = 20 * 60  # 20 Minutes
    RECAPTCHA_PUBLIC_KEY = "6LeZl1gUAAAAAARV1XA2pNUXSKhvn89crZVrT_FY"
    MINIMUM_PASSWORD_LENGTH = 8
    RATELIMIT_KEY_PREFIX = "RATELIMITER#"
    MAPBOX_ACCESS_TOKEN = "pk.eyJ1Ijoiai1jaGFkIiwiYSI6ImNqajIzenFpMTB6ZHczd3Bjam50cmUwa2wifQ.mQ8rOg6dSN3P2EnUweer8g"

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
    SERVER_NAME = "vent.local:8000"
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
