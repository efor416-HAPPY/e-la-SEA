# -*- coding: utf-8 -*-
"""
🕸️ ARA AI Knowledge Graph (ARA 3.0)
In-memory concept graph that models relationships between entities.

Example:
    금 ↔ 금리 ↔ 달러 ↔ 미국연준
     ↕         ↕
    인플레이션   경기침체

The graph enables:
  - Relationship-aware reasoning ("금리가 오르면 금값은?")
  - Concept discovery through BFS/DFS traversal
  - Auto-extraction of concepts from Thought content
  - Weighted edges for relationship strength
"""

import time
import threading
import re
import json
import os
from collections import deque
from typing import Optional
from uuid import uuid4


class KnowledgeNode:
    """지식 그래프의 노드 (개념)."""

    def __init__(self, label: str, concept_type: str = "general", properties: dict = None):
        self.id = str(uuid4())[:8]
        self.label = label
        self.concept_type = concept_type  # "entity", "topic", "event", "metric"
        self.properties = properties or {}
        self.created_at = time.time()
        self.access_count = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "concept_type": self.concept_type,
            "properties": self.properties,
            "access_count": self.access_count,
        }


class KnowledgeEdge:
    """지식 그래프의 엣지 (관계)."""

    def __init__(self, from_id: str, to_id: str, relation: str, weight: float = 1.0):
        self.from_id = from_id
        self.to_id = to_id
        self.relation = relation  # "related_to", "causes", "part_of", "opposite_of"
        self.weight = weight
        self.created_at = time.time()
        self.reinforcement_count = 0

    def reinforce(self, amount: float = 0.1) -> None:
        """관계 강도를 강화합니다 (반복 확인 시)."""
        self.weight = min(5.0, self.weight + amount)
        self.reinforcement_count += 1

    def to_dict(self) -> dict:
        return {
            "from_id": self.from_id,
            "to_id": self.to_id,
            "relation": self.relation,
            "weight": self.weight,
            "reinforcement_count": self.reinforcement_count,
        }


