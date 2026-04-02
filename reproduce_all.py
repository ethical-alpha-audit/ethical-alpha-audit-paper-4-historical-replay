
import json
import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def run_step(label, cmd):
    print(f"=== {label} ===")
    result = subprocess.run(cmd, cwd=BASE_DIR, text=True)
    if result.returncode != 0:
        print(f"FAIL: {label}")
        sys.exit(result.returncode)
    print(f"OK: {label}")

def main():
    settings = json.loads((BASE_DIR / "config" / "harness_settings.json").read_text(encoding="utf-8"))
    os.environ["PYTHONHASHSEED"] = str(settings["python_hash_seed"])
    run_step("Notebook execution", [sys.executable, "scripts/notebook_runner.py"])
    run_step("Manifest generation", [sys.executable, "scripts/hash_manifest.py"])
    run_step("Output validation", [sys.executable, "scripts/validate_outputs.py"])
    run_step("HTML export", [sys.executable, "scripts/export_html.py"])
    print("ALL STEPS PASSED")

if __name__ == "__main__":
    main()
