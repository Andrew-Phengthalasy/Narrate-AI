import io
import pandas as pd
try:
    from .preprocessor import compute_statistics  # package import (local dev)
except ImportError:
    from preprocessor import compute_statistics   # flat import (Vercel)


# Cap rows read to avoid exhausting lambda memory on huge CSVs.
# Statistics are computed on this sample; shape.rows reflects the true count.
_MAX_ROWS = 5_000


def parse_csv(content: bytes) -> dict:
    """Parse CSV bytes into a structured data dict with statistics."""
    # First pass: get true row count — count non-empty lines minus the header.
    # Using splitlines() avoids iterating BytesIO chunks as arbitrary byte spans.
    total_rows = max(sum(1 for ln in content.splitlines() if ln.strip()) - 1, 0)

    df = pd.read_csv(io.BytesIO(content), nrows=_MAX_ROWS)
    df.dropna(how="all", inplace=True)

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    categorical_cols = df.select_dtypes(include="object").columns.tolist()
    date_cols = _detect_date_columns(df, categorical_cols)

    return {
        "source_type": "csv",
        "shape": {"rows": total_rows, "columns": len(df.columns)},
        "sampled_rows": len(df),
        "columns": df.columns.tolist(),
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "date_columns": date_cols,
        "sample_rows": _serialisable_rows(df.head(5)),
        "statistics": compute_statistics(df, numeric_cols, date_cols),
    }


def _serialisable_rows(df: pd.DataFrame) -> list[dict]:
    """Convert a DataFrame slice to plain Python dicts safe for JSON serialisation.

    Fills NaN with None and casts numpy scalar types (int64, float64, etc.) to
    their native Python equivalents so FastAPI's JSON encoder never chokes.
    """
    rows = []
    for record in df.to_dict(orient="records"):
        rows.append({
            k: (None if (isinstance(v, float) and v != v) else  # NaN check
                v.item() if hasattr(v, "item") else             # numpy scalars
                str(v) if hasattr(v, "isoformat") else          # Timestamps
                v)
            for k, v in record.items()
        })
    return rows


def _detect_date_columns(df: pd.DataFrame, candidates: list[str]) -> list[str]:
    date_cols = []
    for col in candidates:
        try:
            series = df[col].dropna()
            # Require at least 3 non-null values to avoid false positives
            if len(series) < 3:
                continue
            parsed = pd.to_datetime(series, errors="coerce")
            if parsed.notna().mean() > 0.8:
                date_cols.append(col)
        except Exception:
            pass
    return date_cols
