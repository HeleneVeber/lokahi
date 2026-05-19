from decimal import Decimal
from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.imovel import Imovel


class QuartoData(BaseModel):
    numero: str


class Quarto(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("imovel_id", "numero"),
        {"extend_existing": True},
    )
    id: int | None = Field(default=None, primary_key=True)
    imovel_id: int = Field(foreign_key="imovel.id")
    numero: str
    tipo: str | None = None
    area_m2: float | None = None
    valor_aluguel: Decimal

    imovel: "Imovel" = Relationship(back_populates="quartos")
