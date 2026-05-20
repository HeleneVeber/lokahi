import io
import pandas as pd
from unittest.mock import patch
from sqlmodel import SQLModel, Session, create_engine, select

from app.models import Address, Gestor, Imovel
from app.schemas import ImovelData
from app.services import ImovelService
from app.types import ViaCepData
from app.utils.import_utils import import_file

engine = create_engine("sqlite:///:memory:")

VALID_CPF = "529.982.247-25"

VIACEP_RESPONSE = ViaCepData(
    cep="01310-100",
    logradouro="Avenida Paulista",
    bairro="Bela Vista",
    localidade="São Paulo",
    uf="SP",
)


def setup_function():
    SQLModel.metadata.create_all(engine)


def teardown_function():
    SQLModel.metadata.drop_all(engine)


def _make_csv(rows: list[dict]) -> io.BytesIO:
    df = pd.DataFrame(rows)
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    buf.name = "test.csv"
    return buf


# --- validate_rows (sans DB, sans fetch_address) ---

def test_validate_rows_valid():
    df = pd.DataFrame([{"nome_imovel": "Ed Central", "cep": "01310-100", "numero": "100"}])
    valid, errors = ImovelService.validate_rows(df)
    assert len(valid) == 1
    assert errors == []
    assert valid[0].nome_imovel == "Ed Central"
    assert valid[0].cep == "01310-100"


def test_validate_rows_missing_nome_imovel():
    df = pd.DataFrame([{"cep": "01310-100", "numero": "100"}])
    valid, errors = ImovelService.validate_rows(df)
    assert valid == []
    assert "nome_imovel" in errors[0]["error"]


def test_validate_rows_missing_cep():
    df = pd.DataFrame([{"nome_imovel": "Ed Central", "numero": "100"}])
    valid, errors = ImovelService.validate_rows(df)
    assert valid == []
    assert "cep" in errors[0]["error"]


def test_validate_rows_missing_numero():
    df = pd.DataFrame([{"nome_imovel": "Ed Central", "cep": "01310-100"}])
    valid, errors = ImovelService.validate_rows(df)
    assert valid == []
    assert "numero" in errors[0]["error"]


def test_validate_rows_optional_fields_absent():
    df = pd.DataFrame([{"nome_imovel": "Ed Central", "cep": "01310-100", "numero": "100"}])
    valid, errors = ImovelService.validate_rows(df)
    assert valid[0].complemento is None
    assert valid[0].cpf_gestor is None
    assert valid[0].nome_gestor is None
    assert valid[0].phone_gestor is None


# --- save_many via import_file (fetch_address + get_session mockés) ---

def test_import_valid_without_gestor():
    file = _make_csv([{"nome_imovel": "Ed Central", "cep": "01310-100", "numero": "100"}])
    with patch("app.services.imovel_service.fetch_address", return_value=VIACEP_RESPONSE), \
         patch("app.services.imovel_service.get_session", return_value=Session(engine)):
        result = import_file(file, ImovelService)
    assert result["imported"] == 1
    assert result["errors"] == []
    with Session(engine) as session:
        imovel = session.exec(select(Imovel)).first()
    assert imovel.nome == "Ed Central"
    assert imovel.gestor_id is None


def test_import_invalid_cep():
    file = _make_csv([{"nome_imovel": "Ed Central", "cep": "00000-000", "numero": "100"}])
    with patch("app.services.imovel_service.fetch_address", side_effect=ValueError("CEP não encontrado")), \
         patch("app.services.imovel_service.get_session", return_value=Session(engine)):
        result = import_file(file, ImovelService)
    assert result["imported"] == 0
    assert len(result["errors"]) == 1
    assert "CEP" in result["errors"][0]["error"]


def test_import_links_existing_gestor():
    with Session(engine) as session:
        gestor = Gestor(name="João Silva", cpf_cnpj=VALID_CPF)
        session.add(gestor)
        session.commit()
        gestor_id = gestor.id

    file = _make_csv([{"nome_imovel": "Ed Central", "cep": "01310-100", "numero": "100", "cpf_gestor": VALID_CPF}])
    with patch("app.services.imovel_service.fetch_address", return_value=VIACEP_RESPONSE), \
         patch("app.services.imovel_service.get_session", return_value=Session(engine)):
        result = import_file(file, ImovelService)
    assert result["imported"] == 1
    with Session(engine) as session:
        imovel = session.exec(select(Imovel)).first()
    assert imovel.gestor_id == gestor_id


def test_import_creates_new_gestor():
    file = _make_csv([{
        "nome_imovel": "Ed Central", "cep": "01310-100", "numero": "100",
        "cpf_gestor": VALID_CPF, "nome_gestor": "João Silva",
    }])
    with patch("app.services.imovel_service.fetch_address", return_value=VIACEP_RESPONSE), \
         patch("app.services.imovel_service.get_session", return_value=Session(engine)):
        result = import_file(file, ImovelService)
    assert result["imported"] == 1
    with Session(engine) as session:
        gestor = session.exec(select(Gestor)).first()
    assert gestor.name == "João Silva"


def test_import_error_new_gestor_without_nome():
    file = _make_csv([{"nome_imovel": "Ed Central", "cep": "01310-100", "numero": "100", "cpf_gestor": VALID_CPF}])
    with patch("app.services.imovel_service.fetch_address", return_value=VIACEP_RESPONSE), \
         patch("app.services.imovel_service.get_session", return_value=Session(engine)):
        result = import_file(file, ImovelService)
    assert result["imported"] == 0
    assert result["errors"][0]["row"] == "Ed Central"


def test_import_duplicate_nome_imovel():
    file = _make_csv([
        {"nome_imovel": "Ed Central", "cep": "01310-100", "numero": "100"},
        {"nome_imovel": "Ed Central", "cep": "01310-100", "numero": "200"},
    ])
    with patch("app.services.imovel_service.fetch_address", return_value=VIACEP_RESPONSE), \
         patch("app.services.imovel_service.get_session", return_value=Session(engine)):
        result = import_file(file, ImovelService)
    assert result["imported"] == 1
    assert len(result["errors"]) == 1


def test_import_duplicate_address():
    file = _make_csv([
        {"nome_imovel": "Ed Central", "cep": "01310-100", "numero": "100"},
        {"nome_imovel": "Ed Norte", "cep": "01310-100", "numero": "100"},
    ])
    with patch("app.services.imovel_service.fetch_address", return_value=VIACEP_RESPONSE), \
         patch("app.services.imovel_service.get_session", return_value=Session(engine)):
        result = import_file(file, ImovelService)
    assert result["imported"] == 1
    assert len(result["errors"]) == 1


def test_import_missing_column():
    file = _make_csv([{"nome_imovel": "Ed Central", "numero": "100"}])
    result = import_file(file, ImovelService)
    assert result["imported"] == 0
    assert "cep" in result["errors"][0]["error"]
