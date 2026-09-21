import time
from agents import resume_parser, jd_analyzer, skills_agent, experience_agent, ats_evaluator, suggestion_agent
from models.schemas import RunResult, AgentEvent

def run(resume_text, jd_text, mode="Fixed", event_cb=None):
    events = []
    times = {}

    def send(sender, receiver, msg_type, msg):
        evt = AgentEvent(sender=sender, receiver=receiver, message_type=msg_type, content=msg)
        events.append(evt)
        if event_cb:
            event_cb(evt)

    # 1. Resume Parser
    if event_cb: event_cb(AgentEvent(sender="System", receiver="Resume Parser", message_type="START", content="Starting Resume Parser..."))
    t = time.perf_counter()
    r = resume_parser.run(resume_text)
    times["Resume Parser"] = time.perf_counter() - t
    send("Resume Parser", "JD Analyzer", "PEER_MSG", f"Parsed candidate profile ({len(r.skills)} skills extracted). Ready for JD sync.")

    # 2. JD Analyzer
    if event_cb: event_cb(AgentEvent(sender="System", receiver="JD Analyzer", message_type="START", content="Starting JD Analyzer..."))
    t = time.perf_counter()
    j = jd_analyzer.run(jd_text)
    times["JD Analyzer"] = time.perf_counter() - t
    send("JD Analyzer", "Skills Agent", "PEER_MSG", f"JD requirements parsed for '{j.job_title}'. Transmitting required criteria.")

    # 3. Skills Agent
    if event_cb: event_cb(AgentEvent(sender="System", receiver="Skills Agent", message_type="START", content="Skills Agent matching skills..."))
    t = time.perf_counter()
    s = skills_agent.run(r, j)
    times["Skills Agent"] = time.perf_counter() - t
    send("Skills Agent", "Experience Agent", "PEER_MSG", f"Skill matching complete ({len(s.matched_skills)} matched, {len(s.missing_skills)} missing). Sharing context.")

    # 4. Experience Agent
    if event_cb: event_cb(AgentEvent(sender="System", receiver="Experience Agent", message_type="START", content="Experience Agent evaluating background..."))
    t = time.perf_counter()
    e = experience_agent.run(r, j)
    times["Experience Agent"] = time.perf_counter() - t

    if mode == "Dynamic":
        send("ATS Evaluator", "Skills Agent", "DYNAMIC_QUERY", "Querying Skills Agent for deep-dive skill deficit breakdown.")
        send("ATS Evaluator", "Experience Agent", "DYNAMIC_QUERY", "Querying Experience Agent for relevance evidence and career gaps.")
    else:
        send("Skills Agent", "ATS Evaluator", "FIXED_HANDOFF", f"Handing off {len(s.matched_skills)} matched skills to ATS Evaluator.")
        send("Experience Agent", "ATS Evaluator", "FIXED_HANDOFF", "Handing off career and education match analysis to ATS Evaluator.")

    # 5. ATS Evaluator
    if event_cb: event_cb(AgentEvent(sender="System", receiver="ATS Evaluator", message_type="START", content="ATS Evaluator synthesizing score..."))
    t = time.perf_counter()
    a = ats_evaluator.run(r, j, s, e)
    times["ATS Evaluator"] = time.perf_counter() - t
    send("ATS Evaluator", "Suggestion Agent", "PEER_MSG", f"Final ATS Score computed: {a.ats_score}/100 with {len(a.weaknesses)} identified gaps.")

    # 6. Suggestion Agent
    if event_cb: event_cb(AgentEvent(sender="System", receiver="Suggestion Agent", message_type="START", content="Suggestion Agent preparing recommendations..."))
    t = time.perf_counter()
    g = suggestion_agent.run(r, j, s, e, a)
    times["Suggestion Agent"] = time.perf_counter() - t
    send("Suggestion Agent", "Candidate Dashboard", "FINAL_DELIVERY", f"Delivered {len(g.suggestions)} actionable optimization steps.")

    return RunResult(
        resume=r, jd=j, skills=s, experience=e, ats=a, suggestions=g,
        events=events, timings=times, architecture=f"Peer-to-Peer ({mode})"
    )

