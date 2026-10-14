from flask_sqlalchemy_lite import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

db = SQLAlchemy()

def init_app(app):
    db.init_app(app)
    return db

class BaseModel(DeclarativeBase):
    _abstract_ = True

def reset_db():
    # recordar importar los modelos acá from src.core import models

    from src.core import models
    
    BaseModel.metadata.drop_all(db.engine)
    BaseModel.metadata.create_all(db.engine)






