# -*- coding: utf-8 -*-
"""
🚌 ARA AI Agent Bus
Manages registration of IAgent objects and dispatches Message packages between them.
"""

from typing import Dict
from backend.agents.base_agent import IAgent
from backend.kernel.message import Message

class AgentBus:
    def __init__(self):
        self.agents: Dict[str, IAgent] = {}

    def register_agent(self, agent: IAgent) -> None:
        """Registers a service agent onto the bus."""
        self.agents[agent.id()] = agent
        agent.bus = self
        print(f"🚌 [AgentBus] Registered agent: '{agent.id()}'")

    def dispatch(self, message: Message) -> bool:
        """Routes a message packet to the targeted agent."""
        target = message.target
        if target in self.agents:
            try:
                return self.agents[target].process(message)
            except Exception as e:
                print(f"❌ [AgentBus] Failed to process message in agent '{target}': {e}")
                return False
        else:
            print(f"⚠️ [AgentBus] Dispatch target '{target}' not registered.")
            return False
