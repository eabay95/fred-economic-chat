from io import StringIO

import pandas as pd
import requests

FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
FREQUENCIES = {
    "GDP": "QS-JAN",  # January, April, July, October
    "CPILFESL": "MS",  # First day of each month
}


def load_series(series_id: str) -> pd.Series:
    """Fetch one FRED series at its original observation frequency."""
    if series_id not in FREQUENCIES:
        raise ValueError(f"Unsupported FRED series: {series_id}")

    response = requests.get(
        FRED_CSV_URL,
        params={"id": series_id},
        timeout=15,
    )
    response.raise_for_status()

    frame = pd.read_csv(StringIO(response.text), na_values=["."])
    frame = frame.rename(columns={"DATE": "observation_date"})

    if not {"observation_date", series_id}.issubset(frame.columns):
        raise ValueError(f"Unexpected CSV columns for {series_id}")

    dates = pd.DatetimeIndex(pd.to_datetime(frame["observation_date"]))
    values = pd.to_numeric(frame[series_id]).to_numpy()
    series = pd.Series(values, index=dates, name=series_id).sort_index()

    if not series.notna().any():
        raise ValueError(f"FRED returned no usable values for {series_id}")

    return series.asfreq(FREQUENCIES[series_id])


if __name__ == "__main__":
    for series_id in FREQUENCIES:
        observations = load_series(series_id)
        latest_date = observations.last_valid_index()
        latest_value = observations.loc[latest_date]

        print(f"{series_id} | {latest_date:%Y-%m-%d} | {latest_value:,.3f}")