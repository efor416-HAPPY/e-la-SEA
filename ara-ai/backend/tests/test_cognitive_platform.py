# -*- coding: utf-8 -*-
"""
🧪 ARA 3.0 Cognitive Platform — Integration Test
Tests the full cognitive pipeline: Thought → CognitiveBus → Engines → Memory
"""

import sys
import os
import io
import time

# Force UTF-8 output on Windows (prevents CP949 encoding crashes)
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


def test_thought_creation():
    """Thought 생성 및 직렬화 테스트."""
    from backend.kernel.message import Thought, Message

    # 기존 Message가 여전히 작동하는지
    msg = Message(source="test", target="chat", action="chat", payload={"message": "hello"})
    assert msg.source == "test"
    assert msg.to_dict()["action"] == "chat"
    print("✅ Message 기존 호환성 OK")

    # Thought 생성
    thought = Thought(
        source="news",
        thought_type="perception",
        content="금리 인상 뉴스 감지",
        importance=0.85,
        emotion={"curiosity": 0.8},
        context={"url": "https://example.com"},
    )
    assert thought.source == "news"
    assert thought.thought_type == "perception"
    assert 0.84 < thought.importance < 0.86
    assert thought.emotion == {"curiosity": 0.8}
    assert thought.id is not None
    assert thought.trace == []
    print("✅ Thought 생성 OK")

    # 직렬화/역직렬화
    d = thought.to_dict()
    restored = Thought.from_dict(d)
    assert restored.id == thought.id
    assert restored.content == thought.content
    assert restored.importance == thought.importance
    print("✅ Thought 직렬화/역직렬화 OK")

    # 파생 Thought
    derived = thought.derive(
        source="reasoning",
        thought_type="reasoning",
        content="금리 인상은 금값에 부정적 영향"
    )
    assert derived.parent_id == thought.id
    assert derived.source == "reasoning"
    print("✅ Thought 파생 (derive) OK")


def test_cognitive_bus():
    """CognitiveBus Pub/Sub 라우팅 테스트."""
    from backend.kernel.cognitive_bus import CognitiveBus
    from backend.kernel.message import Thought, Message
    from backend.agents.base_cognitive_agent import ICognitiveAgent

    received_thoughts = []

    class TestAgent(ICognitiveAgent):
        def id(self): return "test_receiver"
        def subscribed_topics(self): return ["perception", "dialogue"]
        def on_thought(self, thought):
            received_thoughts.append(thought)
            return None
        def initialize(self): return True
        def shutdown(self): pass

    class TestSender(ICognitiveAgent):
        def id(self): return "test_sender"
        def subscribed_topics(self): return []
        def on_thought(self, thought): return None
        def initialize(self): return True
        def shutdown(self): pass

    bus = CognitiveBus()
    receiver = TestAgent()
    sender = TestSender()
    bus.register(receiver)
    bus.register(sender)

    # publish_sync 테스트 (동기식)
    thought = Thought(source="test_sender", thought_type="perception", content="테스트 인지 메시지")
    bus.publish_sync(thought)

    assert len(received_thoughts) == 1
    assert received_thoughts[0].content == "테스트 인지 메시지"
    assert "test_receiver" in received_thoughts[0].trace
    print("✅ CognitiveBus Pub/Sub 라우팅 OK")

    # 구독하지 않은 토픽은 전달되지 않음
    thought2 = Thought(source="test_sender", thought_type="system", content="시스템 메시지")
    bus.publish_sync(thought2)
    assert len(received_thoughts) == 1  # receiver는 "system" 미구독
    print("✅ CognitiveBus 토픽 필터링 OK")

    # Legacy dispatch 호환
    msg = Message(source="test", target="test_receiver", action="chat", payload={"message": "hello"})
    result = bus.dispatch(msg)
    # TestAgent.process()가 호출되어 on_thought 실행됨
    assert len(received_thoughts) >= 2
    print("✅ CognitiveBus Legacy dispatch 호환 OK")

    # 통계
    stats = bus.get_stats()
    assert stats["agents_registered"] == 2
    assert stats["total_published"] >= 0
    print(f"✅ CognitiveBus 통계 OK: {stats}")


