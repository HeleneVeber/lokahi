import re
from sqlalchemy.orm import validates
from sqlmodel import Field, SQLModel
from validate_docbr import CNPJ, CPF


class Gestor(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: int | None = Field(default=None, primary_key=True)
    name: str
    cpf_cnpj: str = Field(unique=True)
    phone: str | None = None

    @validates("cpf_cnpj")
    def validate_cpf_cnpj(self, key: str, value: str) -> str:
        digits = re.sub(r"\D", "", value)
        if len(digits) == 11 and CPF().validate(value):
            return value
        if len(digits) == 14 and CNPJ().validate(value):
            return value
        raise ValueError("CPF/CNPJ inválido")
