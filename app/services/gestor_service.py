"""Service for Gestor business logic.

⚠️ IMPORTANT - Streamlit Hot-Reload Pattern:
All imports from app.models MUST be done inside methods (lazy imports)
to avoid SQLAlchemy double-registration during Streamlit hot-reload.

Example:
    ❌ WRONG (top-level import):
        from app.models import Gestor
        class GestorService:
            def method(self): ...
    
    ✅ CORRECT (lazy import):
        class GestorService:
            def method(self):
                from app.models import Gestor  # Import here
                ...

See CLAUDE.md section "Pattern Streamlit Hot-Reload" for full explanation.
"""

from sqlmodel import Session, select

from app.database import get_session
from app.schemas import GestorData
from app.utils.import_utils import parse_phone


class GestorService:
    """Handles business logic for Gestor operations."""

    @staticmethod
    def get_or_create(session: Session, gestor: GestorData):
        """
        Get existing gestor by CPF or create new one.

        Args:
            session: Database session
            gestor: Gestor data

        Returns:
            Tuple of (Gestor instance, created flag)

        Raises:
            ValueError: If creating new gestor without name
        """
        from app.models import Gestor  # Lazy import to avoid hot-reload issues
        
        existing = session.exec(
            select(Gestor).where(Gestor.cpf_cnpj == gestor.cpf_cnpj)
        ).first()

        if existing:
            return existing, False

        if not gestor.name:
            raise ValueError(
                f"Nome obrigatório para novo gestor com CPF/CNPJ {gestor.cpf_cnpj}"
            )

        new_gestor = Gestor(**gestor.model_dump())
        session.add(new_gestor)
        session.flush()

        return new_gestor, True

    @staticmethod
    def validate_rows(df) -> tuple[list[GestorData], list[dict[str, str | None]]]:
        """
        Validate DataFrame rows for gestor import.

        Args:
            df: DataFrame with gestor data

        Returns:
            Tuple of (valid GestorData list, error list)
        """
        import pandas as pd
        
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
                # Check for None/NaN in required fields
                if pd.isna(row["cpf_cnpj"]):
                    raise ValueError("CPF/CNPJ não pode ser vazio")
                
                valid.append(
                    GestorData(
                        name=str(row["name"]),
                        cpf_cnpj=str(row["cpf_cnpj"]),
                        phone=parse_phone(row.get("phone")),
                    )
                )
            except (ValueError, KeyError) as e:
                errors.append({"row": str(row.get("name", "unknown")), "error": str(e)})

        return valid, errors

    @staticmethod
    def save_many(
        gestores: list[GestorData], session: Session | None = None
    ) -> tuple[int, list[dict[str, str | None]]]:
        """
        Save multiple gestores to database.

        Args:
            gestores: List of GestorData to save
            session: Optional session (for testing). If None, creates new session.

        Returns:
            Tuple of (imported count, error list)
        """
        imported = 0
        errors = []

        def _save_in_session(sess: Session):
            nonlocal imported, errors
            for gestor in gestores:
                try:
                    # savepoint: if this row fails, only this row is rolled back
                    with sess.begin_nested():
                        _, created = GestorService.get_or_create(sess, gestor)
                        if not created:
                            raise ValueError("CPF/CNPJ já cadastrado")
                        imported += 1
                except ValueError as e:
                    errors.append({"row": gestor.name, "error": str(e)})

            sess.commit()

        if session:
            _save_in_session(session)
        else:
            with get_session() as sess:
                _save_in_session(sess)

        return imported, errors
