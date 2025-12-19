import streamlit as st
from openai import OpenAI

# ----------------------------
# API key handling
# ----------------------------

client = OpenAI()

# ----------------------------
# Page config
# ----------------------------
st.set_page_config(
    page_title="ChatGPT Assistant",
    page_icon="💬",
    layout="wide"
)

st.title("💬 ChatGPT Assistant")
st.caption("Powered by OpenAI API")

# ----------------------------
# Domain system prompts (integration-ready)
# ----------------------------
SYSTEM_PROMPTS = {
    "Cybersecurity": """You are a cybersecurity expert assistant.
- Analyze incidents and threats
- Provide technical guidance
- Explain attack vectors and mitigations
- Use standard terminology (MITRE ATT&CK, CVE when relevant)
- Prioritize actionable recommendations
Tone: Professional, technical
Format: Clear, structured responses""",

    "Data Science": """You are a data science expert assistant.
- Help with analysis, visualization, and statistical insights
- Explain methods clearly and suggest next steps
Tone: Helpful, analytical
Format: Clear, structured responses""",

    "IT Operations": """You are an IT operations expert assistant.
- Troubleshoot issues, optimize systems, and manage tickets
- Provide step-by-step troubleshooting
Tone: Professional, practical
Format: Clear, actionable responses"""
}

# ----------------------------
# Sidebar controls
# ----------------------------
with st.sidebar:
    st.subheader("Chat Controls")

    # Domain selection (this maps to your coursework domains)
    domain = st.selectbox(
        "Domain",
        list(SYSTEM_PROMPTS.keys()),
        index=0
    )

    model = st.selectbox(
        "Model",
        ["gpt-4o-mini", "gpt-4o"],
        index=0
    )

    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=2.0,
        value=0.7,
        step=0.1,
        help="Higher values make output more random"
    )

    if st.button("Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.write("**Message count:**", len(st.session_state.get("messages", [])))


# ----------------------------
# Session state: messages
# Start with a system message based on chosen domain
# ----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPTS[domain]}
    ]

if "last_domain" not in st.session_state:
    st.session_state.last_domain = domain

if domain != st.session_state.last_domain:
    st.session_state.last_domain = domain
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPTS[domain]}
    ]
    st.rerun()

# ----------------------------
# Display chat history (skip system message)
# ----------------------------
for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ----------------------------
# User input
# ----------------------------
prompt = st.chat_input("Ask something...")

if prompt:
    # Show user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Stream assistant response
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_reply = ""

        with st.spinner("Thinking..."):
            stream = client.chat.completions.create(
                model=model,
                messages=st.session_state.messages,
                temperature=temperature,
                stream=True
            )

            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta and getattr(delta, "content", None):
                    full_reply += delta.content
                    placeholder.markdown(full_reply)

        # Save assistant response
        st.session_state.messages.append({"role": "assistant", "content": full_reply})