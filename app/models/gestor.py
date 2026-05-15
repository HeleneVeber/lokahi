import re
from typing import Self
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import validates
from sqlmodel import Field, SQLModel, select
from validate_docbr import CNPJ, CPF
from app.database import get_session
from app.utils.import_utils import parse_phone
from app.types import GestorData


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

    @classmethod
    def get_or_create(cls, session, gestor: GestorData) -> "Gestor":
        existing = session.exec(
            select(cls).where(
                cls.cpf_cnpj == gestor.cpf_cnpj
                )
            ).first()
        if existing:
            return existing

        if not gestor.name:
            raise ValueError(f"Nome obrigatório para novo gestor com CPF/CNPJ {gestor.cpf_cnpj}")

        new = cls(**gestor.model_dump())
        session.add(new)
        session.flush()

        return new


    # Check if the file are all required columns and if the values are valid (e.g. cpf_cnpj format, phone number)
    @classmethod
    def validate_rows(cls, dataframe) -> tuple[list[Self], list[dict[str, str | None]]]:
        required = {
            key for key, field in cls.model_fields.items() if field.is_required()
        }
        missing = required - set(dataframe.columns)

        if missing:
            return [], [
                {
                    "row": None,
                    "error": f"Coluna obrigatória ausente: {', '.join(missing)}",
                }
            ]

        valid, errors = [], []
        for _, row in dataframe.iterrows():
            try:
                valid.append(
                    cls(
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
        cls, instances: list[Self]
    ) -> tuple[int, list[dict[str, str | None]]]:
        imported = 0
        errors = []
        with get_session() as session:
            for instance in instances:
                try:
                    # savepoint: if this row fails, only this row is rolled back
                    with session.begin_nested():
                        session.add(instance)
                        # flush sends SQL to DB without committing — triggers IntegrityError early
                        session.flush()
                    imported += 1
                except IntegrityError:
                    errors.append({"row": instance.name, "error": "CPF/CNPJ já cadastrado"})
            session.commit()
        return imported, errors
