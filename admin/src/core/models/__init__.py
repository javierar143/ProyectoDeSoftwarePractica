"""Importaciones de los modelos para registrar sus tablas."""

from src.core.models.Configuracion import Configuracion
from src.core.models.Cupo import Cupo
from src.core.models.Entrega import Entrega
from src.core.models.Pedido import Pedido
from src.core.models.Permiso import Permiso
from src.core.models.Personal import Personal
from src.core.models.Rol import Rol
from src.core.models.RolPoseePermiso import RolPoseePermiso
from src.core.models.Sector import Sector
from src.core.models.SectorCompuestoPorPersonal import (
    SectorCompuestoPorPersonal,
)
from src.core.models.Solicitud import Solicitud
from src.core.models.TipoComida import TipoComida
from src.core.models.TipoMenu import TipoMenu
from src.core.models.TipoPersonal import TipoPersonal
from src.core.models.Usuario import Usuario
from src.core.models.UsuarioEsJefeSector import UsuarioEsJefeSector

__all__ = [
    "Configuracion",
    "Cupo",
    "Entrega",
    "Pedido",
    "Permiso",
    "Personal",
    "Rol",
    "RolPoseePermiso",
    "Sector",
    "SectorCompuestoPorPersonal",
    "Solicitud",
    "TipoComida",
    "TipoMenu",
    "TipoPersonal",
    "Usuario",
    "UsuarioEsJefeSector",
]