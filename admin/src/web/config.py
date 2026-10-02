import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'you-will-never-guess')
    TESTING = False
    SESSION_TYPE = 'filesystem'


class DevelopmentConfig(Config):
    TESTING = False
    DB_USER = os.environ['DB_USER']
    DB_PASSWORD = os.environ['DB_PASSWORD']
    DB_HOST = os.environ['DB_HOST']
    DB_PORT = os.environ['DB_PORT']
    DB_NAME = os.environ['DB_NAME']

    SQLALCHEMY_ENGINES = {
    "default": f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    }

class TestingConfig(Config):
    TESTING = True

class ProductionConfig(Config):
    TESTING = False
    SQLALCHEMY_DATABASE_URI = {
        'default': os.environ.get('DATABASE_URL')
    }

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}