from typing import Optional
from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel, select



class AddressData(BaseModel):
    cep: str
    logradouro: str
    numero: str
    complemento: str | None = None
    bairro: str
    localidade: str
    uf: str

class Address(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: int | None = Field(default=None, primary_key=True)
    cep: str
    logradouro: str
    numero: str
    complemento: str | None = None
    bairro: str
    localidade: str
    uf: str

    imovel: Optional["Imovel"] = Relationship(back_populates="address")

    def format(self) -> str:
        complemento = f", {self.complemento}" if self.complemento else ""
        return f"{self.logradouro}, {self.numero} {complemento} — {self.bairro}, {self.localidade} - {self.uf}"

    @classmethod
    def get_or_create(cls, session, address: AddressData) -> "Address":
        existing_address = session.exec(
            select(cls).where(
                cls.cep == address.cep,
                cls.numero == address.numero,
                cls.complemento == address.complemento,
            )
        ).first()

        if existing_address:
            return existing_address

        new_address = cls(**address.model_dump())
        session.add(new_address)
        session.flush()
        return new_address
