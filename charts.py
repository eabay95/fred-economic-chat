from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

from analytics import quarterly_comparison, recent_window, year_over_year
from fred_data import load_series


def line_chart(title: str, y_label: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        title=title,
        xaxis_title="Observation date",
        yaxis_title=y_label,
        template="plotly_white",
        hovermode="x unified",
    )
    return fig


def add_series(fig: go.Figure, data: pd.Series, label: str) -> None:
    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data,
            name=label,
            mode="lines",
            connectgaps=False,
        )
    )


def gdp_chart(gdp: pd.Series, years: int = 10) -> go.Figure:
    fig = line_chart(
        "U.S. nominal GDP",
        "Billions of dollars, seasonally adjusted annual rate",
    )
    add_series(fig, recent_window(gdp, years), "Nominal GDP")
    return fig


def inflation_chart(core_cpi: pd.Series, years: int = 5) -> go.Figure:
    fig = line_chart("U.S. Core CPI inflation", "Year-over-year change (%)")
    inflation = year_over_year(core_cpi, 12)
    add_series(fig, recent_window(inflation, years), "Core CPI inflation")
    return fig


def comparison_chart(paired_quarters: pd.DataFrame) -> go.Figure:
    fig = line_chart(
        "Nominal GDP growth and Core CPI inflation",
        "Year-over-year change (%)",
    )

    # Restore omitted quarters as empty rows so Plotly shows a visible gap.
    plot_data = paired_quarters.asfreq("QS-JAN")

    add_series(fig, plot_data["nominal_gdp_growth_pct"], "Nominal GDP growth")
    add_series(fig, plot_data["core_cpi_inflation_pct"], "Core CPI inflation")
    return fig


if __name__ == "__main__":
    gdp = load_series("GDP")
    core_cpi = load_series("CPILFESL")
    paired_quarters = recent_window(quarterly_comparison(gdp, core_cpi), 10)

    output_dir = Path("docs/figures")
    output_dir.mkdir(parents=True, exist_ok=True)

    charts = {
        "nominal_gdp.html": gdp_chart(gdp),
        "core_cpi_inflation.html": inflation_chart(core_cpi),
        "gdp_vs_core_cpi.html": comparison_chart(paired_quarters),
    }

    for filename, figure in charts.items():
        path = output_dir / filename
        figure.write_html(path, include_plotlyjs=True)
        print(f"Saved {path}")