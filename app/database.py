from pathlib import Path
from sqlmodel import Session, SQLModel, create_engine

DB_DIR = Path("data")
DB_DIR.mkdir(exist_ok=True)

DB_PATH = DB_DIR / "lokai.db"

engine = create_engine(f"sqlite:///{DB_PATH}")

def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)

def get_session() -> Session:
    return Session(engine)

