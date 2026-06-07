package com.ara.platform.memory;

import com.ara.platform.model.KnowledgePacket;
import java.util.List;

/**
 * Qdrant / Weaviate / ChromaDB 연동용 백터 메모리 인터페이스
 */
public interface VectorMemory {
    void store(KnowledgePacket packet);
    List<KnowledgePacket> searchSimilar(List<Float> queryVector, int limit);
}
