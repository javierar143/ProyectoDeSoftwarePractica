import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "you-will-never-guess")
    TESTING = False
    SESSION_TYPE = "filesystem"
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
    COOKIE_SECURE = False



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
    COOKIE_SECURE = True
    GOOGLE_CLIENT_ID = (
        os.environ.get("GOOGLE_CLIENT_ID")
        or "701054035330-m5c4op59s9gkmh24upeocfdrgik1s6q3.apps.googleusercontent.com"
    )
    CORS_ORIGINS = ["https://grupo50.proyecto2026.linti.unlp.edu.ar"]
    SQLALCHEMY_ENGINES = {
        "default": os.environ.get("DATABASE_URL")
    }


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
