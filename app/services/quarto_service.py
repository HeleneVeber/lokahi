"""Service for Quarto business logic.

⚠️ IMPORTANT - Streamlit Hot-Reload Pattern:
All imports from app.models MUST be done inside methods (lazy imports)
to avoid SQLAlchemy double-registration during Streamlit hot-reload.
See CLAUDE.md section "Pattern Streamlit Hot-Reload" for details.
"""


class QuartoService:
    """Handles business logic for Quarto operations."""

    # For now, Quarto service is minimal
    # Business logic will be added as needed in future user stories
    # When adding methods, use lazy imports:
    #   def method(self):
    #       from app.models import Quarto  # Import here, not at top
    pass
