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
public class YoutubeCollector {
    private static final Logger logger = LoggerFactory.getLogger(YoutubeCollector.class);
    private final KafkaTemplate<String, String> kafkaTemplate;

    private static final List<String> TARGET_KEYWORDS = Arrays.asList("Economy", "Semiconductor", "AI");

    public YoutubeCollector(KafkaTemplate<String, String> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }

    @Scheduled(fixedDelayString = "${collector.youtube.interval:600000}")
    @CircuitBreaker(name = "youtubeApi", fallbackMethod = "fallbackCollect")
    @RateLimiter(name = "youtubeApi")
    public void collectVideos() {
        logger.info("[YoutubeCollector] Starting YouTube video collection for insights...");
        
        for (String keyword : TARGET_KEYWORDS) {
            try {
                // TODO: 실제 YouTube Data API v3 호출 로직으로 대체
                String mockVideoJson = String.format("{\"videoId\": \"mock-%s\", \"title\": \"New Analysis on %s\", \"channel\": \"Tech/Econ Channel\", \"timestamp\": %d}", 
                                                     keyword, keyword, System.currentTimeMillis());
                
                kafkaTemplate.send("youtube.raw", mockVideoJson);
                logger.info("[YoutubeCollector] Published video info for keyword: {}", keyword);
                
            } catch (Exception e) {
                logger.error("[YoutubeCollector] Error collecting for keyword: {}", keyword, e);
                throw e;
            }
        }
    }

    public void fallbackCollect(Throwable t) {
        logger.warn("[YoutubeCollector] YouTube API fallback. Reason: {}", t.getMessage());
    }
}
