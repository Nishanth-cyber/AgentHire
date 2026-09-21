import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv(override=True)

from services.pdf_parser import extract_pdf_text
from services.llm import (
    check_ollama, check_huggingface, get_llm, set_active_llm,
    get_hf_token, HF_POPULAR_FREE_MODELS, DEFAULT_HF_MODEL, DEFAULT_OLLAMA_MODEL, DEFAULT_PROVIDER
)
from services.report_generator import generate_pdf_report
from communication import sequential, parallel, blackboard, p2p
from ui.visualization import show_architecture

st.set_page_config(page_title="Multi-Agent ATS Analyzer", page_icon="🤖", layout="wide")
st.markdown("""<style>.block-container{padding-top:2rem}.metric-card{padding:1rem;border:1px solid #ddd;border-radius:12px}</style>""", unsafe_allow_html=True)

st.title("🤖 Multi-Agent Resume ATS Analyzer")
st.caption("Six specialized agents • Four communication architectures • Free Hugging Face & Local Ollama")

with st.sidebar:
    st.header("1. LLM Provider")
    provider_options = ["Hugging Face (Free Cloud)", "Ollama (Local)"]
    default_provider_idx = 1 if "ollama" in DEFAULT_PROVIDER.lower() else 0
    provider = st.radio("Provider", provider_options, index=default_provider_idx)
    
    selected_model = ""
    hf_token = ""
    is_ready = False
    
    if provider == "Hugging Face (Free Cloud)":
        default_model_idx = HF_POPULAR_FREE_MODELS.index(DEFAULT_HF_MODEL) if DEFAULT_HF_MODEL in HF_POPULAR_FREE_MODELS else 0
        selected_model = st.selectbox("Free Hugging Face Model", HF_POPULAR_FREE_MODELS, index=default_model_idx)
        env_token = get_hf_token() or ""
        default_token = st.session_state.get("hf_token") or env_token
        hf_token = st.text_input(
            "🔑 Hugging Face API Token (Free)",
            value=default_token,
            type="password",
            help="Configured in .env as HF_TOKEN or paste here"
        )
        if hf_token:
            st.session_state["hf_token"] = hf_token
        
        ok, msg = check_huggingface(selected_model, hf_token)
        is_ready = ok
        st.write("🟢" if ok else "🔴", msg)
        if not ok:
            st.caption("💡 Set `HF_TOKEN` in `.env` or get a free token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)")
    else:
        selected_model = st.text_input("Ollama Model", value=DEFAULT_OLLAMA_MODEL)
        ok, msg = check_ollama(selected_model)
        is_ready = ok
        st.write("🟢" if ok else "🔴", msg)
        st.caption("Configured in `.env` as `OLLAMA_MODEL` (default: http://localhost:11434)")


    st.divider()
    st.header("2. Communication Framework")
    mode = st.radio("Architecture", ["Sequential", "Parallel", "Blackboard / Shared State", "Peer-to-Peer"])
    p2p_mode = "Fixed"
    if mode == "Peer-to-Peer":
        p2p_mode = st.radio("P2P Mode", ["Fixed", "Dynamic"])

left, right = st.columns([1, 1])
with left:
    upload = st.file_uploader("📄 Upload Resume PDF", type=["pdf"])
with right:
    jd = st.text_area("📋 Paste Job Description", height=220, placeholder="Paste the complete job description here...")

st.subheader("Architecture")
show_architecture(mode)

if st.button("🚀 Analyze Resume", type="primary", use_container_width=True):
    if not upload:
        st.error("Please upload a resume PDF."); st.stop()
    if not jd.strip():
        st.error("Please paste a Job Description."); st.stop()
    if provider == "Hugging Face (Free Cloud)" and not hf_token:
        st.error("Please enter your free Hugging Face API token in the sidebar to proceed (get one free at https://huggingface.co/settings/tokens).")
        st.stop()
        
    try:
        provider_key = "Hugging Face" if "Hugging Face" in provider else "Ollama"
        active_llm = get_llm(provider=provider_key, model_name=selected_model, token=hf_token)
        set_active_llm(active_llm)
    except Exception as e:
        st.error(f"Failed to initialize LLM: {e}")
        st.stop()
    
    with st.status("🤖 Multi-Agent Execution in Progress...", expanded=True) as status_box:
        def live_callback(evt):
            status_box.write(f"💬 **{evt.sender}** ➔ **{evt.receiver}** `[{evt.message_type}]`: {evt.content}")
        
        try:
            text = extract_pdf_text(upload.getvalue())
            if not text: st.error("No selectable text was found in the PDF."); st.stop()
            if mode == "Sequential":
                result = sequential.run(text, jd, event_cb=live_callback)
            elif mode == "Parallel":
                result = parallel.run(text, jd, event_cb=live_callback)
            elif mode == "Blackboard / Shared State":
                result = blackboard.run(text, jd, event_cb=live_callback)
            else:
                result = p2p.run(text, jd, mode=p2p_mode, event_cb=live_callback)
            st.session_state["result"] = result
            status_box.update(label="✅ Analysis complete across all 6 agents!", state="complete", expanded=False)
        except Exception as e:
            status_box.update(label="❌ Analysis failed", state="error")
            st.error(f"Analysis failed: {e}")
            st.stop()


