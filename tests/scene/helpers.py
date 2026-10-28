"""Shared helpers for the scene skill tests. Scripts run as a user would run them."""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKILL = os.path.join(ROOT, "skills", "core", "marso-scene-decompose")
SCRIPTS = os.path.join(SKILL, "scripts")


def script_dirs(script):
    """The scripts/ folder holding `script`, as a list for tests that loop over copies."""
    return [SCRIPTS] if os.path.exists(os.path.join(SCRIPTS, script)) else []


def run(script, *args, cwd=None, env=None):
    """Run a Python script; return (exit code, stdout, stderr)."""
    result = subprocess.run([sys.executable, script, *args], capture_output=True, text=True,
                            encoding="utf-8", errors="replace", cwd=cwd, env=env)
    return result.returncode, result.stdout, result.stderr


def run_json(script, *args, cwd=None, env=None):
    code, out, err = run(script, *args, cwd=cwd, env=env)
    try:
        return code, json.loads(out), err
    except json.JSONDecodeError:
        raise AssertionError(f"{os.path.basename(script)} did not print JSON.\nstdout: {out}\nstderr: {err}")
