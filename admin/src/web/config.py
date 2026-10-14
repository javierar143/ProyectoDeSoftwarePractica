import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'you-will-never-guess')
    TESTING = False
    SESSION_TYPE = 'filesystem'


class DevelopmentConfig(Config):
    TESTING = False

class TestingConfig(Config):
    TESTING = True

class ProductionConfig(Config):
    TESTING = False

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}