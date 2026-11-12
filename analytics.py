import pandas as pd

from fred_data import load_series


def year_over_year(series: pd.Series, periods_per_year: int) -> pd.Series:
    """Calculate year-over-year percent changes on a regular date index."""
    prior_year = series.shift(periods_per_year)
    return (series / prior_year - 1) * 100


def quarterly_comparison(gdp: pd.Series, core_cpi: pd.Series) -> pd.DataFrame:
    """Pair nominal GDP growth and Core CPI inflation by quarter."""
    monthly_groups = core_cpi.resample("QS-JAN")
    quarterly_cpi = monthly_groups.mean().where(monthly_groups.count().eq(3))

    return pd.concat(
        [
            year_over_year(gdp, 4).rename("nominal_gdp_growth_pct"),
            year_over_year(quarterly_cpi, 4).rename("core_cpi_inflation_pct"),
        ],
        axis=1,
        join="inner",
    ).dropna()


def recent_window(
    data: pd.Series | pd.DataFrame, years: int
) -> pd.Series | pd.DataFrame:
    """Keep observations from the latest date back through the cutoff."""
    if data.empty:
        return data

    cutoff = data.index[-1] - pd.DateOffset(years=years)
    return data.loc[cutoff:]


if __name__ == "__main__":
    gdp = load_series("GDP")
    core_cpi = load_series("CPILFESL")

    latest_quarter = gdp.last_valid_index()
    gdp_growth = year_over_year(gdp, 4).loc[latest_quarter]

    latest_month = core_cpi.last_valid_index()
    inflation_rates = year_over_year(core_cpi, 12)
    latest_rate = inflation_rates.loc[latest_month]

    print(f"Nominal GDP growth ({latest_quarter:%Y-%m}): {gdp_growth:.2f}% YoY")

    if pd.notna(latest_rate):
        print(f"Core CPI inflation ({latest_month:%Y-%m}): {latest_rate:.2f}% YoY")
    else:
        prior_month = latest_month - pd.DateOffset(years=1)
        print(
            f"Core CPI inflation ({latest_month:%Y-%m}): unavailable "
            f"(missing {prior_month:%Y-%m} index)."
        )

        latest_available = inflation_rates.last_valid_index()
        if latest_available is not None:
            available_rate = inflation_rates.loc[latest_available]
            print(f"Latest calculable rate ({latest_available:%Y-%m}): {available_rate:.2f}% YoY")

    comparison = recent_window(quarterly_comparison(gdp, core_cpi), years=10)

    if len(comparison) >= 2:
        correlation = comparison["nominal_gdp_growth_pct"].corr(
            comparison["core_cpi_inflation_pct"]
        )
        start, end = comparison.index[[0, -1]].to_period("Q")
        print(f"\nComparison window: {start} through {end}")
        print(f"Paired quarters: {len(comparison)}")
        print(f"Pearson correlation: {correlation:.3f}")
        print(comparison.tail().round(2).to_string())
    else:
        print("Too few paired quarters to calculate correlation.")