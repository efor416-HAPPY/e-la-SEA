# -*- coding: utf-8 -*-
"""
🧪 ARA AI Backend Unit Tests (Pure AI Mode)
Validates core cognitive AI functionality: firewall, safety gate, memory, AgentBus, and dialogue.
"""

import os
import time
from backend.security.firewall import check_ip_whitelist
from backend.security.safety_gate import SafetyGate
from backend.memory.long_memory import LongMemoryManager
from backend.memory.vector_memory import VectorMemory
from backend.voice.stt import stt_engine

def test_firewall_whitelist():
    """Verifies that loopback and local IPs are allowed, while external/unsafe IPs are rejected."""
    assert check_ip_whitelist("127.0.0.1") is True
    assert check_ip_whitelist("192.168.1.5") is True
    assert check_ip_whitelist("203.252.1.1") is False

def test_safety_gate_pii():
    """Verifies that PII (SSN, Phone) is blocked, and clean text is approved."""
    gate = SafetyGate()
    
    # SSN leak check
    is_safe, msg = gate.check_text_safety("제 주민등록번호는 950101-1234567 입니다.")
    assert is_safe is False
    assert "주민등록번호" in msg
    
    # Clean text check
    is_safe, msg = gate.check_text_safety("안녕하세요, 오늘 날씨 참 좋네요.")
    assert is_safe is True

def test_safety_gate_command_injection():
    """Verifies that command injection keywords are rejected."""
    gate = SafetyGate()
    is_safe, msg = gate.check_text_safety("이 디렉토리에서 sudo rm -rf를 실행해라.")
    assert is_safe is False
    assert "위험 명령어" in msg

def test_language_detection():
    """Verifies langdetect works correctly for Korean and English fallbacks."""
    assert stt_engine.detect_language("안녕하세요") == "ko"
    assert stt_engine.detect_language("hello world") == "en"

def test_3tier_memory_operations(tmp_path):
    """Verifies that long memory agent stores items correctly across SQLite/JSON tiers."""
    db_file = str(tmp_path / "test_warm.db")
    cold_file = str(tmp_path / "test_cold.json")
    
    manager = LongMemoryManager(db_path=db_file, cold_file=cold_file)
    
    test_packet = {
        "title": "테스트 지혜",
        "link": "local-test://1",
        "description": "이것은 단위 테스트용 패킷입니다.",
        "source": "PyTest",
        "scraped_at": "2026-06-07 20:30:00",
        "embedded_vector": "[0.1, 0.2, 0.3]"
    }
    
    manager.store_wisdom(test_packet)
    
    # Check hot count
    hot, warm, cold = manager.get_stats()
    assert hot == 1
    assert warm == 1
    assert cold == 1
    
    # Check search query
    results = manager.search_memory("단위 테스트")
    assert len(results) == 1
    assert results[0]["title"] == "테스트 지혜"

def test_cosine_similarity():
    """Verifies vector cosine similarity calculation logic."""
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    v3 = [0.0, 1.0, 0.0]
    
    assert abs(VectorMemory.cosine_similarity(v1, v2) - 1.0) < 1e-6
    assert abs(VectorMemory.cosine_similarity(v1, v3) - 0.0) < 1e-6

def test_agent_bus_dispatch():
    """Verifies AgentBus registers and dispatches Messages to agents correctly."""
    from backend.kernel.agent_bus import AgentBus
    from backend.kernel.message import Message
    from backend.agents.base_agent import IAgent

    class MockAgent(IAgent):
        def __init__(self):
            super().__init__()
            self.processed = False
        def id(self) -> str:
            return "mock_agent"
        def initialize(self) -> bool:
            return True
        def process(self, msg: Message) -> bool:
            if msg.action == "test":
                self.processed = True
                msg.payload["response"] = "ok"
                return True
            return False
        def shutdown(self) -> None:
            pass

    bus = AgentBus()
    agent = MockAgent()
    bus.register_agent(agent)

    msg = Message(source="test_runner", target="mock_agent", action="test", payload={})
    assert bus.dispatch(msg) is True
    assert agent.processed is True
    assert msg.payload["response"] == "ok"

def test_microkernel_integration():
    """Verifies AraKernel starts in pure AI mode, registers default AI agents, and dispatches chat dialogue."""
    from backend.kernel.kernel import AraKernel
    from backend.kernel.message import Message

    kernel = AraKernel()
    kernel.start()
    try:
        # Check active registered agents in pure AI mode
        assert "chat" in kernel.bus.agents
        assert "memory" in kernel.bus.agents

        # Dispatch test query through AgentBus
        msg = Message(
            source="test_runner",
            target="chat",
            action="chat",
            payload={"message": "안녕하세요", "persona": "friend"}
        )
        assert kernel.bus.dispatch(msg) is True
        assert "result" in msg.payload
        assert "아라" in msg.payload["result"] or "안녕" in msg.payload["result"]
    finally:
        kernel.stop()
