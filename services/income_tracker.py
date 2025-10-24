import pandas as pd

def summarize_earnings_by_source(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    g = df.groupby("source", as_index=False)["amount"].sum().sort_values("amount", ascending=False)
    return g

def earnings_timeseries(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    d = df.copy()
    d["date"] = d["ts"].dt.date
    ts = d.groupby("date", as_index=False)["amount"].sum()
    return ts
