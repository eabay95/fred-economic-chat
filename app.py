import os
from datetime import datetime, timezone

import pandas as pd
import streamlit as st
from openai import OpenAI, OpenAIError
from requests import RequestException

from answers import Answer, answer_request
from assistant import interpret_question
from fred_data import load_series

st.set_page_config(page_title="FRED Economic Chat", page_icon="📈", layout="wide")

STARTER_QUESTIONS = (
    "What is the latest reported U.S. GDP?",
    "What is the current Core CPI inflation rate?",
    "Plot GDP growth and Core CPI inflation over the last 10 years.",
    "Summarize the key economic trends in both datasets.",
)


@st.cache_data(ttl=900)
def fetch_series(series_id: str) -> tuple[pd.Series, datetime]:
    observations = load_series(series_id)
    return observations, datetime.now(timezone.utc)


def render_answer(
    answer: Answer, fetched_at: dict[str, datetime], turn: int
) -> None:
    with st.chat_message("assistant"):
        st.markdown(answer.text)

        if answer.chart is not None:
            st.plotly_chart(answer.chart, key=f"chart-{turn}", theme=None)

        if answer.sources:
            links = [
                f"[{series}](https://fred.stlouisfed.org/series/{series})"
                for series in answer.sources
            ]
            st.markdown("FRED sources · " + " · ".join(links))

            timestamps = [
                f"{series} {fetched_at[series]:%Y-%m-%d %H:%M UTC}"
                for series in answer.sources
            ]
            st.caption("Data fetched · " + " · ".join(timestamps))


st.title("FRED Economic Chat")
st.caption("Explore U.S. nominal GDP and Core CPI inflation.")

if not os.getenv("OPENAI_API_KEY"):
    st.error("Set OPENAI_API_KEY in your .env file, then restart the app.")
    st.stop()

if "history" not in st.session_state:
    st.session_state.history = []
    st.session_state.previous_request = None

starter_question = None
with st.sidebar:
    st.subheader("Try a question")
    for example in STARTER_QUESTIONS:
        if st.button(example):
            starter_question = example

for turn, (question, answer, fetched_at) in enumerate(st.session_state.history):
    with st.chat_message("user"):
        st.write(question)
    render_answer(answer, fetched_at, turn)

typed_question = st.chat_input("Ask about GDP or Core CPI inflation")
question = (typed_question or starter_question or "").strip()

if question:
    with st.chat_message("user"):
        st.write(question)

    fetched_at = {}

    def load_for_answer(series_id: str) -> pd.Series:
        observations, timestamp = fetch_series(series_id)
        fetched_at[series_id] = timestamp
        return observations

    with st.spinner("Analyzing your question…"):
        try:
            with OpenAI(timeout=30.0) as client:
                request = interpret_question(
                    client, question, st.session_state.previous_request
                )
            answer = answer_request(request, load=load_for_answer)
        except OpenAIError:
            answer = Answer(
                "The model request failed. Check your OpenAI API key, "
                "model access, and usage limits, then try again."
            )
        except RequestException:
            answer = Answer("FRED could not be reached. Try your question again.")
        except ValueError:
            answer = Answer(
                "The app could not process the request or the returned data. "
                "Try rephrasing your question."
            )
        else:
            if request.intent != "clarify":
                st.session_state.previous_request = request

    turn = len(st.session_state.history)
    st.session_state.history.append((question, answer, fetched_at))
    render_answer(answer, fetched_at, turn)