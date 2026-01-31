import os
import subprocess
import sys


def check_tool(tool_name):
    try:
        subprocess.run(
            [tool_name, "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=True,
        )
        return True
    except:
        return False


def run_scan():
    print("=== NEURAXIS Security Scanner ===")

    # Check dependencies
    # Using 'safety' and 'bandit'

    # 1. Dependency Scan
    print("\n[1/2] Scanning Dependencies (Safety)...")
    safety_code = subprocess.call("safety check", shell=True)

    if safety_code != 0:
        print("WARNING: Vulnerabilities found in dependencies.")
    else:
        print("PASS: Dependencies look clean.")

    # 2. Static Analysis (SAST)
    print("\n[2/2] Scanning Codebase (Bandit)...")
    # -r: recursive, -ll: level (medium/high), -x: exclude tests
    bandit_cmd = "bandit -r app -x tests -ll"
    bandit_code = subprocess.call(bandit_cmd, shell=True)

    if bandit_code != 0:
        print("FAILURE: Security issues found in code (High/Medium Severity).")
        sys.exit(1)
    else:
        print("PASS: Code analysis passed.")


if __name__ == "__main__":
    # Ensure run from correct directory logic or just run
    run_scan()
