from pydantic import BaseModel


class ViaCepData(BaseModel):
    cep: str
    logradouro: str
    bairro: str
    localidade: str
    uf: str
