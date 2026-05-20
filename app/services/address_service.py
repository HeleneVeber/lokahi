"""Service for Address business logic.

⚠️ IMPORTANT - Streamlit Hot-Reload Pattern:
All imports from app.models MUST be done inside methods (lazy imports)
to avoid SQLAlchemy double-registration during Streamlit hot-reload.
See CLAUDE.md section "Pattern Streamlit Hot-Reload" for details.
"""

from sqlmodel import Session, select

from app.schemas import AddressData


class AddressService:
    """Handles business logic for Address operations."""

    @staticmethod
    def get_or_create(session: Session, address: AddressData):
        """
        Get existing address or create new one.

        Args:
            session: Database session
            address: Address data

        Returns:
            Address instance
        """
        from app.models import Address  # Lazy import to avoid hot-reload issues
        
        existing_address = session.exec(
            select(Address).where(
                Address.cep == address.cep,
                Address.numero == address.numero,
                Address.complemento == address.complemento,
            )
        ).first()

        if existing_address:
            return existing_address

        new_address = Address(**address.model_dump())
        session.add(new_address)
        session.flush()
        return new_address
