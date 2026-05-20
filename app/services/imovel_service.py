"""Service for Imovel business logic.

⚠️ IMPORTANT - Streamlit Hot-Reload Pattern:
All imports from app.models MUST be done inside methods (lazy imports)
to avoid SQLAlchemy double-registration during Streamlit hot-reload.
See CLAUDE.md section "Pattern Streamlit Hot-Reload" for details.
"""

import pandas as pd
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.database import get_session
from app.schemas import AddressData, GestorData, ImovelData
from app.services.address_service import AddressService
from app.services.gestor_service import GestorService
from app.utils.import_utils import parse_phone
from app.utils.viacep import fetch_address


class ImovelService:
    """Handles business logic for Imovel operations."""

    @staticmethod
    def create(session: Session, imovel: ImovelData):
        """
        Create a new imovel.

        Args:
            session: Database session
            imovel: Imovel data

        Returns:
            Created Imovel instance

        Raises:
            ValueError: If address already exists for another imovel
        """
        from app.models import Imovel  # Lazy import to avoid hot-reload issues
        
        viacep = fetch_address(imovel.cep)
        address = AddressService.get_or_create(
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

        existing = session.exec(select(Imovel).where(Imovel.address_id == address.id)).first()
        if existing:
            raise ValueError(
                f"Este endereço já está cadastrado no imóvel '{existing.nome}'"
            )

        gestor_id = imovel.gestor_id
        if gestor_id is None and imovel.cpf_gestor:
            gestor, _ = GestorService.get_or_create(
                session,
                GestorData(
                    cpf_cnpj=imovel.cpf_gestor,
                    name=imovel.nome_gestor,
                    phone=imovel.phone_gestor,
                ),
            )
            gestor_id = gestor.id

        new_imovel = Imovel(
            nome=imovel.nome_imovel, gestor_id=gestor_id, address_id=address.id
        )
        session.add(new_imovel)
        session.flush()
        return new_imovel

    @staticmethod
    def validate_rows(df) -> tuple[list[ImovelData], list[dict[str, str | None]]]:
        """
        Validate DataFrame rows for imovel import.

        Args:
            df: DataFrame with imovel data

        Returns:
            Tuple of (valid ImovelData list, error list)
        """
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
            valid.append(
                ImovelData(
                    nome_imovel=str(row["nome_imovel"]),
                    cep=str(row["cep"]),
                    numero=str(row["numero"]),
                    complemento=str(row["complemento"])
                    if pd.notna(row.get("complemento"))
                    else None,
                    cpf_gestor=str(row["cpf_gestor"])
                    if pd.notna(row.get("cpf_gestor"))
                    else None,
                    nome_gestor=str(row["nome_gestor"])
                    if pd.notna(row.get("nome_gestor"))
                    else None,
                    phone_gestor=parse_phone(row.get("phone_gestor"))
                    if pd.notna(row.get("phone_gestor"))
                    else None,
                )
            )

        return valid, []

    @staticmethod
    def save_many(
        imoveis: list[ImovelData], session: Session | None = None
    ) -> tuple[int, list[dict[str, str | None]]]:
        """
        Save multiple imoveis to database.

        Args:
            imoveis: List of ImovelData to save
            session: Optional session (for testing). If None, creates new session.

        Returns:
            Tuple of (imported count, error list)
        """
        imported = 0
        errors = []

        def _save_in_session(sess: Session):
            nonlocal imported, errors
            for imovel in imoveis:
                try:
                    with sess.begin_nested():
                        ImovelService.create(sess, imovel)
                        imported += 1

                except (ValueError, IntegrityError) as e:
                    errors.append({"row": imovel.nome_imovel, "error": str(e)})

            sess.commit()

        if session:
            _save_in_session(session)
        else:
            with get_session() as sess:
                _save_in_session(sess)

        return imported, errors
