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
public class EconomicDataCollector {
    private static final Logger logger = LoggerFactory.getLogger(EconomicDataCollector.class);
    private final KafkaTemplate<String, String> kafkaTemplate;

    private static final List<String> INDICATORS = Arrays.asList("InterestRate", "Inflation", "UnemploymentRate", "ExchangeRate", "GDP");

    public EconomicDataCollector(KafkaTemplate<String, String> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }

    @Scheduled(fixedDelayString = "${collector.economy.interval:3600000}") // 1 hour
    @CircuitBreaker(name = "economyApi", fallbackMethod = "fallbackCollect")
    @RateLimiter(name = "economyApi")
    public void collectEconomicData() {
        logger.info("[EconomicDataCollector] Fetching macroeconomic indicators from FRED/OECD...");
        
        for (String indicator : INDICATORS) {
            try {
                // TODO: 실제 FRED/OECD API 호출 로직으로 대체
                String mockDataJson = String.format("{\"indicator\": \"%s\", \"value\": 100.0, \"source\": \"FRED\", \"timestamp\": %d}", 
                                                    indicator, System.currentTimeMillis());
                
                kafkaTemplate.send("economy.raw", mockDataJson);
                logger.info("[EconomicDataCollector] Published economic data for: {}", indicator);
                
            } catch (Exception e) {
                logger.error("[EconomicDataCollector] Error fetching indicator: {}", indicator, e);
                throw e;
            }
        }
    }

    public void fallbackCollect(Throwable t) {
        logger.warn("[EconomicDataCollector] Economic Data API fallback. Reason: {}", t.getMessage());
    }
}
