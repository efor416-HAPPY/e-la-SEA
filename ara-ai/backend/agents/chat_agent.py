# -*- coding: utf-8 -*-
"""
🤖 ARA AI Agent Layer: Chat Agent
Bridges user dialogue with the ReasoningCore and coordinates chat-related actions via the AgentBus.
"""

from backend.agents.base_agent import IAgent
from backend.kernel.message import Message


class ChatAgent(IAgent):
    def __init__(self, model="gpt-4"):
        self.model = model
        self.history = []
        self.kernel = None
        self.bus = None

    def id(self) -> str:
        return "chat"

    def initialize(self) -> bool:
        return True

    def process(self, message: Message) -> bool:
        """Processes dialogue generation requests received via the AgentBus."""
        if message.action == "chat":
            user_msg = message.payload.get("message", "")
            persona = message.payload.get("persona", "friend")
            reply = self.generate_response(user_msg, persona)
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
        """Delegates cognitive thinking and response generation to the central ReasoningCore."""
        self.add_to_history("user", user_message)
        
        # Call the kernel reasoning core
        if self.kernel:
            reply = self.kernel.reasoning_core.think(user_message, current_persona)
        else:
            # Fallback if kernel is not set (for decoupled direct instantiations)
            from backend.kernel.kernel import kernel_instance
            reply = kernel_instance.reasoning_core.think(user_message, current_persona)
            
        self.add_to_history("assistant", reply)
        return reply


# Global Chat Agent Instance
chat_agent = ChatAgent()
