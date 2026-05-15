from sqlmodel import SQLModel, Session, create_engine, select

from app.models.address import Address
from app.types import AddressData

engine = create_engine("sqlite:///:memory:")

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


def test_create_address():
    with Session(engine) as session:
        address = Address(**ADDRESS_DATA)
        session.add(address)
        session.commit()
        session.refresh(address)

    assert address.id is not None
    assert address.logradouro == "Avenida Paulista"
    assert address.complemento is None


def test_create_address_with_complemento():
    with Session(engine) as session:
        address = Address(**ADDRESS_DATA, complemento="Apto 42")
        session.add(address)
        session.commit()
        session.refresh(address)

    assert address.complemento == "Apto 42"


def test_read_address():
    with Session(engine) as session:
        address = Address(**ADDRESS_DATA)
        session.add(address)
        session.commit()
        address_id = address.id

    with Session(engine) as session:
        found = session.get(Address, address_id)

    assert found is not None
    assert found.cep == "01310-100"
    assert found.localidade == "São Paulo"


def test_update_address():
    with Session(engine) as session:
        address = Address(**ADDRESS_DATA)
        session.add(address)
        session.commit()
        address_id = address.id

    with Session(engine) as session:
        address = session.get(Address, address_id)
        address.numero = "2000"
        session.commit()
        session.refresh(address)

    assert address.numero == "2000"


def test_delete_address():
    with Session(engine) as session:
        address = Address(**ADDRESS_DATA)
        session.add(address)
        session.commit()
        address_id = address.id

    with Session(engine) as session:
        address = session.get(Address, address_id)
        session.delete(address)
        session.commit()

    with Session(engine) as session:
        deleted = session.get(Address, address_id)

    assert deleted is None


def test_get_or_create_creates_new():
    with Session(engine) as session:
        address = Address.get_or_create(session, AddressData(**{**ADDRESS_DATA, "numero": "100"}))
        session.commit()
        address_id = address.id

    with Session(engine) as session:
        all_addresses = session.exec(select(Address)).all()
    assert len(all_addresses) == 1
    assert all_addresses[0].id == address_id


def test_get_or_create_returns_existing():
    with Session(engine) as session:
        existing = Address(**ADDRESS_DATA)
        session.add(existing)
        session.commit()
        existing_id = existing.id

    with Session(engine) as session:
        address = Address.get_or_create(session, AddressData(**ADDRESS_DATA))
        session.commit()
        address_id = address.id

    with Session(engine) as session:
        all_addresses = session.exec(select(Address)).all()
    assert len(all_addresses) == 1
    assert address_id == existing_id


def test_get_or_create_same_cep_different_numero():
    with Session(engine) as session:
        Address.get_or_create(session, AddressData(**{**ADDRESS_DATA, "numero": "100"}))
        session.commit()

    with Session(engine) as session:
        Address.get_or_create(session, AddressData(**{**ADDRESS_DATA, "numero": "200"}))
        session.commit()

    with Session(engine) as session:
        all_addresses = session.exec(select(Address)).all()
    assert len(all_addresses) == 2


def test_get_or_create_with_complemento():
    with Session(engine) as session:
        address = Address.get_or_create(session, AddressData(**{**ADDRESS_DATA, "numero": "100", "complemento": "Apto 1"}))
        session.commit()
        complemento = address.complemento

    assert complemento == "Apto 1"
