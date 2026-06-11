# -*- coding: utf-8 -*-
"""
💾 ARA AI Cognitive Agent: Memory Agent (ARA 3.0)
Handles memory operations via CognitiveBus.
Subscribes to perception, dialogue, reasoning, learning topics
to automatically capture and store important Thoughts.
"""

import time
from backend.agents.base_cognitive_agent import ICognitiveAgent
from backend.kernel.message import Message, Thought
from backend.kernel.memory_core import MemoryItem
from backend.memory.vector_memory import VectorMemory
from typing import Optional


class MemoryAgent(ICognitiveAgent):
    def __init__(self):
        super().__init__()

    def id(self) -> str:
        return "memory"

    def subscribed_topics(self) -> list[str]:
        # 대부분의 Thought를 수신하여 자동 기억
        return ["perception", "dialogue", "reasoning", "learning", "observation"]

    def initialize(self) -> bool:
        return True

    def on_thought(self, thought: Thought) -> Optional[Thought]:
        """
        Thought를 수신하면 자동으로 기억 시스템에 저장합니다.
        중요도에 따라 STM/MTM/LTM 계층이 자동 결정됩니다.
        """
        if not self.kernel:
            return None

        # 대화 내용은 DialogueMemoryItem으로 저장
        if thought.thought_type == "dialogue":
            from backend.kernel.memory_core import DialogueMemoryItem
            user_msg = thought.content
            reply = thought.context.get("reply", "")
            persona = thought.context.get("persona", "friend")
            if reply:
                item = DialogueMemoryItem(
                    user_msg=user_msg,
                    bot_reply=reply,
                    persona=persona,
                )
                self.kernel.memory_core.store(item)

        # 에피소드 기록: 중요한 인지/추론은 에피소드로
        if thought.importance >= 0.6 and thought.thought_type in ("perception", "reasoning"):
            self.kernel.memory_core.episodic.add_event(
                agent_id=thought.source,
                event_type=thought.thought_type,
                content=thought.content[:100],
                importance=thought.importance,
                metadata=thought.context,
            )

        # 학습 Thought는 LTM에 직접 저장
        if thought.thought_type == "learning":
            item = MemoryItem(
                title=f"학습: {thought.content[:20]}",
                link=f"learning://{time.time()}",
                description=thought.content,
                source=thought.source,
                scraped_at=time.strftime('%Y-%m-%d %H:%M:%S'),
                embedded_vector=str(VectorMemory.generate_mock_vector(thought.content)),
            )
            self.kernel.memory_core.store(item)

        # 기억 저장 완료를 memory Thought로 응답 (중요도 높은 것만)
        if thought.importance >= 0.7:
            return thought.derive(
                source=self.id(),
                thought_type="memory",
                content=f"기억 저장 완료: {thought.content[:30]}",
                importance=0.3,  # 메타 정보이므로 낮은 중요도
            )

        return None

    def process(self, message: Message) -> bool:
        """Legacy AgentBus dispatch 호환."""
        if message.action == "remember":
            info = message.payload.get("info", "")
            return self.remember(info)
        elif message.action == "recall":
            query = message.payload.get("query", "")
            if isinstance(message.payload, dict):
                message.payload["result"] = self.recall(query)
            return True
        return False

    def shutdown(self) -> None:
        pass

    def remember(self, info: str) -> bool:
        """Stores a custom intelligence statement into the memory core."""
        if not self.kernel:
            return False
        now_str = time.strftime('%Y-%m-%d %H:%M:%S')
        item = MemoryItem(
            title=f"기억된 지식: {info[:15]}",
            link=f"local-memo://{time.time()}",
            description=info,
            source="MemoryAgent",
            scraped_at=now_str,
            embedded_vector=str(VectorMemory.generate_mock_vector(info))
        )
        self.kernel.memory_core.store(item)
        return True

    def recall(self, query: str) -> str:
        """Recalls the most relevant description matching the query."""
        if not self.kernel:
            return ""
        items = self.kernel.memory_core.search(query)
        if not items:
            return ""
        return items[0].description


# Global Memory Agent Instance
memory_agent = MemoryAgent()
