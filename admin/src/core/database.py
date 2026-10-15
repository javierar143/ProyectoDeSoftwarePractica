from flask_sqlalchemy_lite import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

db = SQLAlchemy()


def init_app(app):
    """Inicializa la conexión a la base de datos de la aplicación."""
    db.init_app(app)
    return db


# Modelo base requerido por la cátedra.
class BaseModel(DeclarativeBase):
    _abstract_ = True


# Inicialización y carga de datos del proyecto.
def reset_db():
    """Recrea las tablas y carga los datos iniciales de desarrollo."""

    from src.core.models.TipoComida import TipoComida
    from src.core.models.Solicitud import Solicitud
    from src.core.models.Pedido import Pedido
    from src.core.models.Cupo import Cupo

    # Recrear la estructura de la base de datos.
    BaseModel.metadata.drop_all(db.engine)
    BaseModel.metadata.create_all(db.engine)

    # Cargar los datos iniciales respetando las dependencias.
    from src.core.seeds.roles import load_roles
    from src.core.seeds.tipos_iniciales import load_tipos_iniciales
    from src.core.seeds.personal_inicial import load_personal_inicial
    from src.core.seeds.permisos import load_permisos

    load_roles()
    load_tipos_iniciales()
    load_personal_inicial()
    load_permisos()

    # Confirmar los cambios.
    db.session.commit()
