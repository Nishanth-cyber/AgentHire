import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schemas import (
    ResumeData, JDData, SkillsAnalysis, ExperienceAnalysis, ATSAnalysis, Suggestions, RunResult
)
from communication import sequential, parallel, blackboard, p2p
from services.report_generator import generate_pdf_report

MOCK_RESUME = ResumeData(name="Alice Developer", skills=["Python", "SQL", "Docker"], experience=["3 years backend engineer"])
MOCK_JD = JDData(job_title="Python Developer", required_skills=["Python", "SQL"], keywords=["FastAPI", "PostgreSQL"])
MOCK_SKILLS = SkillsAnalysis(matched_skills=["Python", "SQL"], missing_skills=["FastAPI"], skill_analysis="Good match")
MOCK_EXP = ExperienceAnalysis(experience_match="Strong", education_match="Matches", analysis="Well aligned")
MOCK_ATS = ATSAnalysis(ats_score=85, score_explanation="Matches required core skills", strengths=["Python expert"], weaknesses=["Missing FastAPI"])
MOCK_SUGG = Suggestions(suggestions=["Highlight FastAPI projects"], keyword_suggestions=["FastAPI"])

class TestArchitectures(unittest.TestCase):
    def setUp(self):
        self.patchers = [
            patch("agents.resume_parser.run", return_value=MOCK_RESUME),
            patch("agents.jd_analyzer.run", return_value=MOCK_JD),
            patch("agents.skills_agent.run", return_value=MOCK_SKILLS),
            patch("agents.experience_agent.run", return_value=MOCK_EXP),
            patch("agents.ats_evaluator.run", return_value=MOCK_ATS),
            patch("agents.suggestion_agent.run", return_value=MOCK_SUGG),
        ]
        for p in self.patchers:
            p.start()

    def tearDown(self):
        for p in self.patchers:
            p.stop()

    def test_sequential_architecture(self):
        events = []
        res = sequential.run("dummy resume text", "dummy jd text", event_cb=lambda e: events.append(e))
        self.assertIsInstance(res, RunResult)
        self.assertEqual(res.architecture, "Sequential")
        self.assertEqual(res.ats.ats_score, 85)
        self.assertTrue(len(res.events) > 0)
        pdf = generate_pdf_report(res)
        self.assertTrue(len(pdf) > 100)

    def test_parallel_architecture(self):
        events = []
        res = parallel.run("dummy resume text", "dummy jd text", event_cb=lambda e: events.append(e))
        self.assertIsInstance(res, RunResult)
        self.assertEqual(res.architecture, "Parallel")
        self.assertEqual(res.ats.ats_score, 85)
        self.assertTrue(len(res.events) > 0)
        pdf = generate_pdf_report(res)
        self.assertTrue(len(pdf) > 100)

    def test_blackboard_architecture(self):
        events = []
        res = blackboard.run("dummy resume text", "dummy jd text", event_cb=lambda e: events.append(e))
        self.assertIsInstance(res, RunResult)
        self.assertEqual(res.architecture, "Blackboard / Shared State")
        self.assertEqual(res.ats.ats_score, 85)
        self.assertTrue(len(res.events) > 0)
        pdf = generate_pdf_report(res)
        self.assertTrue(len(pdf) > 100)

    def test_p2p_fixed_architecture(self):
        events = []
        res = p2p.run("dummy resume text", "dummy jd text", mode="Fixed", event_cb=lambda e: events.append(e))
        self.assertIsInstance(res, RunResult)
        self.assertEqual(res.architecture, "Peer-to-Peer (Fixed)")
        self.assertEqual(res.ats.ats_score, 85)
        self.assertTrue(len(res.events) > 0)
        pdf = generate_pdf_report(res)
        self.assertTrue(len(pdf) > 100)

    def test_p2p_dynamic_architecture(self):
        events = []
        res = p2p.run("dummy resume text", "dummy jd text", mode="Dynamic", event_cb=lambda e: events.append(e))
        self.assertIsInstance(res, RunResult)
        self.assertEqual(res.architecture, "Peer-to-Peer (Dynamic)")
        self.assertEqual(res.ats.ats_score, 85)
        self.assertTrue(len(res.events) > 0)
        pdf = generate_pdf_report(res)
        self.assertTrue(len(pdf) > 100)

if __name__ == "__main__":
    unittest.main()
