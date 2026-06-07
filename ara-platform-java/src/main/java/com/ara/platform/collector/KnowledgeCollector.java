package com.ara.platform.collector;

import com.ara.platform.model.KnowledgePacket;
import java.util.List;

/**
 * 모듈러 수집기를 위한 공통 수집기 인터페이스
 */
public interface KnowledgeCollector {
    List<KnowledgePacket> collect();
}
