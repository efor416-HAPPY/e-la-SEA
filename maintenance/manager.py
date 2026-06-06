# -*- coding: utf-8 -*-
import os
import sys
import shutil
import json
import time
import re

import self_diagnostics
import repair_agent

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAINTENANCE_DIR = os.path.join(WORKSPACE_DIR, 'maintenance')
BACKUPS_DIR = os.path.join(MAINTENANCE_DIR, 'backups')
LOGS_FILE = os.path.join(WORKSPACE_DIR, 'data', 'maintenance_log.json')

# Ensure directories exist
os.makedirs(BACKUPS_DIR, exist_ok=True)
os.makedirs(os.path.join(WORKSPACE_DIR, 'data'), exist_ok=True)

def find_target_file_from_message(message):
    """
    Scans the feedback message to find a file path in the workspace.
    Returns relative path if found, or None.
    """
    # Look for filenames like app.js, viewer.js, *.py
    matches = re.findall(r'([\w\-\./]+\.(?:js|py|html|css|json|ps1|yml))', message)
    for match in matches:
        # Clean up path
        clean_path = match.replace('/', os.sep).replace('\\', os.sep)
        # Try finding the file relative to workspace
        full_path = os.path.join(WORKSPACE_DIR, clean_path)
        if os.path.exists(full_path):
            return clean_path
            
        # Try search recursively in subfolders
        for root, dirs, files in os.walk(WORKSPACE_DIR):
            if clean_path in files:
                rel_path = os.path.relpath(os.path.join(root, clean_path), WORKSPACE_DIR)
                return rel_path
    return None

def write_log(entry):
    """Appends a maintenance log entry to maintenance_log.json."""
    logs = []
    if os.path.exists(LOGS_FILE):
        try:
            with open(LOGS_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except Exception:
            logs = []
            
    logs.insert(0, entry)  # Prepend newest logs
    
    try:
        with open(LOGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Failed to write log file:", e)

def prepare_repair_target(feedback):
    """Checks diagnostics, resolves target file and path, loads code and creates a backup."""
    report = self_diagnostics.run_diagnostics()
    target_file = find_target_file_from_message(feedback)
    if not target_file and report["syntax_errors"]:
        target_file = report["syntax_errors"][0]["file"]
        feedback = f"Fix syntax error in {target_file}: {report['syntax_errors'][0]['error']}. " + feedback

    if not target_file:
        return {
            "status": "error",
            "message": "수정할 대상 파일명을 찾지 못했습니다. 피드백 메시지에 수정하고자 하는 파일 이름(예: app.js, generate_excel.py)을 포함해 주십시오."
        }
        
    full_target_path = os.path.join(WORKSPACE_DIR, target_file)
    if not os.path.exists(full_target_path):
        return {
            "status": "error",
            "message": f"대상 파일 {target_file}을(를) 찾을 수 없습니다."
        }
        
    try:
        with open(full_target_path, 'r', encoding='utf-8', errors='ignore') as f:
            current_code = f.read()
    except Exception as e:
        return {
            "status": "error",
            "message": f"대상 파일 읽기 실패: {str(e)}"
        }
        
    timestamp = int(time.time())
    backup_filename = f"{os.path.basename(target_file)}.{timestamp}.bak"
    backup_path = os.path.join(BACKUPS_DIR, backup_filename)
    
    try:
        shutil.copy2(full_target_path, backup_path)
    except Exception as e:
        return {
            "status": "error",
            "message": f"백업 파일 생성 실패 (보호장치 오작동): {str(e)}"
        }
        
    return {
        "status": "ok",
        "target_file": target_file,
        "full_target_path": full_target_path,
        "backup_path": backup_path,
        "current_code": current_code,
        "feedback": feedback
    }

def perform_repair(feedback):
    """Orchestrates the entire repair, verification, and rollback lifecycle."""
    start_time = time.time()
    
    prep = prepare_repair_target(feedback)
    if prep["status"] == "error":
        return prep
        
    target_file = prep["target_file"]
    full_target_path = prep["full_target_path"]
    backup_path = prep["backup_path"]
    current_code = prep["current_code"]
    feedback = prep["feedback"]
        
    # 3. Call AI Repair Agent
    try:
        proposed_code = repair_agent.query_ollama_repair(target_file, current_code, feedback)
        if not proposed_code or len(proposed_code.strip()) == 0:
            raise ValueError("Ollama returned empty code.")
    except Exception as e:
        # Cleanup backup
        if os.path.exists(backup_path):
            os.remove(backup_path)
        return {
            "status": "error",
            "message": f"인공지능 코어 분석 및 패치 생성 실패: {str(e)}"
        }
        
    # 4. Write patch to target file
    try:
        with open(full_target_path, 'w', encoding='utf-8') as f:
            f.write(proposed_code)
    except Exception as e:
        # Restore immediately
        shutil.copy2(backup_path, full_target_path)
        os.remove(backup_path)
        return {
            "status": "error",
            "message": f"패치 코드 작성 실패: {str(e)}. 안전 복원을 수행했습니다."
        }
        
    # 5. Verify the patch (Self-Testing & Integrity Checks)
    verify_report = self_diagnostics.run_diagnostics()
    
    # Check if there are any syntax errors on the modified file, or if system integrity is degraded
    syntax_error_on_target = any(se["file"] == target_file for se in verify_report["syntax_errors"])
    integrity_failed = verify_report["integrity"]["status"] != "success"
    
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "feedback": feedback,
        "target_file": target_file,
        "backup_file": backup_path,
        "elapsed_seconds": round(time.time() - start_time, 2)
    }
    
    if syntax_error_on_target or integrity_failed:
        # ROLLBACK!
        try:
            shutil.copy2(backup_path, full_target_path)
            rollback_status = "Rollback Succeeded"
        except Exception as e:
            rollback_status = f"Rollback Failed: {str(e)}"
            
        os.remove(backup_path)
        
        # Determine failure details
        reasons = []
        if syntax_error_on_target:
            target_err = [se["error"] for se in verify_report["syntax_errors"] if se["file"] == target_file]
            reasons.append(f"구문 에러 검출: {', '.join(target_err)}")
        if integrity_failed:
            reasons.append("시스템 무결성 테스트 실패 (verify_integrity.ps1 PASS 실패)")
            
        log_entry.update({
            "status": "rolled_back",
            "reason": "; ".join(reasons),
            "rollback_status": rollback_status
        })
        write_log(log_entry)
        
        return {
            "status": "rollback",
            "message": f"안전 보호 장치 가동: AI 코드 수정 결과 검증 도중 오류가 검출되어 롤백을 수행했습니다. (사유: {'; '.join(reasons)})"
        }
    else:
        # COMMIT SUCCESS!
        os.remove(backup_path)
        log_entry.update({
            "status": "success",
            "message": "자가 진단 및 무결성 검증을 통과하여 패치가 정상 배포되었습니다."
        })
        write_log(log_entry)
        
        return {
            "status": "success",
            "message": f"축하합니다! {target_file} 파일 자율 수리 및 무결성 검증이 완료되어 안전하게 배포되었습니다."
        }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ARA Autonomous Maintenance Orchestrator")
    parser.add_argument("--diagnose", action="store_true", help="Run self-diagnostics report")
    parser.add_argument("--repair", type=str, help="Submit feedback message for self-healing repair")
    
    args = parser.parse_args()
    if args.diagnose:
        print(json.dumps(self_diagnostics.run_diagnostics(), ensure_ascii=False, indent=2))
    elif args.repair:
        print("[진행] 자율 유지보수 복구 엔진 가동 중...")
        result = perform_repair(args.repair)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        parser.print_help()
