# -*- coding: utf-8 -*-
"""
🌱 ARA AI Microkernel Orchestrator (Pure AI Runtime)
Coordinates the AgentBus, MemoryCore, and ReasoningCore for natural AI dialogue.
"""

from backend.agents.base_agent import IAgent
from backend.kernel.agent_bus import AgentBus
from backend.kernel.message import Message
from backend.kernel.memory_core import MemoryCore
from backend.kernel.reasoning_core import ReasoningCore
from backend.kernel.security_core import SecurityCore
from backend.kernel.audit_core import AuditCore


class AraKernel:
    def __init__(self):
        # 1. Instantiate Core Subsystems
        self.bus = AgentBus()
        self.memory_core = MemoryCore()
        self.reasoning_core = ReasoningCore(self.memory_core)
        self.security_core = SecurityCore()
        self.audit_core = AuditCore()
        self.running = False

    def register_agent(self, agent: IAgent) -> None:
        """Registers a system agent on the central AgentBus and links the kernel."""
        agent.kernel = self
        self.bus.register_agent(agent)

    def start(self) -> None:
        """Powers on the core AI agents and registers them."""
        self.running = True
        self.audit_core.log("SYSTEM_LIFECYCLE", "Kernel", "Startup", "ARA AI Pure Microkernel boot sequence initiated.")

        # Register default AI agents
        from backend.agents.memory_agent import memory_agent
        from backend.agents.chat_agent import chat_agent
        from backend.agents.planner_agent import planner_agent

        self.register_agent(memory_agent)
        self.register_agent(chat_agent)
        self.register_agent(planner_agent)

        # Initialize all registered agents
        for agent in list(self.bus.agents.values()):
            agent.initialize()

        print("🌱 [AraKernel] Pure AI Microkernel booted successfully.")

    def stop(self) -> None:
        """Powers down the microkernel and registered agents."""
        self.running = False

        # Stop registered agents
        for agent_id, agent in list(self.bus.agents.items()):
            try:
                agent.shutdown()
            except Exception as e:
                print(f"❌ Error shutting down agent '{agent_id}': {e}")

        self.audit_core.log("SYSTEM_LIFECYCLE", "Kernel", "Shutdown", "ARA AI Pure Microkernel shutdown sequence completed.")
        print("🌱 [AraKernel] stopped.")


# Global Kernel Coordinator Instance
kernel_instance = AraKernel()
