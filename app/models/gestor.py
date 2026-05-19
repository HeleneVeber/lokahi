import re
from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlalchemy.orm import validates
from sqlmodel import Field, Relationship, SQLModel, select
from validate_docbr import CNPJ, CPF

from app.database import get_session
from app.utils.import_utils import parse_phone

if TYPE_CHECKING:
    from app.models.imovel import Imovel


class GestorData(BaseModel):
    cpf_cnpj: str
    name: str | None = None
    phone: str | None = None


class Gestor(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: int | None = Field(default=None, primary_key=True)
    name: str
    cpf_cnpj: str = Field(unique=True)
    phone: str | None = None

    imoveis: list["Imovel"] = Relationship(back_populates="gestor")

    def display(self) -> dict:
        return {"Nome": self.name, "CPF/CNPJ": self.cpf_cnpj, "Telefone": self.phone}

    @validates("cpf_cnpj")
    def validate_cpf_cnpj(self, _: str, value: str) -> str:
        digits = re.sub(r"\D", "", value)
        if len(digits) == 11 and CPF().validate(value):
            return value
        if len(digits) == 14 and CNPJ().validate(value):
            return value
        raise ValueError("CPF/CNPJ inválido")

    @classmethod
    def get_or_create(cls, session, gestor: GestorData) -> tuple["Gestor", bool]:
        existing = session.exec(
            select(cls).where(cls.cpf_cnpj == gestor.cpf_cnpj)
        ).first()
        if existing:
            return existing, False

        if not gestor.name:
            raise ValueError(
                f"Nome obrigatório para novo gestor com CPF/CNPJ {gestor.cpf_cnpj}"
            )

        new = cls(**gestor.model_dump())
        session.add(new)
        session.flush()

        return new, True

    # Check if the file are all required columns and if the values are valid (e.g. cpf_cnpj format, phone number)
    @classmethod
    def validate_rows(cls, df) -> tuple[list[GestorData], list[dict[str, str | None]]]:
        required = {"name", "cpf_cnpj"}
        missing = required - set(df.columns)

        if missing:
            return [], [
                {
                    "row": None,
                    "error": f"Coluna obrigatória ausente: {', '.join(missing)}",
                }
            ]

        valid, errors = [], []
        for _, row in df.iterrows():
            try:
                valid.append(
                    GestorData(
                        name=str(row["name"]),
                        cpf_cnpj=str(row["cpf_cnpj"]),
                        phone=parse_phone(row.get("phone")),
                    )
                )
            except ValueError as e:
                errors.append({"row": row["name"], "error": str(e)})

        return valid, errors

    @classmethod
    def save_many(
        cls, gestores: list[GestorData]
    ) -> tuple[int, list[dict[str, str | None]]]:
        imported = 0
        errors = []
        with get_session() as session:
            for gestor in gestores:
                try:
                    # savepoint: if this row fails, only this row is rolled back
                    with session.begin_nested():
                        _, created = cls.get_or_create(session, gestor)
                        if not created:
                            raise ValueError("CPF/CNPJ já cadastrado")
                        imported += 1
                except ValueError as e:
                    errors.append({"row": gestor.name, "error": str(e)})
            session.commit()
        return imported, errors
