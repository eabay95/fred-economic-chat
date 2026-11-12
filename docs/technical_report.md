# FRED Economic Chat Assistant

## Objective

The application lets users ask natural-language questions about U.S.
nominal GDP and Core CPI inflation. It retrieves observations from FRED,
calculates economic indicators, and displays answers and interactive
charts in a Streamlit conversation.

## Implementation

Streamlit captures the question and passes it to an OpenAI model. The
model returns a structured request with an analysis type, a time window,
and a chart preference. Python validates the request, retrieves the
required FRED series, and computes the results with pandas. Plotly renders
the charts. Streamlit stores the previous successful request so a user
can change the time window without restating the comparison.

The app uses quarterly nominal GDP in billions of dollars at a
seasonally adjusted annual rate and the monthly seasonally adjusted
Core CPI index. It computes year-over-year changes by comparing each
observation with the corresponding period one year earlier. For the
quarterly comparison, it averages Core CPI index values within complete
quarters, computes year-over-year changes from those averages, and
aligns the resulting rates with nominal GDP growth. It calculates
Pearson correlation on the shared quarters.

## Findings

| Measure | Result from the recorded run |
|---|---|
| Latest nominal GDP | $33,010.036 billion in Q3 2026 at a seasonally adjusted annual rate |
| Ten-year change in nominal GDP | +74.72% from Q3 2016 to Q3 2026 |
| Latest calculable monthly Core CPI inflation | 2.57% YoY in September 2026 |
| Core CPI inflation peak in the ten-year summary | 6.62% YoY in September 2022 |
| Ten-year GDP growth and Core CPI correlation | 0.681 across 40 paired quarters |
| Five-year GDP growth and Core CPI correlation | 0.738 across 20 paired quarters |

Core CPI inflation eased from its September 2022 peak to 2.57% by
September 2026. The positive correlation in both windows indicates
that the two rates tended to move together, with a stronger linear
association in the five-year window.

## Missing data and limitations

October 2026 Core CPI inflation is unavailable because the October
2025 index needed for the year-over-year calculation is missing.
The quarterly comparison omits Q4 2025, and the chart shows a gap
at that quarter. GDP is measured in current dollars. The correlation
is descriptive and does not establish causality. FRED revisions can
change the results on later runs.

## Reproducibility and sources

Record the submitted CSV snapshot path and UTC retrieval timestamp here.

- [FRED nominal GDP](https://fred.stlouisfed.org/series/GDP)
- [FRED Core CPI](https://fred.stlouisfed.org/series/CPILFESL)
- [BLS note on October 2026 12-month changes](https://www.bls.gov/cpi/notices/2026/12m-changes-202610.htm)