import os


class Config:
    """Base Configuration"""

    SECRET_KEY = os.environ["EVENT_APP_SECRET"]
    BCRYPT_LOG_ROUNDS = 14
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    DEBUG_TB_TEMPLATE_EDITOR_ENABLED = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    APP_DIR = os.path.abspath(os.path.dirname(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, os.path.pardir))
    print(PROJECT_ROOT)


class ProductionConfig(Config):
    ENV = "Production"
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{ os.path.join(Config.PROJECT_ROOT, "prod.db") }'


class DevelopmentConfig(Config):
    ENV = "Development"
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{ os.path.join(Config.PROJECT_ROOT, "dev.db") }'


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
