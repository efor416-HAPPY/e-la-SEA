package com.ara.platform.collector;

import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

@Component
public class RssCollector implements Collector {
    private final KafkaTemplate<String, String> kafkaTemplate;

    public RssCollector(KafkaTemplate<String, String> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }

    @Override
    public void collect() {
        System.out.println("[RssCollector] 지정 웹 매거진 및 기업 뉴스 RSS 피드 동기화 가동...");
        String rawRssMetadata = "{ \"title\": \"인플레이션 우려에 따른 긴축 재정 도입 뉴스\", \"link\": \"https://news.com/article1\", \"source\": \"RSS\" }";
        
        kafkaTemplate.send("rss.raw", rawRssMetadata);
        System.out.println("[RssCollector] 원본 RSS 피드 데이터 카프카 적재 완료.");
    }
}
