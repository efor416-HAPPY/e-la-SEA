# -*- coding: utf-8 -*-
import sys, io
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from backend.kernel.kernel import kernel_instance
from backend.kernel.message import Message, Thought

# 1. Boot
kernel_instance.start()
print()

# 2. Full Neuron Connection Map
print("=" * 70)
print("  NEURON CONNECTION MAP (ARA 3.0)")
print("=" * 70)
bus = kernel_instance.cognitive_bus
stats = bus.get_stats()
agents = list(bus._agents.keys())
print(f"Total agents: {len(agents)}")
print(f"Agents: {agents}")
print()
print("Topic subscriptions (who reacts to what):")
for topic, subs in sorted(stats["subscriptions"].items()):
    print(f"  {topic:15s} -> {subs}")
print()

# 3. Legacy dispatch still works
print("=" * 70)
print("  LEGACY DISPATCH TEST")
print("=" * 70)
msg = Message("test", "chat", "chat", {"message": "hello", "persona": "friend"})
r = bus.dispatch(msg)
reply = msg.payload.get("result", "EMPTY")
print(f"dispatch('chat'): {r}")
print(f"Reply: {reply[:80]}")
print()

# 4. Full cognitive cycle: perception -> cascade
print("=" * 70)
print("  FULL COGNITIVE CYCLE TEST")
print("=" * 70)
t = Thought(
    source="external_sensor",
    thought_type="perception",
    content="Fed raises interest rates, gold price drops, dollar strengthens",
    importance=0.85,
)
cascaded = bus.publish_sync(t)
print(f"Input: perception (importance=0.85)")
print(f"Cascade reactions: {len(cascaded)}")
for c in cascaded:
    print(f"  [{c.source:20s}] {c.thought_type:12s} -> {c.content[:55]}")
print()

# 5. Check all subsystems reacted
print("=" * 70)
print("  SUBSYSTEM STATUS")
print("=" * 70)
emotion = kernel_instance.emotion_engine.get_state()
print(f"Emotion: curiosity={emotion['curiosity']:.2f}, confidence={emotion['confidence']:.2f}, "
      f"attention={emotion['attention']:.2f}, empathy={emotion['empathy']:.2f}")

mem_stats = kernel_instance.memory_core.get_cognitive_stats()
print(f"Memory:  STM={mem_stats['stm_count']}, MTM={mem_stats['mtm_count']}, "
      f"LTM=({mem_stats['ltm_hot']},{mem_stats['ltm_warm']},{mem_stats['ltm_cold']})")

kg_stats = kernel_instance.knowledge_graph.get_stats()
print(f"KnowledgeGraph: {kg_stats['total_concepts']} concepts, {kg_stats['total_relations']} relations")

plan_stats = kernel_instance.planner_engine.get_stats()
print(f"Planner: {plan_stats['active_plans']} active, {plan_stats['completed_plans']} completed")

thoughts = bus.get_recent_thoughts()
print(f"Recent thoughts: {len(thoughts)}")
print()

# 6. Verify all connections
print("=" * 70)
print("  VERIFICATION")
print("=" * 70)
errors = []
if len(agents) < 8:
    errors.append(f"Expected 8 agents, got {len(agents)}")
if len(cascaded) < 2:
    errors.append(f"Expected 2+ cascade reactions, got {len(cascaded)}")
if emotion['curiosity'] <= 0.5:
    errors.append(f"Emotion curiosity should have increased from 0.5")
if len(thoughts) < 1:
    errors.append(f"No thoughts recorded in history")

if errors:
    for e in errors:
        print(f"  FAIL: {e}")
else:
    print("  ALL CONNECTIONS VERIFIED OK")
print("=" * 70)
