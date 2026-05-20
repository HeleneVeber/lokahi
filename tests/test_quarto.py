"""Tests for Quarto model (US3.1)
"""
import pytest
from decimal import Decimal
from sqlmodel import Session, SQLModel, create_engine
from app.models import Address, Gestor, Imovel, Quarto
from app.schemas import ImovelData
from app.services import ImovelService


@pytest.fixture(name="session")
def session_fixture():
    """Create a fresh in-memory database for each test"""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="imovel")
def imovel_fixture(session: Session):
    """Create a test imovel"""
    address = Address(
        cep="01310-100",
        logradouro="Avenida Paulista",
        numero="1000",
        bairro="Bela Vista",
        localidade="São Paulo",
        uf="SP"
    )
    session.add(address)
    session.flush()
    
    imovel = Imovel(
        nome="Coliving Teste",
        address_id=address.id
    )
    session.add(imovel)
    session.commit()
    session.refresh(imovel)
    return imovel


def test_create_quarto(session: Session, imovel: Imovel):
    """Test: create a simple quarto"""
    quarto = Quarto(
        imovel_id=imovel.id,
        numero="101",
        tipo="Single",
        area_m2=12.5,
        valor_aluguel=Decimal("1200.00")
    )
    session.add(quarto)
    session.commit()
    session.refresh(quarto)
    
    assert quarto.id is not None
    assert quarto.numero == "101"
    assert quarto.tipo == "Single"
    assert quarto.area_m2 == 12.5
    assert quarto.valor_aluguel == Decimal("1200.00")
    assert quarto.imovel_id == imovel.id


def test_read_quarto(session: Session, imovel: Imovel):
    """Test: read a quarto from database"""
    # Create a quarto
    quarto = Quarto(
        imovel_id=imovel.id,
        numero="102",
        tipo="Double",
        area_m2=18.0,
        valor_aluguel=Decimal("1500.00")
    )
    session.add(quarto)
    session.commit()
    quarto_id = quarto.id
    
    # Read it back
    retrieved = session.get(Quarto, quarto_id)
    
    assert retrieved is not None
    assert retrieved.numero == "102"
    assert retrieved.tipo == "Double"
    assert retrieved.area_m2 == 18.0
    assert retrieved.valor_aluguel == Decimal("1500.00")


def test_update_quarto(session: Session, imovel: Imovel):
    """Test: update a quarto"""
    # Create a quarto
    quarto = Quarto(
        imovel_id=imovel.id,
        numero="103",
        tipo="Single",
        area_m2=10.0,
        valor_aluguel=Decimal("1000.00")
    )
    session.add(quarto)
    session.commit()
    quarto_id = quarto.id
    
    # Update it
    retrieved = session.get(Quarto, quarto_id)
    retrieved.tipo = "Suite"
    retrieved.area_m2 = 15.0
    retrieved.valor_aluguel = Decimal("1800.00")
    session.commit()
    
    # Verify changes
    updated = session.get(Quarto, quarto_id)
    assert updated.numero == "103"  # unchanged
    assert updated.tipo == "Suite"  # changed
    assert updated.area_m2 == 15.0  # changed
    assert updated.valor_aluguel == Decimal("1800.00")  # changed


def test_delete_quarto(session: Session, imovel: Imovel):
    """Test: delete a quarto"""
    # Create a quarto
    quarto = Quarto(
        imovel_id=imovel.id,
        numero="104",
        valor_aluguel=Decimal("1200.00")
    )
    session.add(quarto)
    session.commit()
    quarto_id = quarto.id
    
    # Delete it
    retrieved = session.get(Quarto, quarto_id)
    session.delete(retrieved)
    session.commit()
    
    # Verify it's gone
    deleted = session.get(Quarto, quarto_id)
    assert deleted is None


def test_unique_constraint_numero_per_imovel(session: Session, imovel: Imovel):
    """Test: numero must be unique per imovel (UniqueConstraint)"""
    from sqlalchemy.exc import IntegrityError
    
    # Create first quarto
    quarto1 = Quarto(
        imovel_id=imovel.id,
        numero="105",
        valor_aluguel=Decimal("1200.00")
    )
    session.add(quarto1)
    session.commit()
    
    # Try to create another quarto with same numero in same imovel
    quarto2 = Quarto(
        imovel_id=imovel.id,
        numero="105",  # SAME numero
        valor_aluguel=Decimal("1500.00")
    )
    session.add(quarto2)
    
    # Should raise IntegrityError
    with pytest.raises(IntegrityError):
        session.commit()


def test_imovel_is_coliving_property(session: Session, imovel: Imovel):
    """Test: Imovel.is_coliving returns True when imovel has quartos"""
    # Initially, no quartos
    session.refresh(imovel)
    assert imovel.is_coliving is False
    
    # Add a quarto
    quarto = Quarto(
        imovel_id=imovel.id,
        numero="201",
        valor_aluguel=Decimal("1000.00")
    )
    session.add(quarto)
    session.commit()
    
    # Now it should be a coliving
    session.refresh(imovel)
    assert imovel.is_coliving is True


def test_imovel_total_quartos_property(session: Session, imovel: Imovel):
    """Test: Imovel.total_quartos counts the number of quartos"""
    # Initially, no quartos
    session.refresh(imovel)
    assert imovel.total_quartos == 0
    
    # Add first quarto
    quarto1 = Quarto(
        imovel_id=imovel.id,
        numero="301",
        valor_aluguel=Decimal("1000.00")
    )
    session.add(quarto1)
    session.commit()
    session.refresh(imovel)
    assert imovel.total_quartos == 1
    
    # Add second quarto
    quarto2 = Quarto(
        imovel_id=imovel.id,
        numero="302",
        valor_aluguel=Decimal("1200.00")
    )
    session.add(quarto2)
    session.commit()
    session.refresh(imovel)
    assert imovel.total_quartos == 2
    
    # Delete one quarto
    session.delete(quarto1)
    session.commit()
    session.refresh(imovel)
    assert imovel.total_quartos == 1
