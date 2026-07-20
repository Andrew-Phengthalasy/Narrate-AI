import io
import pandas as pd
from .preprocessor import compute_statistics


def parse_csv(content: bytes) -> dict:
    """Parse CSV bytes into a structured data dict with statistics."""
    df = pd.read_csv(io.BytesIO(content))
    df.dropna(how="all", inplace=True)

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    categorical_cols = df.select_dtypes(include="object").columns.tolist()
    date_cols = _detect_date_columns(df, categorical_cols)

    return {
        "source_type": "csv",
        "shape": {"rows": len(df), "columns": len(df.columns)},
        "columns": df.columns.tolist(),
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "date_columns": date_cols,
        "sample_rows": df.head(5).fillna("").to_dict(orient="records"),
        "statistics": compute_statistics(df, numeric_cols),
    }


def _detect_date_columns(df: pd.DataFrame, candidates: list[str]) -> list[str]:
    date_cols = []
    for col in candidates:
        try:
            parsed = pd.to_datetime(df[col], errors="coerce")
            if parsed.notna().mean() > 0.8:
                date_cols.append(col)
        except Exception:
            pass
    return date_cols
