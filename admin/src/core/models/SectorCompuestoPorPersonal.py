"""Modelo que representa la relacion entre un sector y el personal que lo compone."""
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.database import BaseModel

class SectorCompuestoPorPersonal(BaseModel):
    __tablename__ = "SectorCompuestoPorPersonal"

    idSector: Mapped[int] = mapped_column(ForeignKey("Sector.idSector"), primary_key=True)
    idPersonal: Mapped[int] = mapped_column(ForeignKey("Personal.idPersonal"), primary_key=True)