import pytest
from schemas import (
    FailureReport,
    ProcessedEvidence,
    RuleStatus,
)
from inference import PhoenixInferenceEngine


@pytest.fixture
def login_evidence():
    return [
        ProcessedEvidence(
            evidence_id="EV-UI-01",
            source_name="login_screen.png",
            screen_name="Login",
            detected_text=["Username", "Password", "Sign In"],
            detected_elements=[
                {"type": "input_field", "label": "username"},
                {"type": "input_field", "label": "password"},
                {"type": "button", "label": "Sign In"}
            ],
            example_inputs={"username": "admin", "password": "password123"},
            example_outputs={"authenticated": True}
        )
    ]


def test_1_identifies_login_fields_and_button(login_evidence):
    """Test 1: Verify engine detects login inputs and buttons."""
    engine = PhoenixInferenceEngine(force_mock=True)
    blueprint = engine.generate_blueprint(login_evidence)

    assert len(blueprint.screens) >= 1
    login_screen = blueprint.screens[0]
    element_types = [e.element_type for e in login_screen.elements]

    assert "input_field" in element_types
    assert "button" in element_types


def test_2_infers_workflow_and_transitions(login_evidence):
    """Test 2: Provide login examples and check inferred navigation and rules."""
    engine = PhoenixInferenceEngine(force_mock=True)
    blueprint = engine.generate_blueprint(login_evidence)

    assert len(blueprint.transitions) > 0
    transition = blueprint.transitions[0]
    assert transition.from_screen == "SCREEN-LOGIN"
    assert transition.status == RuleStatus.INFERRED

    rule = blueprint.rules[0]
    assert rule.status == RuleStatus.INFERRED
    assert rule.logic_type == "auth_validation"


def test_3_marks_missing_evidence_as_uncertain():
    """Test 3: Remove input/output evidence and check whether behavior is marked as UNKNOWN."""
    incomplete_evidence = [
        ProcessedEvidence(
            evidence_id="EV-SPARSE-01",
            source_name="corrupt_frame.png",
            detected_text=[],
            detected_elements=[],
            example_inputs={},
            example_outputs={}
        )
    ]

    engine = PhoenixInferenceEngine(force_mock=True)
    blueprint = engine.generate_blueprint(incomplete_evidence)

    uncertain_rule = next((r for r in blueprint.rules if r.status == RuleStatus.UNKNOWN), None)
    assert uncertain_rule is not None
    assert uncertain_rule.confidence_score == 0.0


def test_4_detects_contradictory_evidence():
    """Test 4: Provide conflicting examples for the same input and ensure conflict is reported."""
    conflicting_evidence = [
        ProcessedEvidence(
            evidence_id="EV-LOG-01",
            source_name="audit_log_1.txt",
            example_inputs={"user": "alice"},
            example_outputs={"status": "ALLOWED"}
        ),
        ProcessedEvidence(
            evidence_id="EV-LOG-02",
            source_name="audit_log_2.txt",
            example_inputs={"user": "alice"},
            example_outputs={"status": "DENIED"}
        )
    ]

    engine = PhoenixInferenceEngine(force_mock=True)
    blueprint = engine.generate_blueprint(conflicting_evidence)

    conflict_rule = next((r for r in blueprint.rules if r.status == RuleStatus.CONTRADICTORY), None)
    assert conflict_rule is not None
    assert conflict_rule.confidence_score < 0.5


def test_member_4_repair_proposal():
    """Verify repair suggestions when Member 4 sends a test failure."""
    engine = PhoenixInferenceEngine(force_mock=True)
    failure = FailureReport(
        test_id="TEST-FAIL-01",
        screen_or_workflow="Login Workflow",
        inputs={"username": "usr_token_old"},
        expected={"status": "ALLOWED"},
        actual={"status": "DENIED"},
        error_message="Legacy session token rejected."
    )

    correction = engine.suggest_correction(None, failure)
    assert "Adjusting validation constraint" in correction.diagnosis
    assert correction.corrected_parameters.get("allow_legacy_tokens") is True
    