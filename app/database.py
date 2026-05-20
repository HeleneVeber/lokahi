"""Database configuration and session management."""

from pathlib import Path

import streamlit as st
from sqlmodel import Session, SQLModel, create_engine

DB_DIR = Path(__file__).parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)

DB_PATH = DB_DIR / "lokai.db"

engine = create_engine(f"sqlite:///{DB_PATH}")


@st.cache_resource
def _import_models():
    """Cache model imports to avoid SQLAlchemy re-registration on Streamlit reload."""
    from app.models import Address, Gestor, Imovel, Quarto
    return Address, Gestor, Imovel, Quarto


def get_models():
    """Get cached model classes. Use this instead of direct imports in pages."""
    Address, Gestor, Imovel, Quarto = _import_models()
    return {
        'Address': Address,
        'Gestor': Gestor,
        'Imovel': Imovel,
        'Quarto': Quarto,
    }


def create_db_and_tables() -> None:
    """Create all database tables if they don't exist."""
    # Import models only once via cache
    _import_models()
    
    # Create tables
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    """Get a new database session."""
    return Session(engine)
