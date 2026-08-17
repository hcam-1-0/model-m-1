import io
from contextlib import redirect_stdout
import unittest

from tools import phase0_readiness


class Phase0ReadinessTests(unittest.TestCase):
    def test_parse_checklist_items_preserves_multiline_text(self):
        content = """# Checklist

- [x] Complete item.
- [ ] Confirm official challenge constraints and dataset rules before any
  sensitive integration.
- [ ] Start camera registry backend implementation after Phase 1 is approved.
"""
        items = phase0_readiness.parse_checklist_items(content)
        self.assertEqual(len(items), 3)
        self.assertTrue(items[0].checked)
        self.assertFalse(items[1].checked)
        self.assertEqual(
            items[1].text,
            "Confirm official challenge constraints and dataset rules before any sensitive integration.",
        )

    def test_build_readiness_report_has_no_automated_failures(self):
        report = phase0_readiness.build_readiness_report(run_validation=False)
        self.assertEqual(report.failures, 0)
        self.assertEqual(report.status, "ready_for_owner_review")
        self.assertEqual(report.manual_gates, 3)
        check_names = {check.name for check in report.checks}
        self.assertIn("manual_gate_artifacts", check_names)

    def test_acceptance_checklist_only_leaves_allowed_manual_gates(self):
        result = phase0_readiness.check_acceptance_checklist()
        self.assertEqual(result.status, phase0_readiness.MANUAL)
        for gate in result.evidence:
            with self.subTest(gate=gate):
                self.assertTrue(phase0_readiness.is_allowed_manual_gate(gate))

    def test_json_report_contains_machine_readable_status(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = phase0_readiness.main(["--json"])
        self.assertEqual(exit_code, 0)
        output = buffer.getvalue()
        self.assertIn('"status": "ready_for_owner_review"', output)
        self.assertIn('"name": "phase0_documents"', output)
        self.assertIn('"name": "manual_gate_artifacts"', output)

    def test_manual_gate_artifacts_are_present(self):
        result = phase0_readiness.check_manual_gate_artifacts()
        self.assertEqual(result.status, phase0_readiness.PASS)
        self.assertIn("owner-review.md", result.evidence[0])
        self.assertIn("official-constraints-intake.md", result.evidence[1])
        self.assertIn("manual-gate-issues.md", result.evidence[2])

    def test_strict_mode_fails_while_manual_gates_remain(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = phase0_readiness.main(["--strict"])
        self.assertEqual(exit_code, 2)


if __name__ == "__main__":
    unittest.main()
