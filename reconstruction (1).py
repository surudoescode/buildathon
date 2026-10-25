import json
import os
from pathlib import Path
from typing import Dict, Any

from engine.rules import RuleManager
from engine.behaviors import BehaviorExecutor
from engine.renderer import BlueprintRenderer
from engine.generator import CodeGenerator

ROOT = Path(__file__).resolve().parent

class PhoenixReconstructor:
    def __init__(self, blueprint_path: str = None, rules_path: str = None):
        self.blueprint_path = blueprint_path or str(ROOT / "data" / "blueprint.json")
        self.rules_path = rules_path or str(ROOT / "data" / "rules.json")
        self.rule_manager = RuleManager(self.rules_path)
        self.blueprint = self._load_blueprint()

    def _load_blueprint(self) -> Dict[str, Any]:
        if not os.path.exists(self.blueprint_path):
            raise FileNotFoundError(f"Blueprint missing at: {self.blueprint_path}")
        with open(self.blueprint_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def execute(self, inputs: Dict[str, Any], version: str = None) -> Dict[str, Any]:
        """Used by test_runner.py and app.py for dynamic candidate execution."""
        target_version = version or self.rule_manager.get_active_version()
        config = self.rule_manager.get_rule_config(target_version)
        executor = BehaviorExecutor(config)
        return executor.execute_action("calculate_invoice", inputs)

    def export_application(self, version: str = None, output_path: str = "generated_app.py") -> str:
        """Compiles standalone code to disk."""
        target_version = version or self.rule_manager.get_active_version()
        config = self.rule_manager.get_rule_config(target_version)
        code = CodeGenerator.generate_standalone_script(self.blueprint, config)
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(code)
        return code

# Backwards-compatible procedural export matching the GitHub repo's intent
def reconstruct(blueprint_path=None, rules_path=None, output_path="generated_app.py"):
    recon = PhoenixReconstructor(blueprint_path, rules_path)
    return recon.export_application(output_path=output_path)
