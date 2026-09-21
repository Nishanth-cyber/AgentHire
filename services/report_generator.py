from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors

def generate_pdf_report(result) -> bytes:
    out = BytesIO()
    doc = SimpleDocTemplate(out, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    title = ParagraphStyle("Title2", parent=styles["Title"], alignment=TA_CENTER, fontSize=20, spaceAfter=18)
    story = [Paragraph("MULTI-AGENT RESUME ATS ANALYZER", title), Paragraph("AI ATS Analysis Report", styles["Heading2"]), Spacer(1, 10)]
    story += [Paragraph(f"Architecture: {result.architecture}", styles["Normal"]), Spacer(1, 12)]
    story += [Paragraph(f"ATS Score: {result.ats.ats_score}/100", styles["Heading1"]), Paragraph(result.ats.score_explanation, styles["BodyText"]), Spacer(1, 12)]
    def section(head, items):
        nonlocal story
        story.append(Paragraph(head, styles["Heading2"]))
        for x in items:
            story.append(Paragraph(f"• {x}", styles["BodyText"]))
        story.append(Spacer(1, 8))
    section("Skills Match", [f"Matched: {', '.join(result.skills.matched_skills) or 'None'}", f"Missing: {', '.join(result.skills.missing_skills) or 'None'}", f"Partial: {', '.join(result.skills.partial_matches) or 'None'}", result.skills.skill_analysis])
    section("Experience & Education", [result.experience.experience_match, result.experience.education_match, result.experience.analysis] + result.experience.gaps)
    section("Strengths", result.ats.strengths)
    section("Weaknesses", result.ats.weaknesses)
    section("Suggestions", result.suggestions.suggestions + result.suggestions.keyword_suggestions)
    story.append(Paragraph("Agent Execution", styles["Heading2"]))
    rows = [["Agent", "Time (s)"]] + [[k, f"{v:.2f}"] for k, v in result.timings.items()]
    t = Table(rows, colWidths=[300, 100])
    t.setStyle(TableStyle([("GRID", (0,0), (-1,-1), 0.5, colors.grey), ("BACKGROUND", (0,0), (-1,0), colors.lightgrey)]))
    story.append(t)
    doc.build(story)
    return out.getvalue()
