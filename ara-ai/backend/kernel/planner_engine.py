# -*- coding: utf-8 -*-
"""
🗓️ ARA AI Planner Engine (ARA 3.0)
Goal-oriented planning with execution tracking, observation feedback, and learning.

Planning lifecycle:
    Goal → Plan → Steps → Execute → Observe → Adapt → Learn

Unlike the legacy PlannerAgent (if/elif branching), this engine:
  - Decomposes goals into executable step chains
  - Tracks execution state per step
  - Observes results and adapts remaining steps
  - Records completed plans as episodes for future reasoning
"""

import time
import threading
from typing import Optional, Any
from uuid import uuid4
from backend.kernel.message import Thought


# ============================================================================
# Plan Data Structures
# ============================================================================

class PlanStep:
    """계획의 개별 실행 단계."""

    def __init__(self, title: str, action_type: str, target: str, details: str = ""):
        self.id = str(uuid4())[:8]
        self.title = title
        self.action_type = action_type   # SEARCH, ANALYZE, COLLECT, STORE, NOTIFY, REASON
        self.target = target
        self.details = details
        self.status = "pending"          # pending, running, completed, failed, skipped
        self.result: Optional[Any] = None
        self.error: Optional[str] = None
        self.started_at: Optional[float] = None
        self.completed_at: Optional[float] = None

    def start(self) -> None:
        self.status = "running"
        self.started_at = time.time()

    def complete(self, result: Any = None) -> None:
        self.status = "completed"
        self.result = result
        self.completed_at = time.time()

    def fail(self, error: str) -> None:
        self.status = "failed"
        self.error = error
        self.completed_at = time.time()

    @property
    def duration(self) -> float:
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "action_type": self.action_type,
            "target": self.target,
            "details": self.details,
            "status": self.status,
            "result": str(self.result) if self.result else None,
            "error": self.error,
            "duration": self.duration,
        }


class Plan:
    """목표 달성을 위한 단계별 계획."""

    def __init__(self, goal: str, plan_type: str = "analysis"):
        self.id = f"plan_{int(time.time() * 1000)}"
        self.goal = goal
        self.plan_type = plan_type
        self.steps: list[PlanStep] = []
        self.status = "created"  # created, executing, completed, failed, adapted
        self.created_at = time.time()
        self.completed_at: Optional[float] = None
        self.adaptations: list[str] = []  # 계획 수정 이력

    def add_step(self, title: str, action_type: str, target: str, details: str = "") -> PlanStep:
        step = PlanStep(title=title, action_type=action_type, target=target, details=details)
        self.steps.append(step)
        return step

    @property
    def current_step_index(self) -> int:
        for i, step in enumerate(self.steps):
            if step.status in ("pending", "running"):
                return i
        return len(self.steps)

    @property
    def progress(self) -> float:
        if not self.steps:
            return 0.0
        completed = sum(1 for s in self.steps if s.status in ("completed", "skipped"))
        return completed / len(self.steps)

    @property
    def is_complete(self) -> bool:
        return all(s.status in ("completed", "skipped", "failed") for s in self.steps)

    @property
    def is_successful(self) -> bool:
        return all(s.status in ("completed", "skipped") for s in self.steps)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "goal": self.goal,
            "plan_type": self.plan_type,
            "status": self.status,
            "progress": self.progress,
            "steps": [s.to_dict() for s in self.steps],
            "adaptations": self.adaptations,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }


# ============================================================================
# PlannerEngine
# ============================================================================

