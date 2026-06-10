# -*- coding: utf-8 -*-
"""
✉️ ARA AI Message & Thought Structure
Message: Legacy structured payload for direct agent dispatch.
Thought: Cognitive unit for CognitiveBus pub/sub propagation (ARA 3.0).
"""

import json
import time
from typing import Any, Optional
from uuid import uuid4


# ============================================================================
# Legacy Message (backward compatible with existing AgentBus dispatch)
# ============================================================================

class Message:
    def __init__(self, source: str, target: str, action: str, payload: Any):
        self.source = source
        self.target = target
        self.action = action
        self.payload = payload

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "target": self.target,
            "action": self.action,
            "payload": self.payload
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        data = json.loads(json_str)
        return cls(
            source=data.get("source", ""),
            target=data.get("target", ""),
            action=data.get("action", ""),
            payload=data.get("payload", "")
        )

    def __repr__(self) -> str:
        return f"Message(source='{self.source}', target='{self.target}', action='{self.action}', payload={self.payload})"


# ============================================================================
# Thought — ARA 3.0 Cognitive Unit
# ============================================================================

# Thought types define the cognitive stage in the perception→action cycle
THOUGHT_TYPES = [
    "perception",    # 외부 자극 인지 (뉴스, 유튜브, 센서 등)
    "memory",        # 기억 검색/저장 결과
    "reasoning",     # 추론 과정/결론
    "plan",          # 계획 수립/단계
    "action",        # 실행 명령/결과
    "observation",   # 실행 결과 관찰
    "learning",      # 학습/기억 강화
    "emotion",       # 감정 상태 변화
    "dialogue",      # 사용자 대화
    "system",        # 시스템 내부 이벤트
]


class Thought:
    """
    아라의 인지 단위 (Cognitive Unit).
    CognitiveBus를 통해 에이전트 간 자동 전파되는 메시지 객체.
    
    인지 사이클:
        인지(perception) → 기억(memory) → 추론(reasoning)
        → 계획(plan) → 실행(action) → 관찰(observation)
        → 학습(learning) → 기억 강화
    """

    def __init__(
        self,
        source: str,
        thought_type: str,
        content: str,
        importance: float = 0.5,
        emotion: Optional[dict] = None,
        context: Optional[dict] = None,
        metadata: Optional[dict] = None,
        parent_id: Optional[str] = None,
    ):
        # Identity
        self.id: str = str(uuid4())
        self.parent_id: Optional[str] = parent_id  # 원인이 된 Thought의 ID (추론 체인)

        # Source & Type
        self.source: str = source              # 발신 에이전트 ID
        self.thought_type: str = thought_type  # THOUGHT_TYPES 중 하나

        # Core Content
        self.content: str = content            # 핵심 내용 (자연어)
        self.importance: float = max(0.0, min(1.0, importance))  # 0.0~1.0 정규화

        # Cognitive Context
        self.emotion: dict = emotion if emotion is not None else {}
        self.context: dict = context if context is not None else {}
        self.metadata: dict = metadata if metadata is not None else {}

        # Temporal
        self.timestamp: float = time.time()
        self.created_at: str = time.strftime('%Y-%m-%d %H:%M:%S')

        # Trace (CognitiveBus가 전파 경로를 추적)
        self.trace: list[str] = []  # [agent_id, ...] 순서대로 전파된 경로

        # Processing state
        self.processed: bool = False
        self.responses: list[dict] = []  # 에이전트들의 반응/응답 수집

    def add_trace(self, agent_id: str) -> None:
        """CognitiveBus가 전파 시 경로 기록."""
        if agent_id not in self.trace:
            self.trace.append(agent_id)

    def add_response(self, agent_id: str, response: Any) -> None:
        """에이전트가 처리 후 응답을 기록."""
        self.responses.append({
            "agent_id": agent_id,
            "response": response,
            "timestamp": time.time()
        })

    def derive(self, source: str, thought_type: str, content: str,
               importance: Optional[float] = None, **kwargs) -> 'Thought':
        """이 Thought에서 파생된 새 Thought를 생성 (추론 체인 추적)."""
        return Thought(
            source=source,
            thought_type=thought_type,
            content=content,
            importance=importance if importance is not None else self.importance,
            parent_id=self.id,
            emotion=kwargs.get("emotion", self.emotion.copy()),
            context=kwargs.get("context", {}),
            metadata=kwargs.get("metadata", {}),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "source": self.source,
            "thought_type": self.thought_type,
            "content": self.content,
            "importance": self.importance,
            "emotion": self.emotion,
            "context": self.context,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "created_at": self.created_at,
            "trace": self.trace,
            "processed": self.processed,
            "responses": self.responses,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)

    @classmethod
    def from_dict(cls, data: dict) -> 'Thought':
        thought = cls(
            source=data.get("source", ""),
            thought_type=data.get("thought_type", "system"),
            content=data.get("content", ""),
            importance=data.get("importance", 0.5),
            emotion=data.get("emotion"),
            context=data.get("context"),
            metadata=data.get("metadata"),
            parent_id=data.get("parent_id"),
        )
        thought.id = data.get("id", thought.id)
        thought.timestamp = data.get("timestamp", thought.timestamp)
        thought.created_at = data.get("created_at", thought.created_at)
        thought.trace = data.get("trace", [])
        thought.processed = data.get("processed", False)
        thought.responses = data.get("responses", [])
        return thought

    def __repr__(self) -> str:
        return (
            f"Thought(id='{self.id[:8]}…', source='{self.source}', "
            f"type='{self.thought_type}', importance={self.importance:.2f}, "
            f"content='{self.content[:30]}…')"
        )
