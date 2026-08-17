from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PHASE0 = ROOT / "docs" / "phase-0"


REQUIRED_DOCS = [
    "README.md",
    "product-brief.md",
    "requirements.md",
    "architecture-baseline.md",
    "data-governance.md",
    "validation-plan.md",
    "roadmap.md",
    "acceptance-checklist.md",
    "phase-1-handoff.md",
    "decision-records.md",
    "phase-1-backlog.md",
    "review-questions.md",
    "cctv-environment.md",
]


REQUIRED_README_LINKS = [
    "product-brief.md",
    "requirements.md",
    "architecture-baseline.md",
    "data-governance.md",
    "validation-plan.md",
    "roadmap.md",
    "acceptance-checklist.md",
    "phase-1-handoff.md",
    "decision-records.md",
    "phase-1-backlog.md",
    "review-questions.md",
    "cctv-environment.md",
]


class Phase0DocsTests(unittest.TestCase):
    def test_required_phase0_documents_exist(self):
        for relative_path in REQUIRED_DOCS:
            with self.subTest(path=relative_path):
                path = PHASE0 / relative_path
                self.assertTrue(path.exists(), f"Missing Phase 0 document: {path}")
                self.assertGreater(path.stat().st_size, 200, f"Document is too small: {path}")

    def test_phase0_readme_links_core_documents(self):
        readme = (PHASE0 / "README.md").read_text(encoding="utf-8")
        for link in REQUIRED_README_LINKS:
            with self.subTest(link=link):
                self.assertIn(link, readme)

    def test_top_level_readme_links_phase0_index(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("docs/phase-0/README.md", readme)

    def test_acceptance_checklist_tracks_exit_review(self):
        checklist = (PHASE0 / "acceptance-checklist.md").read_text(encoding="utf-8")
        required_items = [
            "Review Phase 0 docs with project owner",
            "Confirm official challenge constraints",
            "phase-1-handoff.md",
            "phase-1-backlog.md",
            "decision-records.md",
            "Start camera registry backend implementation",
        ]
        for item in required_items:
            with self.subTest(item=item):
                self.assertIn(item, checklist)

    def test_phase1_handoff_names_camera_registry_seed(self):
        handoff = (PHASE0 / "phase-1-handoff.md").read_text(encoding="utf-8")
        required_terms = [
            "hcam.camera_registry.seed.v1",
            "Camera Registry",
            "FastAPI",
            "SQLite",
            "PostgreSQL",
            "No CCTV video is stored",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, handoff)

    def test_backlog_contains_first_registry_work(self):
        backlog = (PHASE0 / "phase-1-backlog.md").read_text(encoding="utf-8")
        required_items = [
            "HCAM-001",
            "HCAM-010",
            "HCAM-011",
            "HCAM-012",
            "HCAM-030",
        ]
        for item in required_items:
            with self.subTest(item=item):
                self.assertIn(item, backlog)


if __name__ == "__main__":
    unittest.main()
