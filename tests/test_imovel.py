import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import SQLModel, Session, create_engine

from app.models.address import Address
from app.models.gestor import Gestor
from app.models.imovel import Imovel

engine = create_engine("sqlite:///:memory:")

VALID_CPF = "529.982.247-25"
ADDRESS_DATA = {
    "cep": "01310-100",
    "logradouro": "Avenida Paulista",
    "numero": "1578",
    "bairro": "Bela Vista",
    "localidade": "São Paulo",
    "uf": "SP",
}


def setup_function():
    SQLModel.metadata.create_all(engine)


def teardown_function():
    SQLModel.metadata.drop_all(engine)


def test_create_imovel():
    with Session(engine) as session:
        imovel = Imovel(nome="Edifício Central")
        session.add(imovel)
        session.commit()
        session.refresh(imovel)

    assert imovel.id is not None
    assert imovel.nome == "Edifício Central"
    assert imovel.gestor_id is None
    assert imovel.address_id is None


def test_create_imovel_with_gestor():
    with Session(engine) as session:
        gestor = Gestor(name="João Silva", cpf_cnpj=VALID_CPF)
        session.add(gestor)
        session.commit()
        session.refresh(gestor)
        gestor_id = gestor.id

        imovel = Imovel(nome="Edifício Central", gestor_id=gestor_id)
        session.add(imovel)
        session.commit()
        session.refresh(imovel)
        imovel_gestor_id = imovel.gestor_id

    assert imovel_gestor_id == gestor_id


def test_create_imovel_with_address():
    with Session(engine) as session:
        address = Address(**ADDRESS_DATA)
        session.add(address)
        session.commit()
        session.refresh(address)
        address_id = address.id

        imovel = Imovel(nome="Edifício Central", address_id=address_id)
        session.add(imovel)
        session.commit()
        session.refresh(imovel)
        imovel_address_id = imovel.address_id

    assert imovel_address_id == address_id


def test_imovel_nome_unique():
    with pytest.raises(IntegrityError):
        with Session(engine) as session:
            session.add(Imovel(nome="Edifício Central"))
            session.add(Imovel(nome="Edifício Central"))
            session.commit()


def test_read_imovel():
    with Session(engine) as session:
        imovel = Imovel(nome="Edifício Central")
        session.add(imovel)
        session.commit()
        imovel_id = imovel.id

    with Session(engine) as session:
        found = session.get(Imovel, imovel_id)

    assert found is not None
    assert found.nome == "Edifício Central"


def test_update_imovel():
    with Session(engine) as session:
        imovel = Imovel(nome="Edifício Central")
        session.add(imovel)
        session.commit()
        imovel_id = imovel.id

    with Session(engine) as session:
        imovel = session.get(Imovel, imovel_id)
        imovel.nome = "Edifício Norte"
        session.commit()
        session.refresh(imovel)

    assert imovel.nome == "Edifício Norte"


def test_delete_imovel():
    with Session(engine) as session:
        imovel = Imovel(nome="Edifício Central")
        session.add(imovel)
        session.commit()
        imovel_id = imovel.id

    with Session(engine) as session:
        imovel = session.get(Imovel, imovel_id)
        session.delete(imovel)
        session.commit()

    with Session(engine) as session:
        deleted = session.get(Imovel, imovel_id)

    assert deleted is None
