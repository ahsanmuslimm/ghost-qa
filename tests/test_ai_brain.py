import json
import pytest
from app.services.ai_brain import AIBrainService
from app.schemas.test_schemas import TestStepSchema


class TestAITestGeneration:
    def test_valid_response(self):
        """AI should generate valid test cases."""
        ai = AIBrainService()
        result = ai.generate_tests(
            pr_title="Add login endpoint",
            pr_body="Implements JWT-based login for users",
            diff="+ def login(email, password): ...",
            changed_files=["src/auth/login.py"],
            linked_issue={"title": "Login feature", "body": "Add auth"},
            existing_tests=["tests/test_auth.py"]
        )
        assert len(result.tests) == 5
        for test in result.tests:
            assert test.id is not None
            assert len(test.title) > 0
            assert len(test.steps) > 0
            assert test.risk_level is not None

    def test_test_types_valid(self):
        """Test types should be valid enum values."""
        ai = AIBrainService()
        result = ai.generate_tests(
            pr_title="Test", pr_body="Test body", diff="test",
            changed_files=["a.py"], existing_tests=[]
        )
        for test in result.tests:
            assert test.type.value in ("functional", "regression", "edge_case", "integration")

    def test_priorities_valid(self):
        """Priorities should be valid enum values."""
        ai = AIBrainService()
        result = ai.generate_tests(
            pr_title="Test", pr_body="Test body", diff="test",
            changed_files=["a.py"], existing_tests=[]
        )
        for test in result.tests:
            assert test.priority.value in ("p0_critical", "p1_high", "p2_medium", "p3_low")

    def test_malformed_response_handling(self):
        """Malformed JSON should raise an error, not crash."""
        ai = AIBrainService()
        # Force a non-demo call would fail, but in demo mode we test the parser
        try:
            parsed = ai._parse_json("not valid json {{{")
            assert False, "Should have raised"
        except (ValueError, json.JSONDecodeError):
            pass

    def test_steps_validation(self):
        """Each test step should have required fields."""
        ai = AIBrainService()
        result = ai.generate_tests(
            pr_title="Test", pr_body="Test", diff="test",
            changed_files=["a.py"], existing_tests=[]
        )
        for test in result.tests:
            for step in test.steps:
                assert hasattr(step, "action")
                assert step.action is not None
