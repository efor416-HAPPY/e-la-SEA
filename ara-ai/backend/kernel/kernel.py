# -*- coding: utf-8 -*-
"""
🌱 ARA AI Microkernel Orchestrator
Coordinates cores (Memory, Knowledge, Reasoning, Action, Security, Audit), AgentBus, Socket Layer, and HealthMonitor.
"""

import threading
import time
from typing import Dict, List, Optional
from backend.agents.base_agent import IAgent
from backend.kernel.agent_bus import AgentBus
from backend.kernel.message import Message
from backend.kernel.socket_layer import ISocket, TcpSocket, PipeSocket, UnixSocket
from backend.kernel.memory_core import MemoryCore
from backend.kernel.knowledge_core import KnowledgeCore
from backend.kernel.reasoning_core import ReasoningCore
from backend.kernel.action_core import ActionCore
from backend.kernel.security_core import SecurityCore
from backend.kernel.audit_core import AuditCore
from backend.kernel.health_monitor import HealthMonitor


class AraKernel:
    def __init__(self):
        # 1. Instantiate Core Subsystems
        self.bus = AgentBus()
        self.memory_core = MemoryCore()
        self.knowledge_core = KnowledgeCore()
        self.reasoning_core = ReasoningCore(self.memory_core)
        self.action_core = ActionCore()
        self.security_core = SecurityCore()
        self.audit_core = AuditCore()
        self.health_monitor = HealthMonitor(self)

        # 2. Instantiate Socket Layer Connections
        self.sockets: Dict[str, ISocket] = {
            "tcp": TcpSocket(port=9091),
            "pipe": PipeSocket(pipe_name="ara_ipc_pipe"),
            "unix": UnixSocket(path="./ara_unix.sock", fallback_port=9092)
        }
        self.active_socket_type = "tcp"

        self.running = False
        self.socket_threads: List[threading.Thread] = []

    def register_agent(self, agent: IAgent) -> None:
        """Registers a system agent on the central AgentBus."""
        agent.kernel = self
        self.bus.register_agent(agent)

    def switch_socket(self, socket_type: str) -> bool:
        """Dynamically hot-swaps the active communication socket at runtime."""
        if socket_type not in self.sockets:
            print(f"⚠️ [AraKernel] Unknown socket type: '{socket_type}'")
            return False

        print(f"🔄 [AraKernel] Swapping socket layer from '{self.active_socket_type}' to '{socket_type}'...")
        
        # Stop old active socket
        self.sockets[self.active_socket_type].close()
        
        # Switch and start new active socket
        self.active_socket_type = socket_type
        if self.running:
            self.sockets[self.active_socket_type].connect()
            
        self.audit_core.log("SOCKET_SWAP", "Kernel", socket_type, f"Swapped active socket to '{socket_type}'", "SUCCESS")
        return True

    def start(self) -> None:
        """Powers on all cores, starts sockets, registers agents, and launches the watchdog daemon."""
        self.running = True
        self.audit_core.log("SYSTEM_LIFECYCLE", "Kernel", "Startup", "ARA AI Microkernel boot sequence initiated.")

        # Register default agents
        from backend.agents.news_agent import news_agent
        from backend.agents.youtube_agent import youtube_agent
        from backend.agents.economy_agent import economy_agent
        from backend.agents.memory_agent import memory_agent
        from backend.agents.planner_agent import planner_agent
        from backend.agents.chat_agent import chat_agent
        from backend.agents.monitor_agent import monitor_agent

        self.register_agent(news_agent)
        self.register_agent(youtube_agent)
        self.register_agent(economy_agent)
        self.register_agent(memory_agent)
        self.register_agent(planner_agent)
        self.register_agent(chat_agent)
        self.register_agent(monitor_agent)

        # Initialize all registered agents
        for agent in list(self.bus.agents.values()):
            agent.initialize()

        # Start background loop threads for news, youtube, economy
        for agent_id in ["news", "youtube", "economy"]:
            agent = self.bus.agents[agent_id]
            thread = threading.Thread(target=agent.start_loop, name=f"{agent_id}_loop", daemon=True)
            self.health_monitor.register_thread(agent_id, thread)
            thread.start()

        # Start active socket
        active_sock = self.sockets[self.active_socket_type]
        active_sock.connect()

        # Start socket listener thread
        sock_thread = threading.Thread(target=self._socket_listen_loop, name="SocketListener", daemon=True)
        self.socket_threads.append(sock_thread)
        sock_thread.start()

        # Start Health Monitor Watchdog
        self.health_monitor.start_monitor()

        print("🌱 [AraKernel] Microkernel booted successfully.")

    def _socket_listen_loop(self) -> None:
        """Listens for incoming connections, translates data to Message objects, and dispatches to the AgentBus."""
        while self.running:
            active_sock = self.sockets[self.active_socket_type]
            if not active_sock.is_connected:
                time.sleep(0.5)
                continue

            raw_data = active_sock.receive()
            if raw_data:
                try:
                    # Translate raw JSON string into standard Message object
                    msg = Message.from_json(raw_data)
                    self.audit_core.log("IPC_RECV", "SocketLayer", msg.target, f"Action: {msg.action}", "SUCCESS")
                    
                    # Dispatch to the AgentBus
                    dispatched = self.bus.dispatch(msg)
                    if dispatched:
                        active_sock.send(f'{{"success": true, "result": "Message dispatched to {msg.target}"}}')
                    else:
                        active_sock.send(f'{{"success": false, "error": "Dispatch to {msg.target} failed"}}')
                except Exception as e:
                    active_sock.send(f'{{"success": false, "error": "Failed to parse message: {str(e)}"}}')
                    self.audit_core.log("IPC_RECV_ERR", "SocketLayer", "None", f"Failed to parse raw data: {str(e)[:50]}", "ERROR")

    def stop(self) -> None:
        """Powers down the microkernel, closes sockets, and stops background threads."""
        self.running = False
        self.health_monitor.stop_monitor()

        # Close all sockets
        for sock in self.sockets.values():
            sock.close()

        # Stop background agent loops
        for agent_id, agent in list(self.bus.agents.items()):
            try:
                agent.shutdown()
            except Exception as e:
                print(f"❌ Error shutting down agent '{agent_id}': {e}")

        self.audit_core.log("SYSTEM_LIFECYCLE", "Kernel", "Shutdown", "ARA AI Microkernel shutdown sequence completed.")
        print("🌱 [AraKernel] Microkernel stopped.")

# Global Kernel Coordinator
kernel_instance = AraKernel()
