import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import SQLModel, Session, create_engine

from app.models.gestor import Gestor

engine = create_engine("sqlite:///:memory:")

VALID_CPF = "529.982.247-25"
VALID_CNPJ = "11.222.333/0001-81"
INVALID_DOC = "123.456.789-00"


def setup_function():
    SQLModel.metadata.create_all(engine)


def teardown_function():
    SQLModel.metadata.drop_all(engine)


def test_create_gestor():
    with Session(engine) as session:
        gestor = Gestor(name="João Silva", cpf_cnpj=VALID_CPF, phone="11999999999")
        session.add(gestor)
        session.commit()
        session.refresh(gestor)

    assert gestor.id is not None
    assert gestor.name == "João Silva"


def test_create_gestor_with_cnpj():
    with Session(engine) as session:
        gestor = Gestor(name="Imobiliária ABC", cpf_cnpj=VALID_CNPJ, phone="11999999999")
        session.add(gestor)
        session.commit()
        session.refresh(gestor)

    assert gestor.id is not None


def test_invalid_cpf_cnpj_raises_error():
    with pytest.raises(ValueError, match="CPF/CNPJ inválido"):
        Gestor(name="João Silva", cpf_cnpj=INVALID_DOC, phone="11999999999")


def test_duplicate_cpf_cnpj_raises_error():
    with pytest.raises(IntegrityError):
        with Session(engine) as session:
            gestor1 = Gestor(name="João Silva", cpf_cnpj=VALID_CPF, phone="11999999999")
            gestor2 = Gestor(name="Maria Costa", cpf_cnpj=VALID_CPF, phone="11888888888")
            session.add(gestor1)
            session.add(gestor2)
            session.commit()


def test_read_gestor():
    with Session(engine) as session:
        gestor = Gestor(name="João Silva", cpf_cnpj=VALID_CPF, phone="11999999999")
        session.add(gestor)
        session.commit()
        session.refresh(gestor)
        gestor_id = gestor.id

    with Session(engine) as session:
        found = session.get(Gestor, gestor_id)

    assert found is not None
    assert found.name == "João Silva"


def test_update_gestor():
    with Session(engine) as session:
        gestor = Gestor(name="João Silva", cpf_cnpj=VALID_CPF, phone="11999999999")
        session.add(gestor)
        session.commit()
        session.refresh(gestor)
        gestor_id = gestor.id

    with Session(engine) as session:
        gestor = session.get(Gestor, gestor_id)
        gestor.name = "João Santos"
        session.commit()
        session.refresh(gestor)

    assert gestor.name == "João Santos"


def test_delete_gestor():
    with Session(engine) as session:
        gestor = Gestor(name="João Silva", cpf_cnpj=VALID_CPF, phone="11999999999")
        session.add(gestor)
        session.commit()
        session.refresh(gestor)
        gestor_id = gestor.id

    with Session(engine) as session:
        gestor = session.get(Gestor, gestor_id)
        session.delete(gestor)
        session.commit()

    with Session(engine) as session:
        deleted = session.get(Gestor, gestor_id)

    assert deleted is None
