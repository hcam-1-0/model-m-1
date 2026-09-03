from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
GITHUB = ROOT / ".github"
ISSUE_TEMPLATE = GITHUB / "ISSUE_TEMPLATE"


class RepoGovernanceTests(unittest.TestCase):
    def test_pull_request_template_exists_with_safety_gate(self):
        template = GITHUB / "PULL_REQUEST_TEMPLATE.md"
        self.assertTrue(template.exists(), "Missing GitHub pull request template")
        content = template.read_text(encoding="utf-8")
        required_terms = [
            "Safety And Data Handling",
            "CCTV video",
            "credentials",
            "government data",
            "personally sensitive data",
            "python -m unittest discover -s tests -v",
            "git diff --check",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, content)

    def test_issue_templates_exist(self):
        expected_templates = [
            "config.yml",
            "phase_task.yml",
            "architecture_decision.yml",
            "risk_compliance.yml",
            "review_question.yml",
        ]
        for relative_path in expected_templates:
            with self.subTest(path=relative_path):
                path = ISSUE_TEMPLATE / relative_path
                self.assertTrue(path.exists(), f"Missing issue template: {path}")
                self.assertGreater(path.stat().st_size, 100, f"Template is too small: {path}")

    def test_phase_task_template_requires_validation_and_data_handling(self):
        content = (ISSUE_TEMPLATE / "phase_task.yml").read_text(encoding="utf-8")
        required_terms = [
            "Acceptance Criteria",
            "Safety And Data Handling",
            "Validation Plan",
            "No CCTV video, credentials, government data, police records, or personally sensitive data",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, content)

    def test_architecture_template_tracks_decision_impact(self):
        content = (ISSUE_TEMPLATE / "architecture_decision.yml").read_text(encoding="utf-8")
        required_terms = [
            "Decision Status",
            "Options Considered",
            "Consequences",
            "Safety And Data Impact",
            "audit logs",
            "retention",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, content)

    def test_risk_template_tracks_controls_and_evidence(self):
        content = (ISSUE_TEMPLATE / "risk_compliance.yml").read_text(encoding="utf-8")
        required_terms = [
            "Risk Class",
            "Severity",
            "Data Involved",
            "Required Controls",
            "Validation Evidence",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, content)

    def test_review_question_template_tracks_phase_blockers(self):
        content = (ISSUE_TEMPLATE / "review_question.yml").read_text(encoding="utf-8")
        required_terms = [
            "Phase movement",
            "Question",
            "Impact If Unanswered",
            "Needed By",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, content)


if __name__ == "__main__":
    unittest.main()
