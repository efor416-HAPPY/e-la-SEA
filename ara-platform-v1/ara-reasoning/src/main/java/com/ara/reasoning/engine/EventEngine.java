package com.ara.reasoning.engine;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

import java.util.Collections;

@Service
public class EventEngine {
    private static final Logger logger = LoggerFactory.getLogger(EventEngine.class);
    private final KafkaTemplate<String, String> kafkaTemplate;
    private final CrossValidationEngine crossValidationEngine;

    public EventEngine(KafkaTemplate<String, String> kafkaTemplate, CrossValidationEngine crossValidationEngine) {
        this.kafkaTemplate = kafkaTemplate;
        this.crossValidationEngine = crossValidationEngine;
    }

    @KafkaListener(topics = "article.parsed", groupId = "ara-reasoning-group")
    public void processParsedArticle(String message) {
        logger.info("[EventEngine] Received parsed article for reasoning: {}", message);

        // 1. 교차 검증 수행 (Cross Validation)
        CrossValidationEngine.ArticleInfo dummyArticle = new CrossValidationEngine.ArticleInfo("NYT", message);
        CrossValidationEngine.CrossValidationResult cvResult = crossValidationEngine.validate("Economy", Collections.singletonList(dummyArticle));
        
        logger.info("[EventEngine] Validation Result: {}", cvResult.getReport());

        if (cvResult.getCertaintyScore() > 0.8) {
            // 2. 확실성이 높은 경우, 경제적 영향도 계산 및 알림 생성
            String alertMessage = String.format("{ \"type\": \"HIGH_CERTAINTY_ALERT\", \"score\": %f, \"message\": \"Verified event detected\", \"original\": %s }", cvResult.getCertaintyScore(), message);
            kafkaTemplate.send("alert.generated", alertMessage);
            logger.info("[EventEngine] Alert generated and sent to alert.generated");
        } else {
            logger.warn("[EventEngine] Information certainty is low ({}). Skipping alert.", cvResult.getCertaintyScore());
        }
    }
}
