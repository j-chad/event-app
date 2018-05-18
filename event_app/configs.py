# coding=utf-8
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

    LOCKDOWN_AFTER_N_PASSWORD_ATTEMPTS = 10
    LOCKDOWN_FOR_N_SECONDS = 30 * 60  # 30 Minutes

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
    RATELIMIT_ENABLED = False


class TestingConfig(Config):
    ENV = "TESTING"
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    WTF_CSRF_ENABLED = False
    BCRYPT_LOG_ROUNDS = 4
    RATELIMIT_ENABLED = False


config_map = {
    "ProductionConfig" : ProductionConfig,
    "DevelopmentConfig": DevelopmentConfig,
    "TestingConfig"    : TestingConfig
}
