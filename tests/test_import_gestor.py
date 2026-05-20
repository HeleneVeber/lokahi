import io
import openpyxl
from unittest.mock import patch
from sqlmodel import SQLModel, Session, create_engine, select
from app.models import Gestor
from app.schemas import GestorData
from app.services import GestorService
from app.utils.import_utils import import_file


engine = create_engine("sqlite:///:memory:")


def setup_function():
    SQLModel.metadata.create_all(engine)


def teardown_function():
    SQLModel.metadata.drop_all(engine)


def test_import_valid_csv():
    csv_content = b"name,cpf_cnpj,phone\nJoao Silva,529.982.247-25,11999999999\nMaria Costa,295.379.955-93,11888888888"
    file = io.BytesIO(csv_content)
    file.name = "test.csv"

    with patch("app.services.gestor_service.get_session", return_value=Session(engine)):
        result = import_file(file, GestorService)

    assert result["imported"] == 2
    assert result["errors"] == []

    with Session(engine) as session:
        gestores = session.exec(select(Gestor)).all()
    assert len(gestores) == 2


def test_import_without_phone():
    csv_content = b"name,cpf_cnpj\nJoao Silva,529.982.247-25"
    file = io.BytesIO(csv_content)
    file.name = "test.csv"

    with patch("app.services.gestor_service.get_session", return_value=Session(engine)):
        result = import_file(file, GestorService)

    assert result["imported"] == 1
    assert result["errors"] == []

    with Session(engine) as session:
        gestor = session.exec(select(Gestor)).first()
    assert gestor.phone is None


def test_import_with_empty_phone_cell():
    csv_content = b"name,cpf_cnpj,phone\nJoao Silva,529.982.247-25,"
    file = io.BytesIO(csv_content)
    file.name = "test.csv"

    with patch("app.services.gestor_service.get_session", return_value=Session(engine)):
        result = import_file(file, GestorService)

    assert result["imported"] == 1

    with Session(engine) as session:
        gestor = session.exec(select(Gestor)).first()
    assert gestor.phone is None


def test_import_invalid_cpf():
    csv_content = b"name,cpf_cnpj,phone\nJoao Silva,123.456.789-00,11999999999\nMaria Costa,295.379.955-93,11888888888"
    file = io.BytesIO(csv_content)
    file.name = "test.csv"

    with patch("app.services.gestor_service.get_session", return_value=Session(engine)):
        result = import_file(file, GestorService)

    assert result["imported"] == 1
    assert len(result["errors"]) == 1
    assert result["errors"][0]["row"] == "Joao Silva"


def test_import_duplicate_cpf():
    csv_content = b"name,cpf_cnpj,phone\nJoao Silva,529.982.247-25,11999999999\nJoao Duplicado,529.982.247-25,11777777777"
    file = io.BytesIO(csv_content)
    file.name = "test.csv"

    with patch("app.services.gestor_service.get_session", return_value=Session(engine)):
        result = import_file(file, GestorService)

    assert result["imported"] == 1
    assert len(result["errors"]) == 1
    assert "já cadastrado" in result["errors"][0]["error"]


def test_import_missing_column():
    csv_content = b"name,phone\nJoao Silva,11999999999"
    file = io.BytesIO(csv_content)
    file.name = "test.csv"

    with patch("app.services.gestor_service.get_session", return_value=Session(engine)):
        result = import_file(file, GestorService)

    assert result["imported"] == 0
    assert len(result["errors"]) == 1
    assert "cpf_cnpj" in result["errors"][0]["error"]


def _make_xlsx(rows: list[dict]) -> io.BytesIO:
    wb = openpyxl.Workbook()
    ws = wb.active
    headers = list(rows[0].keys())
    ws.append(headers)
    for row in rows:
        ws.append([row.get(h) for h in headers])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    buf.name = "test.xlsx"
    return buf


def test_import_valid_xlsx():
    file = _make_xlsx(
        [
            {
                "name": "Joao Silva",
                "cpf_cnpj": "529.982.247-25",
                "phone": "11999999999",
            },
            {
                "name": "Maria Costa",
                "cpf_cnpj": "295.379.955-93",
                "phone": "11888888888",
            },
        ]
    )

    with patch("app.services.gestor_service.get_session", return_value=Session(engine)):
        result = import_file(file, GestorService)

    assert result["imported"] == 2
    assert result["errors"] == []


def test_import_xlsx_without_phone():
    file = _make_xlsx(
        [
            {"name": "Joao Silva", "cpf_cnpj": "529.982.247-25"},
        ]
    )

    with patch("app.services.gestor_service.get_session", return_value=Session(engine)):
        result = import_file(file, GestorService)

    assert result["imported"] == 1
    with Session(engine) as session:
        gestor = session.exec(select(Gestor)).first()
    assert gestor.phone is None


def test_import_unsupported_format():
    file = io.BytesIO(b"some content")
    file.name = "data.txt"

    with patch("app.services.gestor_service.get_session", return_value=Session(engine)):
        result = import_file(file, GestorService)

    assert result["imported"] == 0
    assert len(result["errors"]) == 1
    assert "suportado" in result["errors"][0]["error"]
