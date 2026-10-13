from src.core.models.Rol import Rol
from src.core.models.Permiso import Permiso
from src.core.models.Usuario import Usuario
from src.core.models.RolPoseePermiso import RolPoseePermiso
from src.core.models.Personal import Personal
from src.core.models.TipoPersonal import TipoPersonal
from src.core.models.TipoMenu import TipoMenu
from src.core.models.Solicitud import Solicitud
from src.core.models.Entrega import Entrega
from src.core.models.Cupo import Cupo
from src.core.models.Pedido import Pedido

from src.core.models.SectorTemporal import SectorTemporal #borrar cuando se cree la tabla SECTOR


#inicio de codigo temporal
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import BaseModel


class TipoComidaTemporal(BaseModel):
    """Modelo temporal para resolver la dependencia de TipoComida."""

    __tablename__ = "TipoComida"

    idTipoComida: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )
    nombre: Mapped[str] = mapped_column(String, nullable=False)


#aaviso de fin de codigo temporal