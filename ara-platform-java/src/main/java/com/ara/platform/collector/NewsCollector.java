package com.ara.platform.collector;

import com.ara.platform.model.KnowledgePacket;
import java.util.ArrayList;
import java.util.List;

/**
 * NewsAPI / The Guardian Open Platform 연동 뉴스 수집기
 */
public class NewsCollector implements KnowledgeCollector {
    private String apiKey;
    private String query;

    public NewsCollector(String apiKey, String query) {
        this.apiKey = apiKey;
        this.query = query;
    }

    @Override
    public List<KnowledgePacket> collect() {
        System.out.println("[NewsCollector] 뉴스 API 조회 쿼리 (" + query + ") 실행...");
        // 1. 허가된 뉴스 API 게이트웨이 호출
        // 2. Article Parser 및 Summarizer를 통한 요약본 추출
        return new ArrayList<>();
    }
}
