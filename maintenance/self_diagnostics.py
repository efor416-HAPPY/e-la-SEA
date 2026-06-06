# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import ast
import json
import time

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run_integrity_check():
    """Runs verify_integrity.ps1 and parses the outcome."""
    ps_file = os.path.join(WORKSPACE_DIR, "verify_integrity.ps1")
    if not os.path.exists(ps_file):
        return {"status": "fail", "message": "verify_integrity.ps1 is missing in workspace root."}
    
    try:
        # Run powershell script
        cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", ps_file]
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=WORKSPACE_DIR, timeout=25)
        
        output = res.stdout
        is_success = "VERIFICATION RESULT: SUCCESS" in output
        
        return {
            "status": "success" if is_success else "fail",
            "log": output,
            "error_log": res.stderr
        }
    except Exception as e:
        return {"status": "fail", "message": f"PowerShell runner failed: {str(e)}"}

def parse_python_file(full_path, rel_path):
    """Parses a single python file and returns error info if failed, or None."""
    try:
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()
        ast.parse(source, filename=rel_path)
        return None
    except SyntaxError as se:
        return {
            "file": rel_path,
            "line": se.lineno,
            "offset": se.offset,
            "text": se.text.strip() if se.text else "",
            "error": str(se)
        }
    except Exception as e:
        return {
            "file": rel_path,
            "error": f"Failed to parse: {str(e)}"
        }

def scan_python_syntax():
    """Scans all Python scripts in the workspace for compile-time syntax errors."""
    errors = []
    skip_dirs = {'.claude', '.cursor', '.github', '.vibecheck', '.git', '__pycache__', '__pycache__', 'node_modules', 'maintenance'}
    
    for root, dirs, files in os.walk(WORKSPACE_DIR):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for file in files:
            if not file.endswith('.py'):
                continue
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, WORKSPACE_DIR)
            err = parse_python_file(full_path, rel_path)
            if err:
                errors.append(err)
                    
    return errors

def run_diagnostics():
    """Combines all diagnostic checks."""
    integrity = run_integrity_check()
    syntax_errors = scan_python_syntax()
    
    overall_health = "healthy"
    if integrity["status"] != "success" or len(syntax_errors) > 0:
        overall_health = "degraded"
        
    return {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "health": overall_health,
        "integrity": integrity,
        "syntax_errors": syntax_errors
    }

if __name__ == "__main__":
    report = run_diagnostics()
    print(json.dumps(report, ensure_ascii=False, indent=2))
