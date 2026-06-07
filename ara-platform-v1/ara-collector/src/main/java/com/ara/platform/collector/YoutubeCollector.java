package com.ara.platform.collector;

import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

@Component
public class YoutubeCollector implements Collector {
    private final KafkaTemplate<String, String> kafkaTemplate;

    public YoutubeCollector(KafkaTemplate<String, String> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }

    @Override
    public void collect() {
        System.out.println("[YouTubeCollector] 모니터링 중인 유튜브 채널의 신규 동영상 및 트랜스크립트 추출 가동...");
        // 1. YouTube Data API 호출 및 스크래핑
        String rawVideoMetadata = "{ \"title\": \"신규 반도체 공장 라인 증설 발표\", \"url\": \"https://youtube.com/watch?v=fac1\", \"source\": \"YOUTUBE\" }";
        
        // 2. 카프카 토픽 youtube.raw 로 메시지 전송 (비동기 Ingestion)
        kafkaTemplate.send("youtube.raw", rawVideoMetadata);
        System.out.println("[YouTubeCollector] 원본 비디오 메타데이터 카프카 적재 완료.");
    }
}
