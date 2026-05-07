import pandas as pd
from sqlalchemy.exc import IntegrityError
from app.database import get_session
from app.models.gestor import Gestor


def import_gestores(file) -> dict:
    result = _read_dataframe(file)
    if isinstance(result, dict):  # erreur format
        return result

    validated = _validate_rows(result)
    if isinstance(validated, dict):
        return validated
    valid, errors = validated

    imported = 0

    with get_session() as session:
        for gestor in valid:
            try:
                with session.begin_nested():
                    session.add(gestor)
                    session.flush()
                imported += 1
            except IntegrityError:
                errors.append({"row": gestor.name, "error": "CPF/CNPJ já cadastrado"})
        session.commit()

    return {"imported": imported, "errors": errors}


def _parse_phone(value) -> str | None:
    if not pd.notna(value):
        return None
    try:
        return str(int(value))
    except (ValueError, TypeError):
        return str(value)


# Check file extension to determine how to read it
def _read_dataframe(file):
    name = getattr(file, "name", "")
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""

    if ext == "csv":
        return pd.read_csv(file)
    elif ext in {"xls", "xlsx"}:
        return pd.read_excel(file)
    else:
        return {
            "imported": 0,
            "errors": [
                {"row": None, "error": f"Formato não suportado: use CSV, XLS ou XLSX."}
            ],
        }


# Check if the file are all required columns and if the values are valid (e.g. cpf_cnpj format, phone number)
def _validate_rows(dataframe):
    required = {
        key for key, field in Gestor.model_fields.items() if field.is_required()
    }
    missing = required - set(dataframe.columns)

    if missing:
        return {
            "imported": 0,
            "errors": [
                {
                    "row": None,
                    "error": f"Coluna obrigatória ausente: {', '.join(missing)}",
                }
            ],
        }

    valid, errors = [], []
    for _, row in dataframe.iterrows():
        try:
            valid.append(
                Gestor(
                    name=str(row["name"]),
                    cpf_cnpj=str(row["cpf_cnpj"]),
                    phone=_parse_phone(row.get("phone")),
                )
            )
        except ValueError as e:
            errors.append({"row": row["name"], "error": str(e)})

    return valid, errors
