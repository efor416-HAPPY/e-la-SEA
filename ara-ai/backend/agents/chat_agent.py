# -*- coding: utf-8 -*-
"""
🤖 ARA AI Cognitive Agent: Chat Agent (ARA 3.0)
Bridges user dialogue with ReasoningCore via CognitiveBus.
Subscribes to "dialogue" topic and emits "reasoning" Thoughts.
"""

from backend.agents.base_cognitive_agent import ICognitiveAgent
from backend.kernel.message import Message, Thought
from typing import Optional


class ChatAgent(ICognitiveAgent):
    def __init__(self, model="gpt-4"):
        super().__init__()
        self.model = model
        self.history = []

    def id(self) -> str:
        return "chat"

    def subscribed_topics(self) -> list[str]:
        return ["dialogue"]

    def initialize(self) -> bool:
        return True

    def on_thought(self, thought: Thought) -> Optional[Thought]:
        """대화 Thought를 수신하여 응답을 생성합니다."""
        user_msg = thought.content
        persona = thought.context.get("persona", "friend")

        reply = self.generate_response(user_msg, persona)

        # 응답을 reasoning Thought로 발행 (다른 에이전트도 반응 가능)
        return thought.derive(
            source=self.id(),
            thought_type="reasoning",
            content=reply,
            importance=thought.importance,
            context={"persona": persona, "user_message": user_msg},
        )

    def process(self, message: Message) -> bool:
        """Legacy AgentBus dispatch 호환."""
        if message.action == "chat":
            user_msg = message.payload.get("message", "")
            persona = message.payload.get("persona", "friend")

            reply = self.generate_response(user_msg, persona)

            # 대화를 CognitiveBus에도 발행 (다른 에이전트 연결)
            if self.bus:
                dialogue_thought = Thought(
                    source=self.id(),
                    thought_type="dialogue",
                    content=user_msg,
                    importance=0.6,
                    context={"persona": persona, "reply": reply},
                )
                # publish로 비동기 전파 (블로킹 안 함)
                self.bus.publish(dialogue_thought)

            if isinstance(message.payload, dict):
                message.payload["result"] = reply
            return True
        return False

    def shutdown(self) -> None:
        pass

    def add_to_history(self, role: str, content: str):
        """Saves message to local RAM memory."""
        self.history.append({"role": role, "content": content})
        if len(self.history) > 30:
            self.history.pop(0)

    def generate_response(self, user_message: str, current_persona="friend") -> str:
        """Delegates cognitive thinking to the central ReasoningCore."""
        self.add_to_history("user", user_message)

        if self.kernel:
            reply = self.kernel.reasoning_core.think(user_message, current_persona)
        else:
            from backend.kernel.kernel import kernel_instance
            reply = kernel_instance.reasoning_core.think(user_message, current_persona)

        # EmotionEngine이 있으면 응답 톤 조절
        if self.kernel and hasattr(self.kernel, 'emotion_engine'):
            reply = self.kernel.emotion_engine.modulate_response(reply)

        self.add_to_history("assistant", reply)
        return reply


# Global Chat Agent Instance
chat_agent = ChatAgent()
