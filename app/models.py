"""Database models (table definitions only - no business logic)."""

import re
from decimal import Decimal
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import validates
from sqlmodel import Field, Relationship, SQLModel
from validate_docbr import CNPJ, CPF


class Address(SQLModel, table=True):
    """Address table - stores physical addresses."""

    __table_args__ = {"extend_existing": True}

    id: int | None = Field(default=None, primary_key=True)
    cep: str
    logradouro: str
    numero: str
    complemento: str | None = None
    bairro: str
    localidade: str
    uf: str

    # Relationships
    imovel: Optional["Imovel"] = Relationship(back_populates="address")

    def format(self) -> str:
        """Format address for display."""
        complemento = f", {self.complemento}" if self.complemento else ""
        return f"{self.logradouro}, {self.numero}{complemento} — {self.bairro}, {self.localidade} - {self.uf}"


class Gestor(SQLModel, table=True):
    """Gestor table - property managers/owners."""

    __table_args__ = {"extend_existing": True}

    id: int | None = Field(default=None, primary_key=True)
    name: str
    cpf_cnpj: str = Field(unique=True)
    phone: str | None = None

    # Relationships
    imoveis: list["Imovel"] = Relationship(back_populates="gestor")

    @validates("cpf_cnpj")
    def validate_cpf_cnpj(self, _: str, value: str) -> str:
        """Validate CPF or CNPJ format."""
        digits = re.sub(r"\D", "", value)
        if len(digits) == 11 and CPF().validate(value):
            return value
        if len(digits) == 14 and CNPJ().validate(value):
            return value
        raise ValueError("CPF/CNPJ inválido")


class Imovel(SQLModel, table=True):
    """Imovel table - properties/buildings."""

    __table_args__ = {"extend_existing": True}

    id: int | None = Field(default=None, primary_key=True)
    nome: str = Field(unique=True)
    gestor_id: int | None = Field(default=None, foreign_key="gestor.id")
    address_id: int | None = Field(foreign_key="address.id")

    # Relationships
    gestor: Optional["Gestor"] = Relationship(back_populates="imoveis")
    address: "Address" = Relationship(back_populates="imovel")
    quartos: list["Quarto"] = Relationship(back_populates="imovel")  # type: ignore[assignment]

    @property
    def is_coliving(self) -> bool:
        """Check if property is a coliving (has multiple rooms)."""
        return len(self.quartos) > 0

    @property
    def total_quartos(self) -> int:
        """Total number of rooms in this property."""
        return len(self.quartos)


class Quarto(SQLModel, table=True):
    """Quarto table - rooms within properties."""

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

    # Relationships
    imovel: "Imovel" = Relationship(back_populates="quartos")
