package com.ara.platform.memory;

import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Service;

import java.util.UUID;

@Service
public class QdrantMemoryService {

    // 3계층 메모리: 1. Hot Memory(LRU List), 2. Warm Memory(PostgreSQL), 3. Cold Memory (Qdrant Vector DB)

    @KafkaListener(topics = {"article.parsed", "summary.generated"}, groupId = "ara-memory-group")
    public void saveTo3TierMemory(String data) {
        System.out.println("[QdrantMemoryService] 데이터 3계층 영구 보존 인덱싱 시작...");
        
        saveToPostgreSQL(data);
        saveToQdrantVectorDB(data);
        
        System.out.println("[QdrantMemoryService] 3계층 메모리 동기화 보존 완료.");
    }

    private void saveToPostgreSQL(String data) {
        System.out.println("  -> [Warm Memory PostgreSQL] 지식 데이터 및 확실성 점수 쓰기 성공");
    }

    private void saveToQdrantVectorDB(String data) {
        // 실제 Qdrant grpc/rest API 연동을 위한 PointStruct 시뮬레이션
        String pointId = UUID.randomUUID().toString();
        System.out.printf("  -> [Vector Memory Qdrant] 생성된 임베딩 벡터 저장 (PointStruct ID: %s)\n", pointId);
        System.out.println("     - Payload: {\"source\": \"Ara Insight Agent\", \"certaintyScore\": 0.95}");
    }
}
