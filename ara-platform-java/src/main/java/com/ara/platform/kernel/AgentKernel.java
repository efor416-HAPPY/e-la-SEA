package com.ara.platform.kernel;

import com.ara.platform.collector.KnowledgeCollector;
import com.ara.platform.memory.VectorMemory;
import com.ara.platform.model.KnowledgePacket;
import com.ara.platform.safety.SafetyLayer;

import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

/**
 * 플랫폼 코어 커널 오케스트레이터 및 분산 스케줄러
 */
public class AgentKernel {
    private final List<KnowledgeCollector> collectors;
    private final VectorMemory vectorMemory;
    private final SafetyLayer safetyLayer;
    private final ScheduledExecutorService scheduler;

    public AgentKernel(List<KnowledgeCollector> collectors, VectorMemory vectorMemory, SafetyLayer safetyLayer) {
        this.collectors = collectors;
        this.vectorMemory = vectorMemory;
        this.safetyLayer = safetyLayer;
        this.scheduler = Executors.newScheduledThreadPool(8);
    }

    public void start() {
        System.out.println("[AgentKernel] ARA 모듈러 지속 학습 플랫폼 시작.");
        
        // 각 수집기들을 스레드 풀 스케줄러에 등록하여 실시간 수집 루프 수행
        for (KnowledgeCollector collector : collectors) {
            scheduler.scheduleAtFixedRate(() -> {
                try {
                    List<KnowledgePacket> packets = collector.collect();
                    for (KnowledgePacket packet : packets) {
                        if (safetyLayer.checkIngestionSafety(packet)) {
                            vectorMemory.store(packet);
                        }
                    }
                } catch (Exception e) {
                    System.err.println("[오류] 에이전트 커널 처리 실패: " + e.getMessage());
                }
            }, 0, 10, TimeUnit.MINUTES);
        }
    }
}
