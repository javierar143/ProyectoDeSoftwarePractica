import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "you-will-never-guess")
    TESTING = False
    SESSION_TYPE = "filesystem"


class DevelopmentConfig(Config):
    TESTING = False
    DB_USER = os.environ.get("DB_USER", "postgres")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "5432")
    DB_NAME = os.environ.get("DB_NAME", "grupo50")

    SQLALCHEMY_ENGINES = {
        "default": f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    }


class TestingConfig(Config):
    TESTING = True


class ProductionConfig(Config):
    TESTING = False
    SQLALCHEMY_ENGINES = {
        "default": os.environ.get("DATABASE_URL")
    }


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}