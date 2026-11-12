# FRED Economic Chat Assistant

A Streamlit app for exploring U.S. nominal GDP and Core CPI inflation through natural-language questions. It retrieves live observations from FRED, calculates economic indicators, and displays interactive Plotly charts in the conversation.

## Quick start

You need Python 3.10 or later, an OpenAI API key, and internet access to FRED and OpenAI.

From the project root, run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

If you already have a `.env` file, use it and skip the copy command. Set the following values in `.env`:

```dotenv
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4.1-mini
```

Keep your API key in `.env`. The repository includes `.env.example` with placeholders for setup.

Launch the app:

```bash
python -m streamlit run app.py
```

Open the local URL printed in the terminal.

## Example questions

- What is the latest reported U.S. GDP?
- How has U.S. GDP changed over the past 10 years?
- What is the current Core CPI inflation rate?
- How has Core CPI inflation changed over the past five years?
- What is the relationship between GDP growth and Core CPI inflation?
- Plot GDP growth and Core CPI inflation over the last 10 years.
- Summarize the key economic trends in both datasets.

After requesting the comparison chart, ask **“Show me the last five years instead.”** The app carries the comparison and chart preference into the follow-up.

## How it works

The OpenAI model converts each question into a structured analysis request. Python retrieves the required FRED series, calculates the results with pandas, and formats the answer. Streamlit displays the answer, source links, fetch timestamps, and any requested Plotly chart.

The comparison pairs year-over-year nominal GDP growth with year-over-year Core CPI inflation calculated from complete quarterly CPI averages. Missing observations appear as gaps in the charts. Pearson correlation describes how the rates moved together over the selected quarters.

## Project files

| File | Purpose |
|---|---|
| `app.py` | Streamlit chat interface, session state, and FRED data cache |
| `assistant.py` | LLM question parsing and follow-up context |
| `answers.py` | Analysis dispatch and answer formatting |
| `fred_data.py` | FRED CSV retrieval and observation parsing |
| `analytics.py` | Year-over-year calculations and quarterly alignment |
| `charts.py` | Plotly chart generation and HTML exports |

## Documentation and figures

- [System architecture](docs/architecture.md)
- [Sample conversations](docs/sample_conversations.md)
- [Technical report and findings](docs/technical_report.md)
- [Nominal GDP chart](docs/figures/nominal_gdp.html)
- [Core CPI inflation chart](docs/figures/core_cpi_inflation.html)
- [GDP growth vs. Core CPI inflation chart](docs/figures/gdp_vs_core_cpi.html)

Run `python charts.py` to regenerate the three HTML figures from live FRED data. The dated snapshots in `docs/data/` document the observations used for the report. Live results may change as FRED releases new observations or revises historical values.

## Data sources

- [FRED GDP](https://fred.stlouisfed.org/series/GDP) — Quarterly nominal U.S. GDP in billions of dollars at a seasonally adjusted annual rate.
- [FRED CPILFESL](https://fred.stlouisfed.org/series/CPILFESL) — Monthly seasonally adjusted Core CPI index, excluding food and energy.