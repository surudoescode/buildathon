# schemas.py
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RuleStatus(str, Enum):
    OBSERVED = "Observed"          # Directly witnessed in evidence
    INFERRED = "Inferred"          # Hypothesized by AI based on patterns
    UNKNOWN = "Unknown"            # Insufficient evidence
    CONTRADICTORY = "Contradictory"# Conflicting evidence points


class ProcessedEvidence(BaseModel):
    """Structured evidence received from Member 3 (OCR/Vision)."""
    evidence_id: str
    source_name: str
    screen_name: Optional[str] = None
    detected_text: List[str] = Field(default_factory=list)
    detected_elements: List[Dict[str, Any]] = Field(default_factory=list)  # e.g., [{"type": "button", "label": "Login"}]
    example_inputs: Dict[str, Any] = Field(default_factory=dict)
    example_outputs: Dict[str, Any] = Field(default_factory=dict)


class UIElement(BaseModel):
    element_id: str
    element_type: str  # "input_field", "button", "label", "table", "display"
    label: str
    status: RuleStatus = RuleStatus.OBSERVED
    supporting_evidence_ids: List[str] = Field(default_factory=list)


class ScreenBlueprint(BaseModel):
    screen_id: str
    title: str
    elements: List[UIElement] = Field(default_factory=list)


class ScreenTransition(BaseModel):
    transition_id: str
    from_screen: str
    to_screen: str
    trigger_action: str
    condition: Optional[str] = None
    status: RuleStatus = RuleStatus.INFERRED
    supporting_evidence_ids: List[str] = Field(default_factory=list)


class BehaviorRule(BaseModel):
    rule_id: str
    name: str
    description: str
    status: RuleStatus
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    logic_type: str  # e.g., "auth_validation", "discount_calculation", "form_navigation"
    parameters: Dict[str, Any] = Field(default_factory=dict)
    confidence_score: float = Field(ge=0.0, le=1.0)
    is_mock: bool = False


class ApplicationBlueprint(BaseModel):
    """The complete deliverable for Member 2 to render."""
    app_name: str
    screens: List[ScreenBlueprint] = Field(default_factory=list)
    transitions: List[ScreenTransition] = Field(default_factory=list)
    rules: List[BehaviorRule] = Field(default_factory=list)
    version: str = "1.0.0"
    is_mock: bool = False


class FailureReport(BaseModel):
    """Received from Member 4 during test verification."""
    test_id: str
    screen_or_workflow: str
    inputs: Dict[str, Any]
    expected: Dict[str, Any]
    actual: Dict[str, Any]
    error_message: str


class BlueprintCorrection(BaseModel):
    proposal_id: str
    target_rule_id: Optional[str] = None
    diagnosis: str
    corrected_parameters: Dict[str, Any] = Field(default_factory=dict)
    is_mock: bool = False
    