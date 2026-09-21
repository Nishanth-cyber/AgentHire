import time
from concurrent.futures import ThreadPoolExecutor
from agents import resume_parser, jd_analyzer, skills_agent, experience_agent, ats_evaluator, suggestion_agent
from models.schemas import RunResult, AgentEvent

def run(resume_text, jd_text, event_cb=None):
    times = {}
    events = []

    def emit(sender, receiver, msg_type, content):
        evt = AgentEvent(sender=sender, receiver=receiver, message_type=msg_type, content=content)
        events.append(evt)
        if event_cb:
            event_cb(evt)

    # Initial Parsing
    if event_cb: event_cb(AgentEvent(sender="Coordinator", receiver="Resume Parser", message_type="TASK_DISPATCH", content="Parsing candidate resume..."))
    t = time.perf_counter()
    r = resume_parser.run(resume_text)
    times["Resume Parser"] = time.perf_counter() - t
    emit("Resume Parser", "Coordinator", "DATA_TRANSFER", f"Extracted {len(r.skills)} skills and {len(r.experience)} work history entries.")

    if event_cb: event_cb(AgentEvent(sender="Coordinator", receiver="JD Analyzer", message_type="TASK_DISPATCH", content="Parsing target job description..."))
    t = time.perf_counter()
    j = jd_analyzer.run(jd_text)
    times["JD Analyzer"] = time.perf_counter() - t
    emit("JD Analyzer", "Coordinator", "DATA_TRANSFER", f"Extracted requirements for '{j.job_title}'.")

    # Parallel Execution Fork
    emit("Coordinator", "Skills Agent & Experience Agent", "PARALLEL_FORK", "Broadcasting resume + JD to Skills Agent and Experience Agent concurrently via ThreadPoolExecutor.")

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=2) as ex:
        fs = ex.submit(skills_agent.run, r, j)
        fe = ex.submit(experience_agent.run, r, j)
        s = fs.result()
        e = fe.result()
    times["Parallel analysis (Skills ∥ Experience)"] = time.perf_counter() - start

    emit("Skills Agent", "Coordinator", "PARALLEL_JOIN", f"Skills analysis complete: {len(s.matched_skills)} matched, {len(s.missing_skills)} missing.")
    emit("Experience Agent", "Coordinator", "PARALLEL_JOIN", f"Experience analysis complete: fit evaluation '{e.experience_match[:50]}...'.")

    # ATS Evaluation
    emit("Coordinator", "ATS Evaluator", "CONSOLIDATION", "Consolidated parallel findings into ATS Evaluator input payload.")
    t = time.perf_counter()
    a = ats_evaluator.run(r, j, s, e)
    times["ATS Evaluator"] = time.perf_counter() - t
    emit("ATS Evaluator", "Suggestion Agent", "SCORE_DISPATCH", f"Assigned ATS Score: {a.ats_score}/100 with {len(a.strengths)} strengths.")

    # Suggestion Agent
    t = time.perf_counter()
    g = suggestion_agent.run(r, j, s, e, a)
    times["Suggestion Agent"] = time.perf_counter() - t
    emit("Suggestion Agent", "Coordinator", "RECOMMENDATIONS", f"Generated {len(g.suggestions)} improvement suggestions.")

    return RunResult(
        resume=r, jd=j, skills=s, experience=e, ats=a, suggestions=g,
        events=events, timings=times, architecture="Parallel"
    )

