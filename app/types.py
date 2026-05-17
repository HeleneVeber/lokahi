from pydantic import BaseModel


class ViaCepData(BaseModel):
    cep: str
    logradouro: str
    bairro: str
    localidade: str
    uf: str


class AddressData(ViaCepData):
    numero: str
    complemento: str | None = None
