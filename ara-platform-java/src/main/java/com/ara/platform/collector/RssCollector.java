package com.ara.platform.collector;

import com.ara.platform.model.KnowledgePacket;
import java.util.ArrayList;
import java.util.List;

/**
 * 웹 매거진 및 블로그 RSS 수집기
 */
public class RssCollector implements KnowledgeCollector {
    private String rssUrl;

    public RssCollector(String rssUrl) {
        this.rssUrl = rssUrl;
    }

    @Override
    public List<KnowledgePacket> collect() {
        System.out.println("[RssCollector] RSS 피드 동기화 -> " + rssUrl);
        // 1. XML Feed parsing 및 신규 기사 감지
        return new ArrayList<>();
    }
}
