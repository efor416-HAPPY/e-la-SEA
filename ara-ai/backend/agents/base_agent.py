# -*- coding: utf-8 -*-
"""
🤖 ARA AI Agent Interface
Standard interface that all platform agents must implement.
"""

from backend.kernel.message import Message

class IAgent:
    def id(self) -> str:
        """Returns the unique identifier of the agent."""
        raise NotImplementedError

    def initialize(self) -> bool:
        """Initializes the agent's resources/dependencies."""
        raise NotImplementedError

    def process(self, message: Message) -> bool:
        """Processes the given Message object."""
        raise NotImplementedError

    def shutdown(self) -> None:
        """Performs cleanup when shutting down the agent."""
        raise NotImplementedError
