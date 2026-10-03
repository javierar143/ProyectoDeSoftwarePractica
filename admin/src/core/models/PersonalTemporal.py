from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import BaseModel


class PersonalTemporal(BaseModel):
    __tablename__ = "Personal"

    idPersonal: Mapped[int] = mapped_column(primary_key=True)