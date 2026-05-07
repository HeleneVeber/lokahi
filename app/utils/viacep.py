import requests


def fetch_address(cep: str) -> dict:
    cep = cep.replace("-", "").replace(" ", "")
    url = f"https://viacep.com.br/ws/{cep}/json/"
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError(f"CEP não encontrado: {cep}")
    data = response.json()
    if "erro" in data:
        raise ValueError(f"CEP não encontrado: {cep}")
    return data
