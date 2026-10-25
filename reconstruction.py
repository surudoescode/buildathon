# reconstruction.py
from pathlib import Path
from typing import Dict, Any

from engine.blueprint import load_blueprint, validate_blueprint
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
        
        # Uses your engine's blueprint loader and validator
        self.blueprint = load_blueprint(self.blueprint_path)
        validate_blueprint(self.blueprint)

    def execute(self, inputs: Dict[str, Any], version: str = None) -> Dict[str, Any]:
        """In-memory candidate execution for live dashboard and test runner."""
        target_version = version or self.rule_manager.get_active_version()
        config = self.rule_manager.get_rule_config(target_version)
        executor = BehaviorExecutor(config)
        return executor.execute_action("calculate_invoice", inputs)

    def export_application(self, version: str = None, output_path: str = "generated_app.py") -> str:
        """Standalone code generator matching the GitHub repo logic."""
        target_version = version or self.rule_manager.get_active_version()
        config = self.rule_manager.get_rule_config(target_version)
        code = CodeGenerator.generate_standalone_script(self.blueprint, config)
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(code)
        return code

# Procedural function so tests or scripts importing reconstruct() continue working
def reconstruct(blueprint_path=ROOT / "data" / "blueprint.json", 
                rules_path=ROOT / "data" / "rules.json", 
                output_path=ROOT / "generated_app.py"):
    recon = PhoenixReconstructor(str(blueprint_path), str(rules_path))
    return recon.export_application(output_path=str(output_path))

if __name__ == "__main__":
    out = reconstruct()
    print(f"Generated standalone code: {out}")
