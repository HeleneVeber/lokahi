from sqlmodel import Field, SQLModel


class Imovel(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: int | None = Field(default=None, primary_key=True)
    nome: str = Field(unique=True)
    gestor_id: int | None = Field(default=None, foreign_key="gestor.id")
    address_id: int | None = Field(default=None, foreign_key="address.id")
