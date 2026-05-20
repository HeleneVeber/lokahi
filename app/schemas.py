"""Data Transfer Objects (DTOs) for input validation and data exchange."""

from pydantic import BaseModel


class AddressData(BaseModel):
    """DTO for address creation/validation."""

    cep: str
    logradouro: str
    numero: str
    complemento: str | None = None
    bairro: str
    localidade: str
    uf: str


class GestorData(BaseModel):
    """DTO for gestor creation/validation."""

    cpf_cnpj: str
    name: str | None = None
    phone: str | None = None


class ImovelData(BaseModel):
    """DTO for imovel creation/validation."""

    nome_imovel: str
    cep: str
    numero: str
    complemento: str | None = None
    gestor_id: int | None = None
    cpf_gestor: str | None = None
    nome_gestor: str | None = None
    phone_gestor: str | None = None


class QuartoData(BaseModel):
    """DTO for quarto creation/validation."""

    numero: str