class KnowledgeGraph:
    """
    아라의 지식 그래프.
    개념 간 관계를 저장하고, BFS 탐색으로 관련 개념을 발견합니다.
    """

    def __init__(self, storage_path: str = "downloads/knowledge_graph.json"):
        self._nodes: dict[str, KnowledgeNode] = {}  # node_id -> KnowledgeNode
        self._label_index: dict[str, str] = {}       # label(lower) -> node_id
        self._edges: list[KnowledgeEdge] = []
        self._adjacency: dict[str, list[KnowledgeEdge]] = {}  # node_id -> [edges]
        self._storage_path = storage_path
        self._lock = threading.Lock()

        # Pre-built concept associations
        self._seed_concepts()
        self._load()

    def _seed_concepts(self) -> None:
        """초기 경제/시사 관련 개념 시드 데이터."""
        seeds = [
            ("금", "metric"), ("금리", "metric"), ("달러", "metric"),
            ("미국연준", "entity"), ("인플레이션", "topic"), ("경기침체", "topic"),
            ("주식시장", "topic"), ("채권", "metric"), ("원화", "metric"),
            ("유가", "metric"), ("반도체", "topic"), ("AI", "topic"),
        ]
        relations = [
            ("금", "금리", "inverse_correlated"),
            ("금", "달러", "inverse_correlated"),
            ("금리", "미국연준", "controlled_by"),
            ("금리", "인플레이션", "response_to"),
            ("금리", "경기침체", "causes"),
            ("달러", "원화", "inverse_correlated"),
            ("유가", "인플레이션", "causes"),
            ("주식시장", "금리", "affected_by"),
            ("반도체", "AI", "enables"),
            ("채권", "금리", "correlated"),
        ]

        for label, ctype in seeds:
            self.add_concept(label, ctype)

        for from_label, to_label, relation in relations:
            self.add_relation_by_label(from_label, to_label, relation)

    # =========================================================================
    # Concept Management
    # =========================================================================

    def add_concept(self, label: str, concept_type: str = "general",
                    properties: dict = None) -> str:
        """개념을 추가하고 노드 ID를 반환합니다."""
        label_lower = label.lower()
        with self._lock:
            if label_lower in self._label_index:
                return self._label_index[label_lower]

            node = KnowledgeNode(label=label, concept_type=concept_type, properties=properties)
            self._nodes[node.id] = node
            self._label_index[label_lower] = node.id
            self._adjacency[node.id] = []
            return node.id

    def get_concept(self, label: str) -> Optional[dict]:
        """라벨로 개념을 조회합니다."""
        with self._lock:
            node_id = self._label_index.get(label.lower())
            if node_id and node_id in self._nodes:
                return self._nodes[node_id].to_dict()
            return None

    # =========================================================================
    # Relation Management
    # =========================================================================

    def add_relation(self, from_id: str, to_id: str, relation: str,
                     weight: float = 1.0) -> None:
        """노드 ID로 관계를 추가합니다."""
        with self._lock:
            if from_id not in self._nodes or to_id not in self._nodes:
                return

            # 중복 관계 확인
            for edge in self._adjacency.get(from_id, []):
                if edge.to_id == to_id and edge.relation == relation:
                    edge.reinforce()
                    return

            edge = KnowledgeEdge(from_id=from_id, to_id=to_id, relation=relation, weight=weight)
            self._edges.append(edge)
            self._adjacency.setdefault(from_id, []).append(edge)

            # 양방향 탐색을 위한 역방향 엣지도 추가
            reverse_edge = KnowledgeEdge(from_id=to_id, to_id=from_id, relation=f"_{relation}", weight=weight)
            self._edges.append(reverse_edge)
            self._adjacency.setdefault(to_id, []).append(reverse_edge)

    def add_relation_by_label(self, from_label: str, to_label: str, relation: str,
                               weight: float = 1.0) -> None:
        """라벨로 관계를 추가합니다."""
        from_id = self._label_index.get(from_label.lower())
        to_id = self._label_index.get(to_label.lower())
        if from_id and to_id:
            self.add_relation(from_id, to_id, relation, weight)

    # =========================================================================
    # Graph Traversal
    # =========================================================================

    def query_related(self, label: str, depth: int = 2, limit: int = 20) -> list[dict]:
        """BFS로 관련 개념을 탐색합니다."""
        with self._lock:
            start_id = self._label_index.get(label.lower())
            if not start_id:
                return []

            visited = set()
            results = []
            queue = deque([(start_id, 0)])
            visited.add(start_id)

            while queue and len(results) < limit:
                node_id, current_depth = queue.popleft()
                if current_depth > depth:
                    break

                node = self._nodes.get(node_id)
                if node and node_id != start_id:
                    node.access_count += 1
                    results.append({
                        **node.to_dict(),
                        "depth": current_depth,
                    })

                if current_depth < depth:
                    for edge in self._adjacency.get(node_id, []):
                        if edge.to_id not in visited:
                            visited.add(edge.to_id)
                            queue.append((edge.to_id, current_depth + 1))

            return results

    def find_path(self, from_label: str, to_label: str, max_depth: int = 5) -> list[str]:
        """두 개념 간 최단 관계 경로를 찾습니다."""
        with self._lock:
            from_id = self._label_index.get(from_label.lower())
            to_id = self._label_index.get(to_label.lower())
            if not from_id or not to_id:
                return []

            # BFS
            visited = {from_id}
            queue = deque([(from_id, [from_label])])

            while queue:
                current, path = queue.popleft()
                if current == to_id:
                    return path
                if len(path) > max_depth:
                    continue

                for edge in self._adjacency.get(current, []):
                    if edge.to_id not in visited:
                        visited.add(edge.to_id)
                        next_node = self._nodes.get(edge.to_id)
                        if next_node:
                            queue.append((edge.to_id, path + [f"-[{edge.relation}]-", next_node.label]))

            return []

    # =========================================================================
    # Auto-Extraction from Thought
    # =========================================================================

    def auto_extract(self, thought) -> list[str]:
        """Thought 내용에서 알려진 개념을 찾아 관계를 강화합니다."""
        content_lower = thought.content.lower()
        found_concepts = []

        with self._lock:
            for label, node_id in self._label_index.items():
                if label in content_lower:
                    found_concepts.append(label)
                    self._nodes[node_id].access_count += 1

        # 같은 Thought에 등장한 개념들 사이에 관계 강화
        for i in range(len(found_concepts)):
            for j in range(i + 1, len(found_concepts)):
                self.add_relation_by_label(
                    found_concepts[i], found_concepts[j],
                    "co_occurs", weight=0.5
                )

        return found_concepts

    # =========================================================================
    # Persistence
    # =========================================================================

    def save(self) -> None:
        """그래프를 JSON에 저장합니다."""
        with self._lock:
            data = {
                "nodes": [n.to_dict() for n in self._nodes.values()],
                "edges": [e.to_dict() for e in self._edges if not e.relation.startswith("_")],
                "label_index": dict(self._label_index),
            }
        try:
            os.makedirs(os.path.dirname(self._storage_path), exist_ok=True)
            with open(self._storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ [KnowledgeGraph] 저장 실패: {e}")

    def _load(self) -> None:
        """저장된 그래프를 로드합니다."""
        if not os.path.exists(self._storage_path):
            return
        try:
            with open(self._storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Restore node access counts and custom properties
            for node_dict in data.get("nodes", []):
                label_lower = node_dict["label"].lower()
                if label_lower in self._label_index:
                    node_id = self._label_index[label_lower]
                    if node_id in self._nodes:
                        self._nodes[node_id].access_count = node_dict.get("access_count", 0)
        except Exception as e:
            print(f"⚠️ [KnowledgeGraph] 로드 실패: {e}")

    # =========================================================================
    # Stats
    # =========================================================================

    def get_stats(self) -> dict:
        with self._lock:
            return {
                "total_concepts": len(self._nodes),
                "total_relations": len(self._edges) // 2,  # 양방향이므로 /2
                "most_accessed": sorted(
                    [n.to_dict() for n in self._nodes.values()],
                    key=lambda x: x["access_count"],
                    reverse=True
                )[:5],
            }

    def __repr__(self) -> str:
        return f"KnowledgeGraph(concepts={len(self._nodes)}, relations={len(self._edges) // 2})"
