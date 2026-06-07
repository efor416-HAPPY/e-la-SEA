# -*- coding: utf-8 -*-
"""
🧠 ARA AI Agent Layer: Planner Agent
Translates high-level User Goals into structural lists of Tasks, SubTasks, and executable Actions.
"""

class Action:
    def __init__(self, action_type: str, target: str, details=""):
        self.action_type = action_type  # READ, WRITE, COGNITIVE, MES_SYNC, ERP_QUERY, AUDIT
        self.target = target
        self.details = details

    def to_dict(self) -> dict:
        return {"action_type": self.action_type, "target": self.target, "details": self.details}

class SubTask:
    def __init__(self, title: str):
        self.title = title
        self.actions = []

    def to_dict(self) -> dict:
        return {"title": self.title, "actions": [a.to_dict() for a in self.actions]}

class Task:
    def __init__(self, title: str):
        self.title = title
        self.subtasks = []

    def to_dict(self) -> dict:
        return {"title": self.title, "subtasks": [st.to_dict() for st in self.subtasks]}

class PlannerAgent:
    """Decomposes goals into hierarchical structures for autonomous agents."""
    
    def generate_plan(self, goal_desc: str, context: dict) -> list[Task]:
        tasks = []
        desc = goal_desc.lower()

        if "analyze" in desc or "file" in desc:
            t = Task("파일 인지 및 데이터 프로세싱 작업")
            st = SubTask("파일 검사 및 인지 변환")
            st.actions.append(Action("READ", context.get("file_path", ""), "파일 콘텐츠 안전한 읽기"))
            st.actions.append(Action("PARSE", context.get("file_path", ""), "데이터 파싱 및 특징 추출"))
            st.actions.append(Action("STORE", context.get("file_path", ""), "3계층 메모리 저장"))
            t.subtasks.append(st)
            tasks.append(t)
            
        elif "sync" in desc or "mes" in desc or "erp" in desc:
            t = Task("제조 정보 및 자원 동기화 작업")
            st = SubTask("설비 실적 데이터 수집 및 MES 송신")
            st.actions.append(Action("MES_SYNC", "MES_ACTUAL_RECORD", "생산 실적 동기화"))
            st.actions.append(Action("ERP_QUERY", "PART_NO_V01", "재고 정보 실시간 조회"))
            st.actions.append(Action("AUDIT", "manufacturing_audit.log", "감사 로그 작성"))
            t.subtasks.append(st)
            tasks.append(t)
            
        else:
            t = Task("시스템 정밀 진단")
            st = SubTask("리소스 텔레메트리 스캔")
            st.actions.append(Action("SYS_TELEMETRY", "CPU/RAM", "하드웨어 부하 상태 점검"))
            t.subtasks.append(st)
            tasks.append(t)
            
        return tasks

# Global Planner Agent
planner_agent = PlannerAgent()
