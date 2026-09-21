import time
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

    # 1. Resume Parser
    if event_cb: event_cb(AgentEvent(sender="System", receiver="Resume Parser", message_type="START", content="Starting Resume Parser agent..."))
    t = time.perf_counter()
    r = resume_parser.run(resume_text)
    times["Resume Parser"] = time.perf_counter() - t
    emit("Resume Parser", "JD Analyzer", "DATA_TRANSFER", f"Extracted {len(r.skills)} skills, {len(r.experience)} work history items, and {len(r.education)} education records.")

    # 2. JD Analyzer
    if event_cb: event_cb(AgentEvent(sender="System", receiver="JD Analyzer", message_type="START", content="Starting Job Description Analyzer..."))
    t = time.perf_counter()
    j = jd_analyzer.run(jd_text)
    times["JD Analyzer"] = time.perf_counter() - t
    emit("JD Analyzer", "Skills Matching", "DATA_TRANSFER", f"Extracted target role '{j.job_title}' with {len(j.required_skills)} required skills and {len(j.keywords)} core keywords.")

    # 3. Skills Matching
    if event_cb: event_cb(AgentEvent(sender="System", receiver="Skills Matching", message_type="START", content="Comparing candidate skills against job requirements..."))
    t = time.perf_counter()
    s = skills_agent.run(r, j)
    times["Skills Matching"] = time.perf_counter() - t
    emit("Skills Matching", "Experience & Education", "ANALYSIS_UPDATE", f"Matched {len(s.matched_skills)} skills, flagged {len(s.missing_skills)} missing skills and {len(s.partial_matches)} partial matches.")

    # 4. Experience & Education
    if event_cb: event_cb(AgentEvent(sender="System", receiver="Experience & Education", message_type="START", content="Evaluating experience relevance and qualification criteria..."))
    t = time.perf_counter()
    e = experience_agent.run(r, j)
    times["Experience & Education"] = time.perf_counter() - t
    emit("Experience & Education", "ATS Evaluator", "HANDOVER", f"Experience Match: '{e.experience_match}'. Education Match: '{e.education_match}'.")

    # 5. ATS Evaluator
    if event_cb: event_cb(AgentEvent(sender="System", receiver="ATS Evaluator", message_type="START", content="Calculating composite ATS score and strength/weakness analysis..."))
    t = time.perf_counter()
    a = ats_evaluator.run(r, j, s, e)
    times["ATS Evaluator"] = time.perf_counter() - t
    emit("ATS Evaluator", "Suggestion Agent", "SCORE_DISPATCH", f"Assigned ATS Score: {a.ats_score}/100 with {len(a.strengths)} key strengths and {len(a.weaknesses)} weaknesses.")

    # 6. Suggestion Agent
    if event_cb: event_cb(AgentEvent(sender="System", receiver="Suggestion Agent", message_type="START", content="Generating targeted resume improvement suggestions..."))
    t = time.perf_counter()
    g = suggestion_agent.run(r, j, s, e, a)
    times["Suggestion Agent"] = time.perf_counter() - t
    emit("Suggestion Agent", "User Dashboard", "RECOMMENDATIONS", f"Generated {len(g.suggestions)} actionable resume adjustments and {len(g.keyword_suggestions)} keyword additions.")

    return RunResult(
        resume=r, jd=j, skills=s, experience=e, ats=a, suggestions=g,
        events=events, timings=times, architecture="Sequential"
    )

