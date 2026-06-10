# -*- coding: utf-8 -*-
"""
💖 ARA AI Emotion Engine (ARA 3.0)
Models ARA's internal emotional state that influences reasoning and responses.

Emotional dimensions:
  - curiosity   (탐구심)  : 새로운 정보에 대한 관심
  - confidence  (확신)    : 현재 추론/응답에 대한 자신감
  - attention   (주의력)  : 현재 작업에 대한 집중도
  - fatigue     (피로도)  : 시스템/인지 피로
  - empathy     (공감)    : 사용자에 대한 감정적 공명

Emotion affects:
  - Response tone and style
  - Reasoning depth (high curiosity → deeper analysis)
  - Task prioritization (high attention → focused work)
  - Memory importance weighting
"""

import time
import math
import threading
from typing import Optional
from backend.kernel.message import Thought


class EmotionEngine:
    """
    아라의 감정 엔진.
    내부 감정 상태가 추론, 응답 톤, 기억 중요도에 영향을 줍니다.
    """

    def __init__(self):
        # =====================================================================
        # Emotional State Vector (0.0 ~ 1.0)
        # =====================================================================
        self.state: dict[str, float] = {
            "curiosity": 0.5,      # 탐구심
            "confidence": 0.5,     # 확신
            "attention": 0.5,      # 주의력
            "fatigue": 0.0,        # 피로도
            "empathy": 0.5,        # 공감
        }

        # =====================================================================
        # Configuration
        # =====================================================================
        self._decay_rate = 0.02     # 시간에 따른 감정 안정화 속도
        self._baseline = {          # 감정의 기본(안정) 수준
            "curiosity": 0.5,
            "confidence": 0.5,
            "attention": 0.5,
            "fatigue": 0.0,
            "empathy": 0.5,
        }

        # Thought type → emotion influence mapping
        self._influence_map: dict[str, dict[str, float]] = {
            "perception": {"curiosity": +0.15, "attention": +0.10},
            "memory":     {"confidence": +0.05},
            "reasoning":  {"confidence": +0.10, "fatigue": +0.05, "curiosity": -0.05},
            "plan":       {"attention": +0.10, "confidence": +0.05},
            "action":     {"fatigue": +0.08},
            "observation": {"curiosity": +0.05, "confidence": +0.05},
            "learning":   {"curiosity": +0.10, "confidence": +0.05, "fatigue": -0.05},
            "dialogue":   {"empathy": +0.15, "attention": +0.10},
            "emotion":    {},  # Meta: emotions about emotions
            "system":     {"fatigue": +0.02},
        }

        # Keywords that amplify emotional response
        self._amplifiers: dict[str, dict[str, float]] = {
            # 긍정적 키워드 → empathy/confidence 증가
            "감사": {"empathy": +0.20, "confidence": +0.10},
            "좋아": {"empathy": +0.15, "confidence": +0.05},
            "최고": {"empathy": +0.15, "confidence": +0.10},
            "도움": {"empathy": +0.20},
            # 부정적 키워드 → empathy 증가, confidence 감소
            "슬퍼": {"empathy": +0.25, "confidence": -0.05},
            "힘들": {"empathy": +0.25, "fatigue": +0.05},
            "화나": {"empathy": +0.20, "attention": +0.15},
            # 지적 자극 → curiosity 증가
            "분석": {"curiosity": +0.20, "attention": +0.15},
            "왜": {"curiosity": +0.15},
            "어떻게": {"curiosity": +0.15, "attention": +0.10},
            "전망": {"curiosity": +0.20},
            "예측": {"curiosity": +0.20, "confidence": -0.05},
        }

        self._lock = threading.Lock()
        self._last_update = time.time()

    # =========================================================================
    # Emotion Update
    # =========================================================================

    def update(self, thought: Thought) -> dict[str, float]:
        """
        Thought에 따라 감정 상태를 갱신합니다.
        반환값: 각 감정 차원의 변화량 {"curiosity": +0.15, ...}
        """
        with self._lock:
            changes: dict[str, float] = {}

            # 1. Thought type 기반 영향
            type_influence = self._influence_map.get(thought.thought_type, {})
            for dim, delta in type_influence.items():
                # 중요도에 비례하여 감정 변화 크기 조정
                scaled_delta = delta * (0.5 + thought.importance)
                changes[dim] = changes.get(dim, 0) + scaled_delta

            # 2. 키워드 기반 감정 증폭
            content_lower = thought.content.lower()
            for keyword, amplification in self._amplifiers.items():
                if keyword in content_lower:
                    for dim, delta in amplification.items():
                        changes[dim] = changes.get(dim, 0) + delta

            # 3. Thought에 명시적 emotion이 있으면 반영
            if thought.emotion:
                for dim, value in thought.emotion.items():
                    if dim in self.state:
                        changes[dim] = changes.get(dim, 0) + value * 0.3

            # 4. 상태 적용
            for dim, delta in changes.items():
                if dim in self.state:
                    self.state[dim] = max(0.0, min(1.0, self.state[dim] + delta))

            self._last_update = time.time()
            return changes

    def decay(self) -> None:
        """시간에 따라 감정을 기본 상태로 안정화합니다."""
        with self._lock:
            elapsed = time.time() - self._last_update
            # 10초마다 decay_rate만큼 기본값으로 수렴
            decay_steps = elapsed / 10.0

            for dim in self.state:
                baseline = self._baseline[dim]
                current = self.state[dim]
                diff = baseline - current
                # 지수적 수렴
                self.state[dim] += diff * (1 - math.exp(-self._decay_rate * decay_steps))

            self._last_update = time.time()

    # =========================================================================
    # Response Modulation
    # =========================================================================

    def modulate_response(self, text: str) -> str:
        """
        현재 감정 상태에 따라 응답 톤을 조절합니다.
        """
        with self._lock:
            curiosity = self.state["curiosity"]
            empathy = self.state["empathy"]
            confidence = self.state["confidence"]
            fatigue = self.state["fatigue"]

        # 높은 공감 → 따뜻한 톤 추가
        if empathy > 0.7 and not text.endswith("🌱"):
            text = text.rstrip(".。") + " 🌱"

        # 높은 피로 → 간결한 응답 선호 (긴 응답 뒤에 휴식 메시지)
        if fatigue > 0.8:
            text += "\n\n(아라가 잠시 에너지를 충전하고 있어요 🍃)"

        # 높은 탐구심 → 추가 분석 제안
        if curiosity > 0.8 and len(text) > 50:
            text += "\n\n💡 더 깊이 분석해드릴까요?"

        return text

    def get_emotional_context(self) -> dict:
        """현재 감정 상태를 추론 맥락으로 반환합니다."""
        with self._lock:
            state_copy = self.state.copy()

        # 감정 상태를 자연어 설명으로
        dominant = max(state_copy, key=state_copy.get)
        descriptions = {
            "curiosity": "탐구적인",
            "confidence": "확신에 찬",
            "attention": "집중하는",
            "fatigue": "피로한",
            "empathy": "공감하는",
        }

        return {
            "state": state_copy,
            "dominant_emotion": dominant,
            "dominant_description": descriptions.get(dominant, "평온한"),
            "emotional_intensity": sum(abs(v - self._baseline.get(k, 0.5)) for k, v in state_copy.items()) / len(state_copy),
        }

    def get_importance_modifier(self) -> float:
        """현재 감정에 따른 기억 중요도 보정치를 반환합니다."""
        with self._lock:
            # 높은 curiosity/attention → 기억 중요도 증가
            return 1.0 + (self.state["curiosity"] - 0.5) * 0.4 + (self.state["attention"] - 0.5) * 0.3

    # =========================================================================
    # State Access
    # =========================================================================

    def get_state(self) -> dict[str, float]:
        with self._lock:
            return self.state.copy()

    def set_state(self, state: dict[str, float]) -> None:
        with self._lock:
            for dim, value in state.items():
                if dim in self.state:
                    self.state[dim] = max(0.0, min(1.0, value))

    def __repr__(self) -> str:
        with self._lock:
            parts = [f"{k}={v:.2f}" for k, v in self.state.items()]
        return f"EmotionEngine({', '.join(parts)})"
