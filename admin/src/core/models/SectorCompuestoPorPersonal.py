"""Modelo que representa la relación entre un sector y el personal que lo compone."""
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.db import db

class SectorCompuestoPorPersonal(db.Model):
    __tablename__ = "SectorCompuestoPorPersonal"

    idSector: Mapped[int] = mapped_column(ForeignKey("sector.idSector"), primary_key=True)
    idPersonal: Mapped[int] = mapped_column(ForeignKey("Personal.idPersonal"), primary_key=True)

    # Relaciones de navegacion
    sector = relationship("Sector", back_populates="personal_asociado")
    personal = relationship("Personal", back_populates="sectores_asignados")
