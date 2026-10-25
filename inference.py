# inference.py
import os
import json
import uuid
from typing import List, Optional
from dotenv import load_dotenv

from schemas import (
    ApplicationBlueprint,
    BehaviorRule,
    BlueprintCorrection,
    FailureReport,
    ProcessedEvidence,
    RuleStatus,
    ScreenBlueprint,
    ScreenTransition,
    UIElement,
)

load_dotenv()


class PhoenixInferenceEngine:
    def __init__(self, api_key: Optional[str] = None, force_mock: bool = False):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.force_mock = force_mock or os.getenv("PHOENIX_USE_MOCK", "false").lower() == "true" or not self.api_key

    def generate_blueprint(self, evidence_list: List[ProcessedEvidence]) -> ApplicationBlueprint:
        """
        Converts processed evidence into a structured application blueprint.
        Falls back to deterministic mock logic when offline or in demo mode.
        """
        if self.force_mock:
            return self._mock_blueprint_generation(evidence_list)

        try:
            return self._live_llm_blueprint_generation(evidence_list)
        except Exception as e:
            print(f"[Inference Notice] Live LLM call failed ({e}). Falling back to honest demo mode.")
            fallback = self._mock_blueprint_generation(evidence_list)
            fallback.is_mock = True
            return fallback

    def suggest_correction(
        self,
        blueprint: ApplicationBlueprint,
        failure_report: FailureReport
    ) -> BlueprintCorrection:
        """
        Diagnoses verification failures from Member 4 and suggests blueprint fixes.
        """
        if self.force_mock:
            return self._mock_suggest_correction(failure_report)

        try:
            return self._live_llm_suggest_correction(blueprint, failure_report)
        except Exception as e:
            print(f"[Inference Notice] Live correction call failed ({e}). Falling back to demo mode.")
            fallback = self._mock_suggest_correction(failure_report)
            fallback.is_mock = True
            return fallback

    # --- Live AI Integration ---

    def _live_llm_blueprint_generation(self, evidence_list: List[ProcessedEvidence]) -> ApplicationBlueprint:
        serialized_evidence = [ev.model_dump() for ev in evidence_list]

        system_prompt = (
            "You are an AI software reconstruction architect. Given processed evidence (UI elements, "
            "detected text, and example I/O), reconstruct the application blueprint as valid JSON matching "
            "the ApplicationBlueprint schema. Correctly classify statuses as Observed, Inferred, Unknown, "
            "or Contradictory."
        )

        from google import genai
        client = genai.Client(api_key=self.api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{system_prompt}\n\nEvidence:\n{json.dumps(serialized_evidence, indent=2)}",
            config={"response_mime_type": "application/json"}
        )

        data = json.loads(response.text)
        return ApplicationBlueprint(**data, is_mock=False)

    def _live_llm_suggest_correction(
        self,
        blueprint: ApplicationBlueprint,
        failure_report: FailureReport
    ) -> BlueprintCorrection:
        prompt = (
            f"The application blueprint failed verification:\n"
            f"Failed test: {failure_report.model_dump_json()}\n"
            "Provide a correction in JSON format with proposal_id, target_rule_id, diagnosis, "
            "and corrected_parameters."
        )

        from google import genai
        client = genai.Client(api_key=self.api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )

        data = json.loads(response.text)
        return BlueprintCorrection(**data, is_mock=False)

    # --- Deterministic Mock Fallback Logic ---

    def _mock_blueprint_generation(self, evidence_list: List[ProcessedEvidence]) -> ApplicationBlueprint:
        evidence_ids = [e.evidence_id for e in evidence_list]

        # 1. Identify screens and elements from evidence
        screens = []
        ui_elements = []

        all_detected_elements = [el for ev in evidence_list for el in ev.detected_elements]
        has_login_fields = any("user" in str(el).lower() or "password" in str(el).lower() for el in all_detected_elements)
        has_button = any(el.get("type") == "button" for el in all_detected_elements)

        if has_login_fields or has_button:
            login_elements = []
            for el in all_detected_elements:
                login_elements.append(
                    UIElement(
                        element_id=f"elem-{uuid.uuid4().hex[:4]}",
                        element_type=el.get("type", "input_field"),
                        label=el.get("label", "Field"),
                        status=RuleStatus.OBSERVED,
                        supporting_evidence_ids=evidence_ids
                    )
                )
            screens.append(ScreenBlueprint(screen_id="SCREEN-LOGIN", title="Login Screen", elements=login_elements))

        # 2. Check for Contradictory Evidence
        # e.g., Same input yielding two mutually conflicting outputs in the evidence
        io_map = {}
        has_contradiction = False
        for ev in evidence_list:
            if ev.example_inputs and ev.example_outputs:
                inp_key = json.dumps(ev.example_inputs, sort_keys=True)
                if inp_key in io_map and io_map[inp_key] != ev.example_outputs:
                    has_contradiction = True
                io_map[inp_key] = ev.example_outputs

        rules = []
        transitions = []

        if has_contradiction:
            rules.append(
                BehaviorRule(
                    rule_id="RULE-AUTH-CONFLICT",
                    name="Conflicting Authentication Policy",
                    description="Identical credentials produce contradictory authentication outcomes across logs.",
                    status=RuleStatus.CONTRADICTORY,
                    supporting_evidence_ids=evidence_ids,
                    logic_type="auth_validation",
                    parameters={"conflict_detected": True},
                    confidence_score=0.1,
                    is_mock=True
                )
            )
        else:
            # 3. Normal / Inferred / Unknown Checks
            has_credentials_evidence = any(
                any("user" in str(k).lower() or "pass" in str(k).lower() for k in ev.example_inputs)
                for ev in evidence_list if ev.example_inputs
            )

            if has_credentials_evidence:
                rules.append(
                    BehaviorRule(
                        rule_id="RULE-AUTH-01",
                        name="Standard Login Verification",
                        description="Validates username and password and directs to dashboard.",
                        status=RuleStatus.INFERRED,
                        supporting_evidence_ids=evidence_ids,
                        logic_type="auth_validation",
                        parameters={"min_length": 6, "require_password": True},
                        confidence_score=0.92,
                        is_mock=True
                    )
                )
                transitions.append(
                    ScreenTransition(
                        transition_id="TRANS-01",
                        from_screen="SCREEN-LOGIN",
                        to_screen="SCREEN-DASHBOARD",
                        trigger_action="Submit Button Click",
                        condition="credentials_valid == True",
                        status=RuleStatus.INFERRED,
                        supporting_evidence_ids=evidence_ids
                    )
                )
            else:
                # Missing evidence scenario -> Mark behavior as Unknown
                rules.append(
                    BehaviorRule(
                        rule_id="RULE-AUTH-UNKNOWN",
                        name="Unknown Authentication Threshold",
                        description="Insufficient evidence to infer validation constraints.",
                        status=RuleStatus.UNKNOWN,
                        supporting_evidence_ids=[],
                        logic_type="auth_validation",
                        parameters={},
                        confidence_score=0.0,
                        is_mock=True
                    )
                )

        return ApplicationBlueprint(
            app_name="Phoenix Reconstructed Application",
            screens=screens,
            transitions=transitions,
            rules=rules,
            version="1.0.0",
            is_mock=True
        )

    def _mock_suggest_correction(self, failure_report: FailureReport) -> BlueprintCorrection:
        return BlueprintCorrection(
            proposal_id="PROP-REPAIR-01",
            target_rule_id="RULE-AUTH-01",
            diagnosis=(
                f"Mismatch on {failure_report.screen_or_workflow}: expected "
                f"{failure_report.expected}, got {failure_report.actual}. "
                "Adjusting validation constraint to accept valid legacy domain tokens."
            ),
            corrected_parameters={"min_length": 4, "allow_legacy_tokens": True},
            is_mock=True
        )
    