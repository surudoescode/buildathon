from pathlib import Path
from engine.blueprint import load_blueprint, validate_blueprint
from engine.rules import load_rules
from engine.generator import generate_app

ROOT = Path(__file__).resolve().parent

def reconstruct(blueprint_path=ROOT / "data" / "blueprint.json",
                rules_path=ROOT / "data" / "rules.json",
                output_path=ROOT / "generated_app.py"):
    blueprint = load_blueprint(blueprint_path)
    validate_blueprint(blueprint)
    rules = load_rules(rules_path)
    return generate_app(blueprint, rules, output_path)

if __name__ == "__main__":
    output = reconstruct()
    print(f"Generated: {output}")
    print("Run with: py -m streamlit run generated_app.py")
