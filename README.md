# Lokahi

Coliving management application for the Brazilian market.

**Current phase:** Streamlit MVP dashboard for data testing and analysis.
**Future phase:** dedicated web application with REST API and frontend.

---

## Prerequisites

- Python 3.12.9
- [uv](https://docs.astral.sh/uv/) — Python package manager

---

## Installation

Clone the repository:
```
git clone git@github.com:HeleneVeber/lokahi.git
```

In the repository, install dependencies:
```
uv sync
```

---

## Run the app

```bash
uv run streamlit run app/main.py
```

The app will open automatically at `http://localhost:8501`.

---

## Project structure

```text
lokahi/
├── docs/
│   ├── overview_pt.md      ← project overview and security requirements (PT)
│   └── ADRs/               ← architecture decision records
├── data/                   ← SQLite database files (local only, not committed)
├── app/
│   ├── main.py             ← Streamlit entry point
│   ├── models/             ← SQLModel data models
│   ├── pages/              ← Streamlit pages
│   └── utils/              ← CSV/Excel import helpers
├── pyproject.toml
└── pyrightconfig.json
```

---

## Documentation

- [Project overview (PT)](docs/overview_pt.md)
- [ADR 001 — Streamlit](docs/ADRs/001_streamlit.md)
- [ADR 002 — Database isolation strategy](docs/ADRs/002_database_strategy.md)
- [ADR 003 — SQLModel as ORM](docs/ADRs/003_sqlmodel.md)
