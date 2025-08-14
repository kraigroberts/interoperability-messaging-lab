#!/usr/bin/env python3
"""
Quality check script for the Interoperability Messaging Lab.
Runs linting, type checking, and tests to ensure code quality.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n🔍 {description}")
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("✅ Success")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed (exit code: {e.returncode})")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False


def main() -> int:
    """Run all quality checks."""
    print("🚀 Interoperability Messaging Lab - Quality Check")
    print("=" * 60)
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    checks = [
        # Linting
        (["python3", "-m", "ruff", "check", "src/", "tests/", "cli.py"], "Ruff Linting"),
        
        # Type checking
        (["python3", "-m", "mypy", "src/", "--ignore-missing-imports"], "MyPy Type Checking"),
        
        # Tests
        (["python3", "-m", "pytest", "tests/", "-q"], "Unit Tests"),
        
        # Package build
        (["python3", "-m", "build"], "Package Build"),
    ]
    
    passed = 0
    total = len(checks)
    
    for cmd, description in checks:
        if run_command(cmd, description):
            passed += 1
        else:
            print(f"\n⚠️  {description} failed - continuing with other checks...")
    
    print("\n" + "=" * 60)
    print(f"📊 Quality Check Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All quality checks passed!")
        return 0
    else:
        print("❌ Some quality checks failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    import os
    sys.exit(main())