result=st.session_state.get("result")
if result:
    st.divider()
    c1,c2,c3=st.columns(3)
    c1.metric("ATS Score",f"{result.ats.ats_score}/100")
    c2.metric("Architecture",result.architecture)
    c3.metric("Agents",6)
    st.subheader("📊 ATS Dashboard")
    a,b=st.columns(2)
    with a:
        st.markdown("### Skills Match")
        st.write("**Matched:**", ", ".join(result.skills.matched_skills) or "None")
        st.write("**Missing:**", ", ".join(result.skills.missing_skills) or "None")
        st.write("**Partial:**", ", ".join(result.skills.partial_matches) or "None")
        st.write(result.skills.skill_analysis)
    with b:
        st.markdown("### Experience & Education")
        st.write(result.experience.experience_match)
        st.write(result.experience.education_match)
        st.write(result.experience.analysis)
    st.markdown("### Strengths")
    for x in result.ats.strengths: st.write("• ",x)
    st.markdown("### Weaknesses")
    for x in result.ats.weaknesses: st.write("• ",x)
    st.markdown("### Improvement Suggestions")
    for x in result.suggestions.suggestions: st.write("• ",x)
    
    st.markdown("### 💬 Agent Communication Trace")
    st.caption("Chronological exchange of data payloads, handoffs, and coordination signals between agents:")
    if result.events:
        for idx, e in enumerate(result.events, start=1):
            color = "#3b82f6" if any(k in e.message_type for k in ["TRANSFER", "HANDOFF"]) else ("#10b981" if any(k in e.message_type for k in ["WRITE", "JOIN"]) else ("#f59e0b" if "READ" in e.message_type else "#8b5cf6"))
            st.markdown(
                f"""
                <div style="padding: 10px 14px; margin-bottom: 8px; border-left: 4px solid {color}; background-color: rgba(128,128,128,0.08); border-radius: 6px;">
                    <span style="font-size: 0.75em; color: #888; font-weight: bold; margin-right: 8px;">STEP {idx}</span>
                    <span style="font-size: 0.72em; background-color: {color}22; color: {color}; border: 1px solid {color}44; padding: 2px 6px; border-radius: 4px; margin-right: 8px;">{e.message_type}</span>
                    <strong>{e.sender}</strong> &nbsp;➔&nbsp; <strong>{e.receiver}</strong>
                    <div style="margin-top: 4px; font-size: 0.92em;">{e.content}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.code(" → ".join(result.timings.keys()), language="text")
        
    st.markdown("### 🛠️ Agent Execution & Validation Details")
    st.dataframe(
        [
            {
                "Agent": k,
                "Status": "✅ Completed",
                "Parsing": "JSON Extracted",
                "Validation": "Pydantic Validated",
                "Execution Time": f"{round(v, 2)}s"
            }
            for k, v in result.timings.items()
        ],
        use_container_width=True,
        hide_index=True
    )

    with st.expander("🔍 Inspect Clean Structured Agent Outputs (JSON)"):
        t1, t2, t3 = st.tabs(["Resume & JD", "Skills & Experience", "ATS & Suggestions"])
        with t1:
            st.markdown("**Parsed Resume Data:**")
            st.json(result.resume.model_dump())
            st.markdown("**Parsed JD Data:**")
            st.json(result.jd.model_dump())
        with t2:
            st.markdown("**Skills Analysis:**")
            st.json(result.skills.model_dump())
            st.markdown("**Experience Analysis:**")
            st.json(result.experience.model_dump())
        with t3:
            st.markdown("**ATS Compatibility Analysis:**")
            st.json(result.ats.model_dump())
            st.markdown("**Improvement Suggestions:**")
            st.json(result.suggestions.model_dump())

    st.subheader("📥 Download")
    pdf = generate_pdf_report(result)
    st.download_button("📥 Download ATS Report", data=pdf, file_name="resume_ats_report.pdf", mime="application/pdf", use_container_width=True)

