import math

import pandas as pd


def compute_statistics(df: pd.DataFrame, numeric_cols: list[str], date_cols: list[str] | None = None) -> dict:
    """Compute descriptive stats, outliers, and trend direction per numeric column.

    If date_cols is provided and non-empty, the DataFrame is sorted by the first
    detected date column before computing trends so direction reflects chronological
    order rather than raw row order.
    """
    stats = {}

    # Sort by the first date column so trend direction is chronologically meaningful
    if date_cols:
        try:
            df = df.copy()
            df[date_cols[0]] = pd.to_datetime(df[date_cols[0]], errors="coerce")
            df = df.sort_values(date_cols[0], na_position="last")
        except Exception:
            pass  # sorting is best-effort; fall back to row order

    for col in numeric_cols:
        series = df[col].dropna()
        if series.empty:
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower_fence = q1 - 1.5 * iqr
        upper_fence = q3 + 1.5 * iqr
        outliers = series[(series < lower_fence) | (series > upper_fence)]

        # Trend: compare first-half mean vs second-half mean
        mid = len(series) // 2
        trend = "stable"
        if mid > 0:
            first_half_mean = series.iloc[:mid].mean()
            second_half_mean = series.iloc[mid:].mean()
            # Guard against NaN means and zero division
            if (
                first_half_mean != 0
                and not math.isnan(first_half_mean)
                and not math.isnan(second_half_mean)
            ):
                pct_change = (second_half_mean - first_half_mean) / abs(first_half_mean)
                if pct_change > 0.05:
                    trend = "increasing"
                elif pct_change < -0.05:
                    trend = "decreasing"

        std_val = series.std()
        stats[col] = {
            "mean": round(float(series.mean()), 4),
            "median": round(float(series.median()), 4),
            # std is NaN for single-value series (ddof=1); emit None for valid JSON
            "std": round(float(std_val), 4) if not math.isnan(std_val) else None,
            "min": round(float(series.min()), 4),
            "max": round(float(series.max()), 4),
            "outlier_count": int(len(outliers)),
            "outlier_values": [round(v, 4) for v in outliers.head(5).tolist()],
            "trend": trend,
        }

    return stats
