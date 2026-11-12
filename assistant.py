import json
import os
from typing import Literal

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field

load_dotenv()


class AnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: Literal[
        "latest_gdp",
        "latest_gdp_growth",
        "latest_core_cpi_inflation",
        "gdp_trend",
        "core_cpi_trend",
        "compare",
        "summarize",
        "clarify",
    ]
    years: int | None = Field(ge=1, le=50)
    show_chart: bool
    clarification: str | None


ROUTING_INSTRUCTIONS = """
Convert the user's question into an analysis request for a FRED app.
The supported series are nominal U.S. GDP and U.S. Core CPI.

- Use latest_gdp for the GDP level and latest_gdp_growth for its YoY rate.
- Use latest_core_cpi_inflation for the latest monthly YoY inflation rate.
- Use gdp_trend for historical nominal GDP levels. Default to 10 years.
- Use core_cpi_trend for historical monthly YoY inflation. Default to 5 years.
- Use compare for questions about the relationship between both series
  or charts comparing them. Default to 10 years.
- Use summarize for a combined trends summary. Default to 10 years.
- Set years to null for latest observations.
- Set show_chart to true when the user asks for a chart or plot.
- For a follow-up that only changes the time window, keep the prior intent
  and chart preference. If the prior intent was latest and the user now
  wants a historical chart, switch to the corresponding trend intent
  when that metric has a supported trend.
- Use clarify if the question is ambiguous or asks for an unsupported
  measure or date range. Set years to null and show_chart to false, and
  put a short question or explanation in clarification.
- Set clarification to null for every other intent.
"""


def interpret_question(
    client: OpenAI,
    question: str,
    previous_request: AnalysisRequest | None = None,
) -> AnalysisRequest:
    payload = {
        "question": question,
        "previous_request": (
            previous_request.model_dump() if previous_request else None
        ),
    }

    response = client.responses.parse(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        instructions=ROUTING_INSTRUCTIONS,
        input=json.dumps(payload),
        text_format=AnalysisRequest,
        store=False,
    )

    if response.output_parsed is None:
        raise ValueError("The model did not return a usable analysis request.")

    return response.output_parsed


if __name__ == "__main__":
    client = OpenAI()
    previous_request = None

    while True:
        question = input("\nAsk a FRED question (Enter to exit): ").strip()
        if not question:
            break

        request = interpret_question(client, question, previous_request)
        print(request.model_dump_json(indent=2))

        if request.intent != "clarify":
            previous_request = request