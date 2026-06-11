# -*- coding: utf-8 -*-
"""
🧠 ARA AI Cognitive Agent: Planner Agent (ARA 3.0)
Subscribes to perception/reasoning topics and automatically generates
execution plans when complex goals or analyses are detected.
Connects to PlannerEngine for structured plan decomposition.
"""

from backend.agents.base_cognitive_agent import ICognitiveAgent
from backend.kernel.message import Message, Thought
from typing import Optional


class PlannerAgent(ICognitiveAgent):
    """인지 계획 에이전트. 복잡한 Thought가 들어오면 자동으로 계획을 세웁니다."""

    def __init__(self):
        super().__init__()

    def id(self) -> str:
        return "planner"

    def subscribed_topics(self) -> list[str]:
        return ["perception", "plan"]

    def initialize(self) -> bool:
        return True

    def on_thought(self, thought: Thought) -> Optional[Thought]:
        """
        인지(perception) Thought가 들어오면:
        - 중요도 0.7 이상이면 PlannerEngine으로 계획 수립
        - plan Thought는 실행 단계를 시작
        """
        if not self.kernel or not hasattr(self.kernel, 'planner_engine'):
            return None

        planner = self.kernel.planner_engine

        # 높은 중요도의 perception → 자동 계획 생성
        if thought.thought_type == "perception" and thought.importance >= 0.7:
            plan = planner.create_plan_from_thought(thought)

            # 에피소드 시작
            if hasattr(self.kernel.memory_core, 'episodic'):
                self.kernel.memory_core.episodic.begin_episode(
                    trigger=thought.content[:50],
                    episode_type="planning",
                    tags=["auto_plan", thought.source],
                )

            return thought.derive(
                source=self.id(),
                thought_type="plan",
                content=f"계획 수립: '{plan.goal}' → {len(plan.steps)}단계 ({plan.plan_type})",
                importance=0.6,
                context={
                    "plan_id": plan.id,
                    "plan_type": plan.plan_type,
                    "steps": [s.to_dict() for s in plan.steps],
                },
            )

        # plan Thought → 계획 상태 보고
        if thought.thought_type == "plan" and thought.context.get("plan_id"):
            plan_id = thought.context["plan_id"]
            plan_data = planner.get_plan(plan_id)
            if plan_data:
                return thought.derive(
                    source=self.id(),
                    thought_type="observation",
                    content=f"계획 '{plan_data['goal']}' 진행률: {plan_data['progress']*100:.0f}%",
                    importance=0.4,
                )

        return None

    def process(self, message: Message) -> bool:
        """Legacy AgentBus dispatch 호환."""
        if message.action == "plan":
            goal_desc = message.payload.get("goal_desc", "")
            context = message.payload.get("context", {})

            if self.kernel and hasattr(self.kernel, 'planner_engine'):
                plan = self.kernel.planner_engine.create_plan(goal_desc)
                if isinstance(message.payload, dict):
                    message.payload["result"] = plan.to_dict()
                return True

            # Fallback: legacy plan generation
            tasks = self._legacy_plan(goal_desc, context)
            if isinstance(message.payload, dict):
                message.payload["result"] = tasks
            return True
        return False

    def shutdown(self) -> None:
        pass

    def _legacy_plan(self, goal_desc: str, context: dict) -> list[dict]:
        """Legacy plan generation for backward compatibility."""
        desc = goal_desc.lower()
        if "analyze" in desc or "file" in desc:
            return [{"title": "파일 인지 및 데이터 프로세싱 작업", "subtasks": [
                {"title": "파일 검사 및 인지 변환", "actions": [
                    {"action_type": "READ", "target": context.get("file_path", ""), "details": "파일 콘텐츠 읽기"},
                    {"action_type": "STORE", "target": context.get("file_path", ""), "details": "메모리 저장"},
                ]}
            ]}]
        return [{"title": "시스템 정밀 진단", "subtasks": [
            {"title": "리소스 텔레메트리 스캔", "actions": [
                {"action_type": "SYS_TELEMETRY", "target": "CPU/RAM", "details": "부하 점검"},
            ]}
        ]}]


# Global Planner Agent Instance
planner_agent = PlannerAgent()
