import time
from models.state import Blackboard
from models.schemas import RunResult, AgentEvent
from agents import resume_parser, jd_analyzer, skills_agent, experience_agent, ats_evaluator, suggestion_agent

def run(resume_text, jd_text, event_cb=None):
    b = Blackboard()

    def emit(sender, receiver, msg_type, content):
        evt = AgentEvent(sender=sender, receiver=receiver, message_type=msg_type, content=content)
        b.events.append(evt)
        if event_cb:
            event_cb(evt)

    def put(name, fn, *args):
        t = time.perf_counter()
        out = fn(*args)
        b.timings[name] = time.perf_counter() - t
        setattr(b, name.lower().replace(" ", "_").replace("&_", ""), out)
        return out

    # 1. Resume Parser
    if event_cb: event_cb(AgentEvent(sender="System", receiver="Resume Parser", message_type="START", content="Extracting resume to write to shared blackboard..."))
    b.resume = put("Resume Parser", resume_parser.run, resume_text)
    emit("Resume Parser", "Shared Blackboard", "WRITE", f"Committed candidate profile ({len(b.resume.skills)} skills, {len(b.resume.education)} education items, {len(b.resume.experience)} jobs).")

    # 2. JD Analyzer
    if event_cb: event_cb(AgentEvent(sender="System", receiver="JD Analyzer", message_type="START", content="Extracting job description to write to shared blackboard..."))
    b.jd = put("JD Analyzer", jd_analyzer.run, jd_text)
    emit("JD Analyzer", "Shared Blackboard", "WRITE", f"Committed target role '{b.jd.job_title}' and {len(b.jd.required_skills)} required skills.")

    # 3. Skills Matching
    emit("Skills Matching", "Shared Blackboard", "READ", "Read candidate skills and job requirements from Blackboard.")
    b.skills = put("Skills Matching", skills_agent.run, b.resume, b.jd)
    emit("Skills Matching", "Shared Blackboard", "WRITE", f"Committed skills evaluation ({len(b.skills.matched_skills)} matched, {len(b.skills.missing_skills)} missing).")

    # 4. Experience & Education
    emit("Experience Agent", "Shared Blackboard", "READ", "Read candidate history and job requirements from Blackboard.")
    b.experience = put("Experience & Education", experience_agent.run, b.resume, b.jd)
    emit("Experience Agent", "Shared Blackboard", "WRITE", f"Committed experience & education analysis.")

    # 5. ATS Evaluator
    emit("ATS Evaluator", "Shared Blackboard", "READ_ALL", "Read all consolidated state slices from Blackboard.")
    b.ats = put("ATS Evaluator", ats_evaluator.run, b.resume, b.jd, b.skills, b.experience)
    emit("ATS Evaluator", "Shared Blackboard", "WRITE", f"Committed ATS compatibility score ({b.ats.ats_score}/100) and analysis.")

    # 6. Suggestion Agent
    emit("Suggestion Agent", "Shared Blackboard", "READ_ALL", "Read complete analysis history from Blackboard.")
    b.suggestions = put("Suggestion Agent", suggestion_agent.run, b.resume, b.jd, b.skills, b.experience, b.ats)
    emit("Suggestion Agent", "Shared Blackboard", "WRITE", f"Committed {len(b.suggestions.suggestions)} actionable resume suggestions.")

    return RunResult(
        resume=b.resume, jd=b.jd, skills=b.skills, experience=b.experience,
        ats=b.ats, suggestions=b.suggestions, events=b.events, timings=b.timings,
        architecture="Blackboard / Shared State"
    )

