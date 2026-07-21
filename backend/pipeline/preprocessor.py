import math

import pandas as pd


def compute_statistics(df: pd.DataFrame, numeric_cols: list[str]) -> dict:
    """Compute descriptive stats, outliers, and trend direction per numeric column."""
    stats = {}

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

        # Simple trend: compare first-half mean vs second-half mean
        mid = len(series) // 2
        trend = "stable"
        if mid > 0:
            first_half_mean = series.iloc[:mid].mean()
            second_half_mean = series.iloc[mid:].mean()
            # Guard against NaN means (e.g. half-series with all-NaN values)
            # and zero division before computing percentage change.
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

        stats[col] = {
            "mean": round(float(series.mean()), 4),
            "median": round(float(series.median()), 4),
            "std": round(float(series.std()), 4),
            "min": round(float(series.min()), 4),
            "max": round(float(series.max()), 4),
            "outlier_count": int(len(outliers)),
            "outlier_values": [round(v, 4) for v in outliers.head(5).tolist()],
            "trend": trend,
        }

    return stats
