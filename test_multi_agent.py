# -*- coding: utf-8 -*-
"""
Verification Script for Multi-Agent ARA Core Redesign
Tests SQLite warm memory, safety checks, reasoning, planning, and asynchronous thread pool executions.
"""
import os
import sys
import json
import sqlite3
import time

# Import restructured module
from smart_resource_integrator import (
    AgentKernel, Goal, Task, SubTask, Action,
    MemoryAgent, SafetyAgent, ReasoningAgent, ExecutionAgent
)

def run_tests():
    print("==================================================")
    print("      ARA Core Multi-Agent Verification Test")
    print("==================================================")
    
    # 1. Test Tiered Memory Agent
    print("\n[테스트 1] 3계층 메모리 에이전트 검증...")
    mem_agent = MemoryAgent()
    
    # Clean warm memory table first for clean test
    if os.path.exists(mem_agent.warm_db.db_path):
        try:
            with sqlite3.connect(mem_agent.warm_db.db_path) as conn:
                conn.execute("DELETE FROM warm_wisdom")
                conn.commit()
        except Exception as e:
            print("Warm database cleanup failed:", e)

    test_item = {
        "title": "테스트 지식 항목",
        "link": "https://example.com/test-wisdom",
        "description": "멀티 에이전트와 3계층 메모리 구조의 연동 테스트입니다.",
        "source": "테스트 에이전트",
        "scraped_at": time.strftime('%Y-%m-%d %H:%M:%S'),
        "embedded_vector": json.dumps([0.1, 0.2, 0.3])
    }
    
    # Store item
    mem_agent.store_wisdom(test_item)
    
    # Verify stats
    hot, warm, cold = mem_agent.get_stats()
    print(f"  - Hot Cache 개수 (RAM): {hot} (기대값: 1)")
    print(f"  - Warm DB 개수 (SQLite): {warm} (기대값: 1)")
    print(f"  - Cold File 개수 (JSON): {cold} (기대값: 1이상)")
    
    assert hot == 1, "Hot memory 캐시 실패"
    assert warm == 1, "Warm memory SQLite 저장 실패"
    assert cold >= 1, "Cold memory JSON 저장 실패"
    print("✅ 3계층 메모리 테스트 성공!")

    # 2. Test Safety Agent Gates
    print("\n[테스트 2] 안전 에이전트 (Safety Gate) 검증...")
    safety_agent = SafetyAgent(allowed_paths=["./ara_input_data", "./downloads"])
    
    # Allowed delete
    safe_del_ok, _ = safety_agent.check_action_safety("DELETE", "./ara_input_data/sample.txt")
    print(f"  - 허용 디렉토리 내 삭제 검증: {safe_del_ok} (기대값: True)")
    assert safe_del_ok is True
    
    # Blocked delete (outside allowed paths)
    unsafe_del_ok, unsafe_reason = safety_agent.check_action_safety("DELETE", "C:/Windows/System32/kernel32.dll")
    print(f"  - 시스템 중요 파일 삭제 차단 검증: {not unsafe_del_ok} (차단 사유: {unsafe_reason})")
    assert unsafe_del_ok is False
    
    # Blocked shell command
    unsafe_shell_ok, cmd_reason = safety_agent.check_action_safety("SHELL_EXEC", "rm -rf /")
    print(f"  - 위험 쉘 명령어 차단 검증: {not unsafe_shell_ok} (차단 사유: {cmd_reason})")
    assert unsafe_shell_ok is False
    print("✅ 안전 통제 게이트 테스트 성공!")

    # 3. Test Reasoning & Planning Agents
    print("\n[테스트 3] 추론/계획 엔진 검증 (Goal -> Task -> SubTask -> Action)...")
    reasoning_agent = ReasoningAgent()
    goal = Goal("Analyze file input data from FileAgent")
    context = {"file_path": "./ara_input_data/raw_log.txt"}
    
    tasks = reasoning_agent.create_plan(goal, context)
    print(f"  - 생성된 대분류 태스크 개수: {len(tasks)}")
    assert len(tasks) > 0
    
    task = tasks[0]
    print(f"    ├─ Task: {task.title}")
    assert len(task.subtasks) > 0
    
    subtask = task.subtasks[0]
    print(f"    │  └─ SubTask: {subtask.title}")
    assert len(subtask.actions) > 0
    
    print("    │     └─ Actions:")
    for action in subtask.actions:
        print(f"            * [{action.action_type}] -> {action.target} ({action.details})")
        
    print("✅ 목표-계획 분해 엔진 테스트 성공!")

    # 4. Test Execution Agent with ThreadPool and Safety
    print("\n[테스트 4] 실행 에이전트 스레드 풀 및 안전 연동 검증...")
    exec_agent = ExecutionAgent(safety_agent, max_workers=4)
    
    execution_results = []
    def callback(success, msg):
        execution_results.append((success, msg))
        print(f"      [Callback] 성공: {success} | 메시지: {msg}")

    # Queue tasks for execution
    exec_agent.execute_plan(tasks, callback=callback)
    
    # Wait for execution threads to complete
    time.sleep(1.0)
    
    print(f"  - 실행된 총 액션 건수: {len(execution_results)}")
    assert len(execution_results) == 3
    for success, msg in execution_results:
        assert success is True, f"액션 실행 실패: {msg}"
        
    print("✅ 비동기 실행 및 스레드 풀 테스트 성공!")
    print("\n==================================================")
    print("       모든 통합 테스트가 성공적으로 완료되었습니다! 🎉")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