def test_memory_layers():
    """5계층 기억 시스템 테스트."""
    from backend.memory.stm import ShortTermMemory
    from backend.memory.mtm import MediumTermMemory
    from backend.memory.episode_memory import EpisodeMemory

    # STM 테스트
    stm = ShortTermMemory(capacity=5, default_ttl=10.0)
    stm.store("key1", "value1", importance=0.3)
    stm.store("key2", "value2", importance=0.8)

    assert stm.recall("key1") == "value1"
    assert stm.recall("key2") == "value2"
    assert stm.get_count() == 2
    print("✅ STM 저장/검색 OK")

    # STM 검색
    results = stm.search("value2")
    assert len(results) >= 1
    print("✅ STM 키워드 검색 OK")

    # MTM 테스트
    mtm = MediumTermMemory(capacity=10)
    mtm.promote_from_stm("k1", "important data", importance=0.9)
    assert mtm.recall("k1") == "important data"
    print("✅ MTM 승격/검색 OK")

    # Episode 테스트
    ep = EpisodeMemory(storage_path="downloads/test_episodes.json")
    episode = ep.begin_episode("테스트 트리거", "test")
    ep.add_event("agent1", "action", "작업 수행", importance=0.7)
    ep.add_event("agent2", "observation", "결과 관찰", importance=0.6)
    completed = ep.end_episode("테스트 성공", success=True)

    assert completed is not None
    assert completed.trigger == "테스트 트리거"
    assert len(completed.events) == 2
    print("✅ Episode 기억 OK")

    # Episode 검색
    results = ep.recall_similar("테스트")
    assert len(results) >= 1
    print("✅ Episode 검색 OK")


def test_emotion_engine():
    """감정 엔진 테스트."""
    from backend.kernel.emotion_engine import EmotionEngine
    from backend.kernel.message import Thought

    engine = EmotionEngine()
    initial = engine.get_state()
    assert initial["curiosity"] == 0.5

    # 인지 Thought → curiosity 증가
    thought = Thought(source="news", thought_type="perception", content="금리 인상 전망 분석")
    changes = engine.update(thought)
    assert engine.get_state()["curiosity"] > 0.5
    print(f"✅ EmotionEngine 업데이트 OK: curiosity={engine.get_state()['curiosity']:.2f}")

    # 대화 Thought → empathy 증가
    thought2 = Thought(source="user", thought_type="dialogue", content="오늘 힘들었어")
    engine.update(thought2)
    assert engine.get_state()["empathy"] > 0.5
    print(f"✅ EmotionEngine 대화 반응 OK: empathy={engine.get_state()['empathy']:.2f}")

    # 감정 맥락
    ctx = engine.get_emotional_context()
    assert "dominant_emotion" in ctx
    assert "emotional_intensity" in ctx
    print(f"✅ EmotionEngine 맥락: {ctx['dominant_description']} ({ctx['dominant_emotion']})")


def test_knowledge_graph():
    """지식 그래프 테스트."""
    from backend.kernel.knowledge_graph import KnowledgeGraph
    from backend.kernel.message import Thought

    kg = KnowledgeGraph(storage_path="downloads/test_kg.json")

    # 시드 개념 확인
    gold = kg.get_concept("금")
    assert gold is not None
    print("✅ KnowledgeGraph 시드 개념 OK")

    # 관계 탐색
    related = kg.query_related("금", depth=2)
    labels = [r["label"] for r in related]
    assert "금리" in labels or len(related) > 0
    print(f"✅ KnowledgeGraph 관계 탐색 OK: 금 → {labels}")

    # 경로 탐색
    path = kg.find_path("금", "미국연준")
    assert len(path) > 0
    print(f"✅ KnowledgeGraph 경로: {' → '.join(path)}")

    # 자동 추출
    thought = Thought(source="news", thought_type="perception", content="금리 인상으로 달러 강세 전망")
    found = kg.auto_extract(thought)
    assert len(found) >= 2  # "금리", "달러"
    print(f"✅ KnowledgeGraph 자동 추출: {found}")


def test_planner_engine():
    """계획 엔진 테스트."""
    from backend.kernel.planner_engine import PlannerEngine

    planner = PlannerEngine()

    # 경제 분석 계획 생성
    plan = planner.create_plan("금값 분석해줘")
    assert plan.plan_type == "economy_analysis"
    assert len(plan.steps) > 0
    print(f"✅ PlannerEngine 계획 생성 OK: {plan.plan_type}, {len(plan.steps)}단계")

    # 단계 실행
    step = planner.execute_step(plan.id)
    assert step is not None
    assert step.status == "running"
    planner.complete_step(plan.id, step.id, result="뉴스 3건 수집 완료")
    print(f"✅ PlannerEngine 단계 실행 OK: {step.title}")

    # 진행률
    plan_data = planner.get_plan(plan.id)
    assert plan_data["progress"] > 0
    print(f"✅ PlannerEngine 진행률: {plan_data['progress']*100:.0f}%")


