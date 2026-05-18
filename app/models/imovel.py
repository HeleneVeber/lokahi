import pandas as pd
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlmodel import Field, Relationship, SQLModel, select
from app.database import get_session
from app.models.address import Address, AddressData
from app.models.gestor import Gestor, GestorData
from app.utils.import_utils import parse_phone
from app.utils.viacep import fetch_address


class ImovelData(BaseModel):
    nome_imovel: str
    cep: str
    numero: str
    complemento: str | None = None
    gestor_id: int | None = None
    cpf_gestor: str | None = None
    nome_gestor: str | None = None
    phone_gestor: str | None = None


class Imovel(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: int | None = Field(default=None, primary_key=True)
    nome: str = Field(unique=True)
    gestor_id: int | None = Field(default=None, foreign_key="gestor.id")
    address_id: int | None = Field(foreign_key="address.id")

    gestor: Gestor | None = Relationship(back_populates="imoveis")
    address: Address = Relationship(back_populates="imovel")

    def display(self) -> dict:
        return {
            "Nome": self.nome,
            "Endereço": self.address.format(),
            "Gestor": self.gestor.name if self.gestor else "-",
        }

    @classmethod
    def create(cls, session, imovel: ImovelData) -> "Imovel":
        viacep = fetch_address(imovel.cep)
        address = Address.get_or_create(
            session,
            AddressData(
                cep=viacep.cep,
                logradouro=viacep.logradouro,
                numero=imovel.numero,
                complemento=imovel.complemento,
                bairro=viacep.bairro,
                localidade=viacep.localidade,
                uf=viacep.uf,
            ),
        )
        existing = session.exec(select(cls).where(cls.address_id == address.id)).first()
        if existing:
            raise ValueError(
                f"Este endereço já está cadastrado no imóvel '{existing.nome}'"
            )
        gestor_id = imovel.gestor_id
        if gestor_id is None and imovel.cpf_gestor:
            gestor, _ = Gestor.get_or_create(
                session,
                GestorData(
                    cpf_cnpj=imovel.cpf_gestor,
                    name=imovel.nome_gestor,
                    phone=imovel.phone_gestor,
                ),
            )
            gestor_id = gestor.id

        new_imovel = cls(
            nome=imovel.nome_imovel, gestor_id=gestor_id, address_id=address.id
        )
        session.add(new_imovel)
        session.flush()
        return new_imovel

    @classmethod
    def validate_rows(cls, df) -> tuple[list[ImovelData], list[dict[str, str | None]]]:
        required = {"nome_imovel", "cep", "numero"}
        missing = required - set(df.columns)

        if missing:
            return [], [
                {
                    "row": None,
                    "error": f"Coluna obrigatória ausente: {', '.join(missing)}",
                }
            ]

        valid = []
        for _, row in df.iterrows():
            valid.append(ImovelData(
                nome_imovel=str(row["nome_imovel"]),
                cep=str(row["cep"]),
                numero=str(row["numero"]),
                complemento=str(row["complemento"]) if pd.notna(row.get("complemento")) else None,
                cpf_gestor=str(row["cpf_gestor"]) if pd.notna(row.get("cpf_gestor")) else None,
                nome_gestor=str(row["nome_gestor"]) if pd.notna(row.get("nome_gestor")) else None,
                phone_gestor=parse_phone(row.get("phone_gestor")) if pd.notna(row.get("phone_gestor")) else None,
            ))

        return valid, []

    @classmethod
    def save_many(
        cls, imoveis: list[ImovelData]
    ) -> tuple[int, list[dict[str, str | None]]]:
        imported = 0
        errors = []
        with get_session() as session:
            for imovel in imoveis:
                try:
                    with session.begin_nested():
                        cls.create(session, imovel)
                        imported += 1

                except (ValueError, IntegrityError) as e:
                    errors.append({"row": imovel.nome_imovel, "error": str(e)})

            session.commit()
        return imported, errors
