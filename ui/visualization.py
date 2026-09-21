import streamlit as st

def show_architecture(mode):
    mermaid_diagrams = {
        "Sequential": """graph LR
    RP["📄 Resume Parser"] --> JDA["📋 JD Analyzer"]
    JDA --> SMA["🎯 Skills Matching"]
    SMA --> EEA["💼 Experience & Education"]
    EEA --> ATS["⚖️ ATS Evaluator"]
    ATS --> SA["💡 Suggestion Agent"]
""",
        "Parallel": """graph TD
    IN["📄 Resume + 📋 JD"] --> FORK["⚡ Fork (ThreadPool)"]
    FORK --> SMA["🎯 Skills Matching (Thread 1)"]
    FORK --> EEA["💼 Experience & Edu (Thread 2)"]
    SMA --> JOIN["🔄 Join Results"]
    EEA --> JOIN
    JOIN --> ATS["⚖️ ATS Evaluator"]
    ATS --> SA["💡 Suggestion Agent"]
""",
        "Blackboard / Shared State": """graph TD
    BB[("🗄️ Shared Blackboard State")]
    RP["📄 Resume Parser"] -->|Write| BB
    JDA["📋 JD Analyzer"] -->|Write| BB
    BB -->|Read| SMA["🎯 Skills Matching"]
    SMA -->|Write| BB
    BB -->|Read| EEA["💼 Experience & Edu"]
    EEA -->|Write| BB
    BB -->|Read State| ATS["⚖️ ATS Evaluator"]
    ATS -->|Write Score| BB
    BB -->|Read All| SA["💡 Suggestion Agent"]
    SA -->|Write Advice| BB
""",
        "Peer-to-Peer": """graph LR
    RP["📄 Resume Parser"] <-->|Sync| JDA["📋 JD Analyzer"]
    JDA <-->|Requirements| SMA["🎯 Skills Agent"]
    SMA <-->|Context| EEA["💼 Experience Agent"]
    SMA <-->|Evidence| ATS["⚖️ ATS Evaluator"]
    EEA <-->|Evidence| ATS
    ATS <-->|Score| SA["💡 Suggestion Agent"]
"""
    }

    diag = mermaid_diagrams.get(mode)
    if diag:
        st.markdown(f"```mermaid\n{diag}\n```")

