flowchart TD
    UI["Streamlit chat"] --> ROUTER["Question parser"]
    STATE["Previous successful request"] --> ROUTER
    ROUTER --> LLM["OpenAI structured output"]
    LLM --> ENGINE["Python answer engine"]
    FRED["FRED GDP and Core CPI"] --> CACHE["Data loader and cache"]
    CACHE --> ENGINE
    ENGINE --> ANALYTICS["pandas calculations"]
    ANALYTICS --> RESULT["Answer text and Plotly chart"]
    RESULT --> UI