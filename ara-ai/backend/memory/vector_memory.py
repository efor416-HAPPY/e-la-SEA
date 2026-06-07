# -*- coding: utf-8 -*-
"""
🧠 ARA AI Knowledge Subsystem: Vector Memory
Provides vector embedding simulation and cosine similarity search helper.
Supports graceful fallback to pure python calculations if PyTorch/Numpy are missing.
"""

import json
import math

class VectorMemory:
    """Handles vector similarity ranking for long term memory retrieval."""
    @staticmethod
    def generate_mock_vector(seed_text: str, dimensions=128) -> list[float]:
        """Simulates text embedding generation."""
        vector = [0.0] * dimensions
        if not seed_text:
            return vector
        
        # Simple deterministically hashed vector based on characters
        for idx, char in enumerate(seed_text):
            vector[idx % dimensions] += ord(char)
            
        # Normalize vector to unit length
        sq_sum = sum(val * val for val in vector)
        if sq_sum > 0:
            norm = math.sqrt(sq_sum)
            vector = [val / norm for val in vector]
        return vector

    @staticmethod
    def cosine_similarity(v1: list[float], v2: list[float]) -> float:
        """Computes cosine similarity between two float vectors."""
        if len(v1) != len(v2) or not v1:
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(v1, v2))
        norm_a = math.sqrt(sum(a * a for a in v1))
        norm_b = math.sqrt(sum(b * b for b in v2))
        
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
            
        return dot_product / (norm_a * norm_b)

    @classmethod
    def rank_similar_packets(cls, query_vector: list[float], packets: list[dict], threshold=0.3, limit=5) -> list[dict]:
        """Ranks database packets based on cosine similarity to query vector."""
        scored_packets = []
        for packet in packets:
            vector_str = packet.get("embedded_vector", "[]")
            try:
                vector = json.loads(vector_str)
            except Exception:
                vector = []
                
            if len(vector) == len(query_vector):
                sim = cls.cosine_similarity(query_vector, vector)
                if sim >= threshold:
                    scored_packets.append((sim, packet))
            
        # Sort by similarity descending
        scored_packets.sort(key=lambda x: x[0], reverse=True)
        return [packet for sim, packet in scored_packets[:limit]]
