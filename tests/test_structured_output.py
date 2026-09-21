import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import AIMessage
from models.schemas import ResumeData
from services.structured_output import parse_structured_response, StructuredOutputError

class TestStructuredOutput(unittest.TestCase):
    def test_1_plain_json(self):
        raw = '{"name": "John Doe", "email": "john@example.com", "skills": ["Python", "FastAPI"]}'
        res = parse_structured_response(raw, ResumeData)
        self.assertEqual(res.name, "John Doe")
        self.assertEqual(res.email, "john@example.com")
        self.assertIn("Python", res.skills)

    def test_2_markdown_fence(self):
        raw = '```json\n{"name": "John Doe", "email": "john@example.com", "skills": ["Python"]}\n```'
        res = parse_structured_response(raw, ResumeData)
        self.assertEqual(res.name, "John Doe")
        self.assertEqual(res.email, "john@example.com")

    def test_3_text_before_json(self):
        raw = 'Here is the extracted information:\n```json\n{"name": "John Doe", "email": "john@example.com", "skills": ["Python"]}\n```'
        res = parse_structured_response(raw, ResumeData)
        self.assertEqual(res.name, "John Doe")
        self.assertEqual(res.email, "john@example.com")

    def test_4_text_before_and_after_json(self):
        raw = 'The candidate has 5 years of experience.\n{"name": "John Doe", "email": "john@example.com", "skills": ["Python"]}\nHope this helps!'
        res = parse_structured_response(raw, ResumeData)
        self.assertEqual(res.name, "John Doe")
        self.assertEqual(res.email, "john@example.com")

    def test_5_deepseek_r1_reasoning_tags(self):
        raw = '<think>\nEvaluating resume text...\nThe candidate name is John Doe.\nSkills include Python.\n</think>\n```json\n{"name": "John Doe", "email": "john@example.com", "skills": ["Python"]}\n```'
        res = parse_structured_response(raw, ResumeData)
        self.assertEqual(res.name, "John Doe")
        self.assertEqual(res.email, "john@example.com")

    def test_6_langchain_ai_message(self):
        ai_msg = AIMessage(content='```json\n{"name": "Jane Smith", "email": "jane@example.com", "skills": ["AWS", "Docker"]}\n```')
        res = parse_structured_response(ai_msg, ResumeData)
        self.assertEqual(res.name, "Jane Smith")
        self.assertIn("AWS", res.skills)

    def test_7_invalid_json_raises_error(self):
        raw = "Not a JSON at all, just plain english text."
        with self.assertRaises(StructuredOutputError):
            parse_structured_response(raw, ResumeData)

if __name__ == "__main__":
    unittest.main()

