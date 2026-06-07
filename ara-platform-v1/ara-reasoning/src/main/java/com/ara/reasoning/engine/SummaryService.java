package com.ara.reasoning.engine;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

@Service
public class SummaryService {
    private static final Logger logger = LoggerFactory.getLogger(SummaryService.class);
    private final KafkaTemplate<String, String> kafkaTemplate;

    public SummaryService(KafkaTemplate<String, String> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }

    @KafkaListener(topics = "article.parsed", groupId = "ara-summary-group")
    public void generateSummary(String message) {
        logger.info("[SummaryService] Generating summary for: {}", message);

        // TODO: 실제 LLM 호출을 통한 요약 및 시나리오 생성 로직
        String summaryJson = String.format("{ \"summary\": \"Generated summary for article\", \"scenario\": \"Investment scenario: wait and see\", \"original\": %s }", message);
        
        kafkaTemplate.send("summary.generated", summaryJson);
        logger.info("[SummaryService] Summary generated and sent to summary.generated");
    }
}
