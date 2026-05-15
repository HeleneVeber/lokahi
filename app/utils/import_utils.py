import pandas as pd


def import_file(file, model_class):
    df = _read_dataframe(file)
    if isinstance(df, dict):
        return df
    valid, errors = model_class.validate_rows(df)
    if not valid:
        return {"imported": 0, "errors": errors}
    imported, db_errors = model_class.save_many(valid)
    return {"imported": imported, "errors": errors + db_errors}


# Check file extension to determine how to read it
def _read_dataframe(file) -> pd.DataFrame | dict :
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


def parse_phone(value) -> str | None:
    if not pd.notna(value):
        return None
    try:
        return str(int(value))
    except (ValueError, TypeError):
        return str(value)
