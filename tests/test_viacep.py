import pytest
from unittest.mock import patch, Mock

from app.utils.viacep import fetch_address

VIACEP_RESPONSE = {
    "cep": "01310-100",
    "logradouro": "Avenida Paulista",
    "complemento": "",
    "bairro": "Bela Vista",
    "localidade": "São Paulo",
    "uf": "SP",
}


def _mock_response(json_data: dict, status_code: int = 200) -> Mock:
    mock = Mock()
    mock.status_code = status_code
    mock.json.return_value = json_data
    return mock


def test_fetch_address_valid_cep():
    with patch("app.utils.viacep.requests.get", return_value=_mock_response(VIACEP_RESPONSE)):
        result = fetch_address("01310-100")

    assert result["logradouro"] == "Avenida Paulista"
    assert result["localidade"] == "São Paulo"
    assert result["uf"] == "SP"


def test_fetch_address_strips_formatting():
    with patch("app.utils.viacep.requests.get", return_value=_mock_response(VIACEP_RESPONSE)) as mock_get:
        fetch_address("01310-100")
        called_url = mock_get.call_args[0][0]

    assert "01310100" in called_url


def test_fetch_address_invalid_cep():
    with patch("app.utils.viacep.requests.get", return_value=_mock_response({"erro": "true"})):
        with pytest.raises(ValueError, match="CEP não encontrado"):
            fetch_address("00000-000")


def test_fetch_address_http_error():
    with patch("app.utils.viacep.requests.get", return_value=_mock_response({}, status_code=400)):
        with pytest.raises(ValueError, match="CEP não encontrado"):
            fetch_address("00000-000")
