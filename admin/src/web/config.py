import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "you-will-never-guess")
    TESTING = False
    SESSION_TYPE = "filesystem"


class DevelopmentConfig(Config):
    TESTING = False
    CORS_ORIGINS = ["http://localhost:5173"]
    DB_USER = os.environ.get("DB_USER")
    DB_PASSWORD = os.environ.get("DB_PASSWORD")
    DB_HOST = os.environ.get("DB_HOST")
    DB_PORT = os.environ.get("DB_PORT")
    DB_NAME = os.environ.get("DB_NAME")
    SQLALCHEMY_ENGINES = {
        "default": f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    }

class TestingConfig(Config):
    TESTING = True
    CORS_ORIGINS = ["http://localhost:5173"]


class ProductionConfig(Config):
    TESTING = False
    CORS_ORIGINS = ["https://grupo50.proyecto2026.linti.unlp.edu.ar"]
    SQLALCHEMY_ENGINES = {
        "default": os.environ.get("DATABASE_URL")
    }


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}