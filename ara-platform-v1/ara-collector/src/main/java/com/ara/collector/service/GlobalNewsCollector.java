package com.ara.collector.service;

import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;
import io.github.resilience4j.ratelimiter.annotation.RateLimiter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.util.Arrays;
import java.util.List;

@Service
public class GlobalNewsCollector {
    private static final Logger logger = LoggerFactory.getLogger(GlobalNewsCollector.class);
    private final KafkaTemplate<String, String> kafkaTemplate;

    // 지원 매체 목록
    private static final List<String> MEDIA_SOURCES = Arrays.asList(
            "NYT", "WashingtonPost", "Economist", "BBC", "FT",
            "PeopleDaily", "DW", "LeMonde", "OGlobo", "Kompas", "VnExpress"
    );

    public GlobalNewsCollector(KafkaTemplate<String, String> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }

    @Scheduled(fixedDelayString = "${collector.news.interval:300000}")
    @CircuitBreaker(name = "newsApi", fallbackMethod = "fallbackCollect")
    @RateLimiter(name = "newsApi")
    public void collectGlobalNews() {
        logger.info("[GlobalNewsCollector] Starting real-time global news collection...");
        
        for (String source : MEDIA_SOURCES) {
            try {
                // TODO: 실제 API 호출 로직으로 대체 (현재는 Mock/데모용)
                String mockNewsJson = String.format("{\"source\": \"%s\", \"title\": \"Global Market Update from %s\", \"content\": \"Sample content discussing interest rates and semiconductors in %s\", \"timestamp\": %d}", 
                                                    source, source, source, System.currentTimeMillis());
                
                kafkaTemplate.send("news.raw", mockNewsJson);
                logger.info("[GlobalNewsCollector] Published news from {}", source);
                
            } catch (Exception e) {
                logger.error("[GlobalNewsCollector] Error collecting from {}", source, e);
                throw e; // CircuitBreaker 트리거를 위한 예외 전파
            }
        }
    }

    public void fallbackCollect(Throwable t) {
        logger.warn("[GlobalNewsCollector] Circuit Breaker triggered or Rate Limit exceeded. Fallback mode. Reason: {}", t.getMessage());
        // DLQ나 관리자 알림 파이프라인으로 라우팅 가능
    }
}
