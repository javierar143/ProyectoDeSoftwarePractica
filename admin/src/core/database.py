from flask_sqlalchemy_lite import SQLAlchemy
from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase

db = SQLAlchemy()


def init_app(app):
    """Inicializa la conexión a la base de datos de la aplicación."""
    db.init_app(app)
    return db


# Modelo base requerido por la cátedra.
class BaseModel(DeclarativeBase):
    _abstract_ = True


def _import_all_models():
    """Importa todos los modelos del sistema para que SQLAlchemy los registre."""
    import src.core.models  # noqa: F401
    from src.core.models.ApiToken import ApiToken  # noqa: F401
    from src.core.models.Configuracion import Configuracion  # noqa: F401
    from src.core.models.Cupo import Cupo  # noqa: F401
    from src.core.models.Entrega import Entrega  # noqa: F401
    from src.core.models.Pedido import Pedido  # noqa: F401
    from src.core.models.Permiso import Permiso  # noqa: F401
    from src.core.models.Personal import Personal  # noqa: F401
    from src.core.models.Rol import Rol  # noqa: F401
    from src.core.models.RolPoseePermiso import RolPoseePermiso  # noqa: F401
    from src.core.models.Sector import Sector  # noqa: F401
    from src.core.models.SectorCompuestoPorPersonal import SectorCompuestoPorPersonal  # noqa: F401
    from src.core.models.Solicitud import Solicitud  # noqa: F401
    from src.core.models.TipoComida import TipoComida  # noqa: F401
    from src.core.models.TipoMenu import TipoMenu  # noqa: F401
    from src.core.models.TipoPersonal import TipoPersonal  # noqa: F401
    from src.core.models.Usuario import Usuario  # noqa: F401
    from src.core.models.UsuarioEsJefeSector import UsuarioEsJefeSector  # noqa: F401


def seed_all():
    """Carga todos los datos iniciales respetando las dependencias."""
    from src.core.seeds.roles import load_roles
    from src.core.seeds.tipos_iniciales import load_tipos_iniciales
    from src.core.seeds.personal_inicial import load_personal_inicial
    from src.core.seeds.permisos import load_permisos
    from src.core.seeds.sectores import SECTORES_INICIALES
    from src.core.services.sectores import sector as sector_service

    load_roles()
    load_tipos_iniciales()
    load_personal_inicial()
    load_permisos()
    sector_service.seed(SECTORES_INICIALES)

    db.session.commit()


def reset_db():
    """Recrea las tablas y carga los datos iniciales de desarrollo."""
    _import_all_models()

    BaseModel.metadata.drop_all(db.engine)
    BaseModel.metadata.create_all(db.engine)

    seed_all()


def ensure_db_initialized():
    """Crea la estructura y carga los datos iniciales si la base de datos está vacía."""
    _import_all_models()
    inspector = inspect(db.engine)
    if not inspector.has_table("Usuario"):
        BaseModel.metadata.create_all(db.engine)
        seed_all()