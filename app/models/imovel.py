import pandas as pd
from sqlalchemy.exc import IntegrityError
from sqlmodel import Field, SQLModel, select
from app.database import get_session
from app.models.address import Address
from app.models.gestor import Gestor
from app.types import AddressData, GestorData
from app.utils.import_utils import parse_phone
from app.utils.viacep import fetch_address


class Imovel(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: int | None = Field(default=None, primary_key=True)
    nome: str = Field(unique=True)
    gestor_id: int | None = Field(default=None, foreign_key="gestor.id")
    address_id: int | None = Field(default=None, foreign_key="address.id")

    @classmethod
    def validate_rows(cls, df) -> tuple[list[dict], list[dict[str, str | None]]]:
        required = {"nome_imovel", "cep", "numero"}
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
                    {
                        "nome_imovel": str(row["nome_imovel"]),
                        "address": fetch_address(str(row["cep"])),
                        "numero": str(row["numero"]),
                        "complemento": str(row.get("complemento"))
                        if pd.notna(row.get("complemento"))
                        else None,
                        "cpf_gestor": str(row.get("cpf_gestor"))
                        if pd.notna(row.get("cpf_gestor"))
                        else None,
                        "nome_gestor": str(row.get("nome_gestor"))
                        if pd.notna(row.get("nome_gestor"))
                        else None,
                        "phone_gestor": parse_phone(row.get("phone_gestor"))
                        if pd.notna(row.get("phone_gestor"))
                        else None,
                    }
                )
            except ValueError as e:
                errors.append({"row": row["nome_imovel"], "error": str(e)})

        return valid, errors

    @classmethod
    def save_many(cls, imoveis: list[dict]) -> tuple[int, list[dict[str, str | None]]]:
        imported = 0
        errors = []
        with get_session() as session:
            for imovel in imoveis:
                try:
                    with session.begin_nested():
                        address = Address.get_or_create(
                            session,
                            AddressData(
                                cep=imovel["address"].cep,
                                logradouro=imovel["address"].logradouro,
                                numero=imovel["numero"],
                                complemento=imovel["complemento"],
                                bairro=imovel["address"].bairro,
                                localidade=imovel["address"].localidade,
                                uf=imovel["address"].uf,
                            ),
                        )
                        existing_imovel = session.exec(
                            select(cls).where(cls.address_id == address.id)
                        ).first()
                        if existing_imovel:
                            raise ValueError(
                                f"Este endereço já está cadastrado no imóvel '{existing_imovel.nome}'"
                            )

                        gestor_id = None
                        if imovel["cpf_gestor"]:
                            gestor = Gestor.get_or_create(
                                session,
                                GestorData(
                                    cpf_cnpj=imovel["cpf_gestor"],
                                    name=imovel["nome_gestor"],
                                    phone=imovel["phone_gestor"],
                                ),
                            )
                            gestor_id = gestor.id

                        session.add(
                            cls(
                                nome=imovel["nome_imovel"],
                                gestor_id=gestor_id,
                                address_id=address.id,
                            )
                        )
                        session.flush()

                        imported += 1

                except IntegrityError:
                    errors.append(
                        {
                            "row": imovel["nome_imovel"],
                            "error": "Nome de imóvel já cadastrado",
                        }
                    )

                except ValueError as e:
                    errors.append({"row": imovel["nome_imovel"], "error": str(e)})

            session.commit()
        return imported, errors
