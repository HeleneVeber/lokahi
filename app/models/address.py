from sqlmodel import Field, SQLModel


class Address(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: int | None = Field(default=None, primary_key=True)
    cep: str
    logradouro: str
    numero: str
    complemento: str | None = None
    bairro: str
    cidade: str
    estado: str

    def format(self) -> str:
        return f"{self.logradouro}, {self.numero} — {self.bairro}, {self.cidade}"