def test_full_cognitive_cycle():
    """전체 인지 사이클 통합 테스트."""
    from backend.kernel.cognitive_bus import CognitiveBus
    from backend.kernel.message import Thought
    from backend.kernel.emotion_engine import EmotionEngine
    from backend.kernel.knowledge_graph import KnowledgeGraph
    from backend.agents.base_cognitive_agent import ICognitiveAgent

    memory_log = []
    reasoning_log = []

    class MockMemoryAgent(ICognitiveAgent):
        def id(self): return "memory"
        def subscribed_topics(self): return ["perception", "reasoning"]
        def on_thought(self, thought):
            memory_log.append(thought.content)
            return thought.derive("memory", "memory", f"기억 저장: {thought.content[:20]}")
        def initialize(self): return True
        def shutdown(self): pass

    class MockReasoningAgent(ICognitiveAgent):
        def id(self): return "reasoning"
        def subscribed_topics(self): return ["perception"]
        def on_thought(self, thought):
            reasoning_log.append(thought.content)
            return thought.derive("reasoning", "reasoning", f"분석 결과: {thought.content[:20]}")
        def initialize(self): return True
        def shutdown(self): pass

    bus = CognitiveBus()
    emotion = EmotionEngine()
    kg = KnowledgeGraph(storage_path="downloads/test_cycle_kg.json")

    # 훅 등록
    bus.add_hook(lambda t: emotion.update(t))
    bus.add_hook(lambda t: kg.auto_extract(t))

    bus.register(MockMemoryAgent())
    bus.register(MockReasoningAgent())

    # 인지 사이클 시작: 뉴스 에이전트가 Thought 발행
    news_thought = Thought(
        source="news",
        thought_type="perception",
        content="금리 인상으로 달러 강세, 금값 하락 전망",
        importance=0.85,
    )

    # 동기식 처리 (테스트용)
    cascaded = bus.publish_sync(news_thought)

    # 검증
    assert len(memory_log) >= 1, "MemoryAgent가 perception을 수신해야 함"
    assert len(reasoning_log) >= 1, "ReasoningAgent가 perception을 수신해야 함"
    print(f"✅ 전체 인지 사이클 OK")
    print(f"   Memory 수신: {memory_log}")
    print(f"   Reasoning 수신: {reasoning_log}")
    print(f"   Cascaded thoughts: {len(cascaded)}")
    print(f"   Emotion state: {emotion.get_state()}")
    print(f"   KG auto-extracted concepts available")

    # 감정이 변했는지 확인
    assert emotion.get_state()["curiosity"] > 0.5, "금리/달러 키워드로 curiosity 증가해야 함"
    print("✅ 감정 반응 확인 OK")

    # Cascade된 Thought가 있는지 확인
    assert len(cascaded) >= 2, "Memory와 Reasoning 에이전트 둘 다 반응해야 함"
    print("✅ Thought cascade 확인 OK")


def run_all_tests():
    """모든 테스트 실행."""
    print("\n" + "=" * 65)
    print("  🧪 ARA 3.0 COGNITIVE PLATFORM — TEST SUITE")
    print("=" * 65 + "\n")

    tests = [
        ("Thought 생성/직렬화", test_thought_creation),
        ("CognitiveBus Pub/Sub", test_cognitive_bus),
        ("5계층 기억 시스템", test_memory_layers),
        ("EmotionEngine", test_emotion_engine),
        ("KnowledgeGraph", test_knowledge_graph),
        ("PlannerEngine", test_planner_engine),
        ("전체 인지 사이클", test_full_cognitive_cycle),
    ]

    passed = 0
    failed = 0
    for name, test_fn in tests:
        print(f"\n--- [{name}] ---")
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"❌ FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print(f"\n{'=' * 65}")
    print(f"  결과: {passed}/{passed + failed} 통과, {failed} 실패")
    print(f"{'=' * 65}\n")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
