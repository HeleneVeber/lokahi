"""Tests for GestorService."""

import pandas as pd
import pytest
from sqlmodel import Session, create_engine

from app.models import Gestor
from app.schemas import GestorData
from app.services.gestor_service import GestorService


@pytest.fixture
def session():
    """Create in-memory SQLite session for testing."""
    from sqlmodel import SQLModel
    from app.models import Address, Gestor, Imovel, Quarto  # noqa: F401

    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def service():
    """Create GestorService instance."""
    return GestorService()


class TestGetOrCreate:
    """Tests for GestorService.get_or_create()."""

    def test_create_new_gestor(self, service, session):
        """Should create a new gestor when CPF doesn't exist."""
        data = GestorData(cpf_cnpj="111.444.777-35", name="João Silva", phone="11999999999")

        gestor, created = service.get_or_create(session, data)

        assert created is True
        assert gestor.name == "João Silva"
        assert gestor.cpf_cnpj == "111.444.777-35"
        assert gestor.phone == "11999999999"

    def test_get_existing_gestor(self, service, session):
        """Should return existing gestor when CPF already exists."""
        # Create gestor first
        existing = Gestor(cpf_cnpj="111.444.777-35", name="João Silva", phone="11999999999")
        session.add(existing)
        session.commit()

        # Try to create again
        data = GestorData(cpf_cnpj="111.444.777-35", name="João Santos")

        gestor, created = service.get_or_create(session, data)

        assert created is False
        assert gestor.id == existing.id
        assert gestor.name == "João Silva"  # Should keep original name

    def test_require_name_for_new_gestor(self, service, session):
        """Should raise ValueError when creating new gestor without name."""
        data = GestorData(cpf_cnpj="111.444.777-35", name=None)

        with pytest.raises(ValueError, match="Nome obrigatório"):
            service.get_or_create(session, data)


class TestValidateRows:
    """Tests for GestorService.validate_rows()."""

    def test_valid_rows(self, service):
        """Should validate all rows when data is correct."""
        df = pd.DataFrame(
            [
                {"name": "João Silva", "cpf_cnpj": "111.444.777-35", "phone": "11999999999"},
                {"name": "Maria Santos", "cpf_cnpj": "529.982.247-25", "phone": None},
            ]
        )

        valid, errors = service.validate_rows(df)

        assert len(valid) == 2
        assert len(errors) == 0
        assert valid[0].name == "João Silva"
        assert valid[1].phone is None

    def test_missing_required_columns(self, service):
        """Should return error when required columns are missing."""
        df = pd.DataFrame([{"name": "João Silva"}])  # missing cpf_cnpj

        valid, errors = service.validate_rows(df)

        assert len(valid) == 0
        assert len(errors) == 1
        assert "cpf_cnpj" in errors[0]["error"]

    def test_invalid_data_in_row(self, service):
        """Should collect errors for invalid rows but continue processing."""
        df = pd.DataFrame(
            [
                {"name": "João Silva", "cpf_cnpj": "111.444.777-35", "phone": "11999999999"},
                {"name": "Invalid", "cpf_cnpj": None, "phone": "11999999999"},  # will fail
                {"name": "Maria Santos", "cpf_cnpj": "529.982.247-25", "phone": None},
            ]
        )

        valid, errors = service.validate_rows(df)

        assert len(valid) == 2  # first and third row
        assert len(errors) == 1  # second row failed
        assert "Invalid" in errors[0]["row"]


class TestSaveMany:
    """Tests for GestorService.save_many()."""

    def test_save_multiple_gestores(self, service, session):
        """Should save all valid gestores."""
        gestores = [
            GestorData(cpf_cnpj="111.444.777-35", name="João Silva"),
            GestorData(cpf_cnpj="529.982.247-25", name="Maria Santos"),
        ]

        imported, errors = service.save_many(gestores, session)

        assert imported == 2
        assert len(errors) == 0

    def test_reject_duplicate_cpf(self, service, session):
        """Should reject gestor with duplicate CPF."""
        gestores = [
            GestorData(cpf_cnpj="111.444.777-35", name="João Silva"),
            GestorData(cpf_cnpj="111.444.777-35", name="João Santos"),  # duplicate
        ]

        imported, errors = service.save_many(gestores, session)

        assert imported == 1
        assert len(errors) == 1
        assert "já cadastrado" in errors[0]["error"]

    def test_continue_after_error(self, service, session):
        """Should continue saving after encountering an error."""
        gestores = [
            GestorData(cpf_cnpj="111.444.777-35", name="João Silva"),
            GestorData(cpf_cnpj="111.444.777-35", name="Duplicate"),  # will fail
            GestorData(cpf_cnpj="529.982.247-25", name="Maria Santos"),  # should succeed
        ]

        imported, errors = service.save_many(gestores, session)

        assert imported == 2
        assert len(errors) == 1
