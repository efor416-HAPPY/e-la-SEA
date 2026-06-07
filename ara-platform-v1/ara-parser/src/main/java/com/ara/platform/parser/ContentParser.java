package com.ara.platform.parser;

import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

@Service
public class ContentParser {
    private final KafkaTemplate<String, String> kafkaTemplate;

    public ContentParser(KafkaTemplate<String, String> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }

    @KafkaListener(topics = {"youtube.raw", "news.raw", "economy.raw", "rss.raw"}, groupId = "ara-parser-group")
    public void parseRawContent(String rawMessage) {
        System.out.println("[ContentParser] 수신된 raw 데이터 파싱 시작: " + rawMessage);
        
        try {
            // TODO: 실제 JSON 파싱 및 중복 검증 로직 추가 (SimHashUtil 활용)
            if (rawMessage.contains("ERROR_TRIGGER")) {
                throw new RuntimeException("Parsing Error for test");
            }

            // 1. HTML 태그 제거, OCR 처리 및 인지 텍스트 정규화
            String parsedData = "{ \"parsed\": true, \"original\": " + rawMessage + " }";
            
            // 2. 가공된 데이터를 카프카 토픽 article.parsed 로 전송
            kafkaTemplate.send("article.parsed", parsedData);
            System.out.println("[ContentParser] 구조화 파싱 완료 및 article.parsed 적재.");
            
        } catch (Exception e) {
            System.err.println("[ContentParser] 에러 발생, DLQ로 전송: " + e.getMessage());
            kafkaTemplate.send("dlq.content", rawMessage);
        }
    }
}