class PlannerEngine:
    """
    아라의 계획 엔진.
    목표를 단계별 계획으로 분해하고, 실행 → 관찰 → 적응 → 학습 사이클을 관리합니다.
    """

    def __init__(self):
        self.active_plans: dict[str, Plan] = {}
        self.completed_plans: list[Plan] = []
        self._lock = threading.Lock()
        self._max_completed = 100

        # Goal decomposition templates
        self._templates: dict[str, list[dict]] = {
            "economy_analysis": [
                {"title": "경제 뉴스 수집", "action_type": "COLLECT", "target": "news", "details": "최신 경제 뉴스 스크랩"},
                {"title": "금리 데이터 조회", "action_type": "SEARCH", "target": "economy", "details": "현재 금리/환율 데이터"},
                {"title": "과거 기록 검색", "action_type": "SEARCH", "target": "memory", "details": "관련 과거 분석 기록"},
                {"title": "통합 분석", "action_type": "REASON", "target": "reasoning", "details": "수집 데이터 종합 분석"},
                {"title": "결과 저장", "action_type": "STORE", "target": "memory", "details": "분석 결과 기억 저장"},
            ],
            "content_analysis": [
                {"title": "콘텐츠 수집", "action_type": "COLLECT", "target": "collector", "details": "대상 콘텐츠 수집"},
                {"title": "텍스트 추출", "action_type": "ANALYZE", "target": "parser", "details": "핵심 내용 추출"},
                {"title": "기억 검색", "action_type": "SEARCH", "target": "memory", "details": "관련 기존 지식 검색"},
                {"title": "분석 수행", "action_type": "REASON", "target": "reasoning", "details": "맥락 기반 분석"},
                {"title": "결과 저장", "action_type": "STORE", "target": "memory", "details": "분석 결과 저장"},
            ],
            "dialogue": [
                {"title": "대화 맥락 파악", "action_type": "SEARCH", "target": "memory", "details": "이전 대화 기록 검색"},
                {"title": "추론 수행", "action_type": "REASON", "target": "reasoning", "details": "응답 생성"},
                {"title": "대화 기록", "action_type": "STORE", "target": "memory", "details": "대화 내용 기억"},
            ],
            "general": [
                {"title": "정보 수집", "action_type": "COLLECT", "target": "general", "details": "관련 정보 수집"},
                {"title": "분석", "action_type": "REASON", "target": "reasoning", "details": "수집 정보 분석"},
                {"title": "결과 저장", "action_type": "STORE", "target": "memory", "details": "결과 저장"},
            ],
        }

    # =========================================================================
    # Plan Creation
    # =========================================================================

    def create_plan(self, goal: str, context: dict = None) -> Plan:
        """
        목표를 분석하고 실행 가능한 계획을 생성합니다.
        """
        plan_type = self._classify_goal(goal)
        plan = Plan(goal=goal, plan_type=plan_type)

        # 템플릿에서 단계 생성
        template = self._templates.get(plan_type, self._templates["general"])
        for step_def in template:
            plan.add_step(**step_def)

        with self._lock:
            self.active_plans[plan.id] = plan

        return plan

    def create_plan_from_thought(self, thought: Thought) -> Plan:
        """Thought에서 계획을 자동 생성합니다."""
        goal = thought.content
        context = thought.context
        plan = self.create_plan(goal, context)

        # Thought의 중요도에 따라 계획 우선순위 조정
        if thought.importance > 0.8:
            plan.plan_type = f"high_priority_{plan.plan_type}"

        return plan

    def _classify_goal(self, goal: str) -> str:
        """목표 텍스트를 분석하여 계획 유형을 분류합니다."""
        goal_lower = goal.lower()

        economy_keywords = ["금", "금리", "달러", "경제", "주식", "환율", "인플레이션", "투자", "시장"]
        dialogue_keywords = ["대화", "말해", "알려", "설명"]
        content_keywords = ["분석", "요약", "리뷰", "정리", "pdf", "문서", "영상"]

        if any(kw in goal_lower for kw in economy_keywords):
            return "economy_analysis"
        if any(kw in goal_lower for kw in content_keywords):
            return "content_analysis"
        if any(kw in goal_lower for kw in dialogue_keywords):
            return "dialogue"
        return "general"

    # =========================================================================
    # Plan Execution
    # =========================================================================

    def execute_step(self, plan_id: str, step_index: int = None) -> Optional[PlanStep]:
        """계획의 다음 단계를 실행합니다."""
        with self._lock:
            plan = self.active_plans.get(plan_id)
            if not plan:
                return None

            if plan.status != "executing":
                plan.status = "executing"

            idx = step_index if step_index is not None else plan.current_step_index
            if idx >= len(plan.steps):
                return None

            step = plan.steps[idx]

        step.start()
        return step

    def complete_step(self, plan_id: str, step_id: str, result: Any = None) -> None:
        """단계 완료를 기록합니다."""
        with self._lock:
            plan = self.active_plans.get(plan_id)
            if not plan:
                return

            for step in plan.steps:
                if step.id == step_id:
                    step.complete(result)
                    break

            # 모든 단계 완료 확인
            if plan.is_complete:
                plan.status = "completed" if plan.is_successful else "failed"
                plan.completed_at = time.time()
                self.completed_plans.append(plan)
                del self.active_plans[plan_id]

                # 완료 계획 수 제한
                if len(self.completed_plans) > self._max_completed:
                    self.completed_plans.pop(0)

    def fail_step(self, plan_id: str, step_id: str, error: str) -> None:
        """단계 실패를 기록합니다."""
        with self._lock:
            plan = self.active_plans.get(plan_id)
            if not plan:
                return
            for step in plan.steps:
                if step.id == step_id:
                    step.fail(error)
                    break

    # =========================================================================
    # Observation & Adaptation
    # =========================================================================

    def observe_result(self, plan_id: str, observation: str) -> None:
        """실행 결과를 관찰하고 기록합니다."""
        with self._lock:
            plan = self.active_plans.get(plan_id)
            if plan:
                plan.adaptations.append(f"[관찰] {observation}")

    def adapt_plan(self, plan_id: str, reason: str, new_steps: list[dict] = None) -> None:
        """관찰 결과에 따라 계획을 수정합니다."""
        with self._lock:
            plan = self.active_plans.get(plan_id)
            if not plan:
                return

            plan.status = "adapted"
            plan.adaptations.append(f"[적응] {reason}")

            # 새 단계 추가
            if new_steps:
                for step_def in new_steps:
                    plan.add_step(**step_def)

    # =========================================================================
    # Query
    # =========================================================================

    def get_active_plans(self) -> list[dict]:
        with self._lock:
            return [p.to_dict() for p in self.active_plans.values()]

    def get_plan(self, plan_id: str) -> Optional[dict]:
        with self._lock:
            plan = self.active_plans.get(plan_id)
            if plan:
                return plan.to_dict()
            # 완료된 계획에서도 검색
            for p in self.completed_plans:
                if p.id == plan_id:
                    return p.to_dict()
            return None

    def get_stats(self) -> dict:
        with self._lock:
            return {
                "active_plans": len(self.active_plans),
                "completed_plans": len(self.completed_plans),
                "successful": sum(1 for p in self.completed_plans if p.is_successful),
                "failed": sum(1 for p in self.completed_plans if not p.is_successful),
            }

    def __repr__(self) -> str:
        return f"PlannerEngine(active={len(self.active_plans)}, completed={len(self.completed_plans)})"
