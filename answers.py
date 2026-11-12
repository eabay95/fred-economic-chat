from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go
from openai import OpenAI

from analytics import quarterly_comparison, recent_window, year_over_year
from assistant import AnalysisRequest, interpret_question
from charts import comparison_chart, gdp_chart, inflation_chart
from fred_data import load_series


@dataclass
class Answer:
    text: str
    chart: go.Figure | None = None
    sources: tuple[str, ...] = ()


def quarter_label(date: pd.Timestamp) -> str:
    return f"Q{date.quarter} {date.year}"


def latest_inflation_text(rates: pd.Series, month: pd.Timestamp) -> str:
    rate = rates.loc[month]
    if pd.notna(rate):
        return f"Core CPI inflation was **{rate:.2f}% YoY** in {month:%B %Y}."

    prior_month = month - pd.DateOffset(years=1)
    text = (
        f"Core CPI inflation for **{month:%B %Y}** is unavailable "
        f"because the {prior_month:%B %Y} index is missing."
    )

    last_available = rates.last_valid_index()
    if last_available is not None:
        text += (
            f" The latest calculable rate was **{rates.loc[last_available]:.2f}% YoY** "
            f"in {last_available:%B %Y}."
        )
    return text


def gdp_trend_text(gdp: pd.Series, years: int) -> str:
    window = recent_window(gdp, years).dropna()
    start, end = window.index[0], window.index[-1]
    first, last = window.iloc[0], window.iloc[-1]
    change = (last / first - 1) * 100
    return (
        f"From {quarter_label(start)} to {quarter_label(end)}, nominal GDP "
        f"changed from ${first:,.3f} billion to ${last:,.3f} billion "
        f"at a seasonally adjusted annual rate (**{change:+.2f}% total**)."
    )


def inflation_trend_text(rates: pd.Series, years: int) -> str:
    window = recent_window(rates, years).dropna()
    if window.empty:
        return "No year-over-year Core CPI rates are available in this window."

    start, end = window.index[0], window.index[-1]
    peak, trough = window.idxmax(), window.idxmin()
    return (
        f"Core CPI inflation went from **{window.iloc[0]:.2f}% YoY** in "
        f"{start:%B %Y} to **{window.iloc[-1]:.2f}% YoY** in {end:%B %Y}. "
        f"It peaked at {window.loc[peak]:.2f}% in {peak:%B %Y} and "
        f"reached a low of {window.loc[trough]:.2f}% in {trough:%B %Y}."
    )


def comparison_text(pairs: pd.DataFrame) -> str:
    if pairs.empty:
        return "No complete paired quarters are available in this window."

    start, end = pairs.index[0], pairs.index[-1]
    window = (
        f"{quarter_label(start)} through {quarter_label(end)} "
        f"({len(pairs)} paired quarters)"
    )
    if len(pairs) < 2 or pairs.nunique().min() < 2:
        return f"Pearson correlation is undefined for {window}."

    gdp_growth = pairs["nominal_gdp_growth_pct"]
    inflation = pairs["core_cpi_inflation_pct"]
    correlation = gdp_growth.corr(inflation)
    return (
        f"The Pearson correlation between nominal GDP growth and Core CPI "
        f"inflation was **{correlation:.3f}** from {window}. "
        "This measures how the two year-over-year rates moved together "
        "over the selected quarters."
    )


def answer_request(request: AnalysisRequest, load=load_series) -> Answer:
    intent = request.intent

    if intent == "clarify":
        return Answer(
            request.clarification or "Which GDP or Core CPI measure should I use?"
        )

    if intent in {"latest_gdp", "latest_gdp_growth", "gdp_trend"}:
        gdp = load("GDP")
        quarter = gdp.last_valid_index()
        gdp = gdp.loc[:quarter]

        if intent == "latest_gdp":
            text = (
                f"Nominal U.S. GDP was **${gdp.loc[quarter]:,.3f} billion** "
                f"in **{quarter_label(quarter)}**, at a seasonally adjusted annual rate."
            )
            return Answer(text, sources=("GDP",))

        if intent == "latest_gdp_growth":
            rate = year_over_year(gdp, 4).loc[quarter]
            result = f"**{rate:.2f}% YoY**" if pd.notna(rate) else "unavailable"
            return Answer(
                f"Nominal GDP growth was {result} in {quarter_label(quarter)}.",
                sources=("GDP",),
            )

        years = request.years or 10
        chart = gdp_chart(gdp, years) if request.show_chart else None
        return Answer(gdp_trend_text(gdp, years), chart, ("GDP",))

    core_cpi = load("CPILFESL")
    month = core_cpi.last_valid_index()
    core_cpi = core_cpi.loc[:month]
    rates = year_over_year(core_cpi, 12)

    if intent == "latest_core_cpi_inflation":
        return Answer(latest_inflation_text(rates, month), sources=("CPILFESL",))

    if intent == "core_cpi_trend":
        years = request.years or 5
        chart = inflation_chart(core_cpi, years) if request.show_chart else None
        return Answer(inflation_trend_text(rates, years), chart, ("CPILFESL",))

    gdp = load("GDP")
    gdp = gdp.loc[:gdp.last_valid_index()]
    years = request.years or 10
    pairs = recent_window(quarterly_comparison(gdp, core_cpi), years)
    text = comparison_text(pairs)

    if intent == "summarize":
        text = "\n\n".join(
            [gdp_trend_text(gdp, years), inflation_trend_text(rates, years), text]
        )

    chart = comparison_chart(pairs) if request.show_chart and not pairs.empty else None
    return Answer(text, chart, ("GDP", "CPILFESL"))


if __name__ == "__main__":
    client = OpenAI()
    previous_request = None

    while question := input("\nAsk a FRED question (Enter to exit): ").strip():
        request = interpret_question(client, question, previous_request)
        answer = answer_request(request)
        print(answer.text)

        for series in answer.sources:
            print(f"Source: https://fred.stlouisfed.org/series/{series}")

        if answer.chart is not None:
            answer.chart.show()

        if request.intent != "clarify":
            previous_request = request