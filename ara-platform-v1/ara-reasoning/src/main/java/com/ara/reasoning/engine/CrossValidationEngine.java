package com.ara.reasoning.engine;

import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class CrossValidationEngine {
    
    // 글로벌 주요 매체 신뢰도 및 성향 맵핑 (예시)
    private static final Map<String, Double> MEDIA_WEIGHTS = new HashMap<>();
    static {
        MEDIA_WEIGHTS.put("NYT", 0.9);
        MEDIA_WEIGHTS.put("WashingtonPost", 0.9);
        MEDIA_WEIGHTS.put("Economist", 0.95);
        MEDIA_WEIGHTS.put("BBC", 0.95);
        MEDIA_WEIGHTS.put("FT", 0.95);
        MEDIA_WEIGHTS.put("PeopleDaily", 0.6); // 관영매체 바이어스 고려
        MEDIA_WEIGHTS.put("DW", 0.9);
        MEDIA_WEIGHTS.put("LeMonde", 0.85);
        MEDIA_WEIGHTS.put("OGlobo", 0.8);
        MEDIA_WEIGHTS.put("Kompas", 0.8);
        MEDIA_WEIGHTS.put("VnExpress", 0.75);
    }

    public CrossValidationResult validate(String topic, List<ArticleInfo> articles) {
        if (articles == null || articles.isEmpty()) {
            return new CrossValidationResult(0.0, "No data to validate");
        }

        double totalWeight = 0;
        double consistencyScore = 0;

        for (ArticleInfo article : articles) {
            double weight = MEDIA_WEIGHTS.getOrDefault(article.getSource(), 0.7);
            totalWeight += weight;
            
            // 단순화된 로직: 모든 기사가 같은 topic에 대해 긍정/부정 등 일치한다고 가정
            // 실제 구현에서는 LLM을 이용해 기사 간 상충 여부를 분석함
            if (article.isConsistentWith(topic)) {
                consistencyScore += weight;
            } else {
                // 상충하는 기사의 경우 페널티 부여
                consistencyScore -= (weight * 0.5); 
            }
        }

        double finalScore = Math.max(0.0, Math.min(1.0, consistencyScore / totalWeight));
        
        String report = String.format("Cross-Validation Score: %.2f based on %d global sources", finalScore, articles.size());
        return new CrossValidationResult(finalScore, report);
    }
    
    public static class ArticleInfo {
        private String source;
        private String content;

        public ArticleInfo(String source, String content) {
            this.source = source;
            this.content = content;
        }

        public String getSource() { return source; }
        public String getContent() { return content; }

        public boolean isConsistentWith(String topic) {
            // 데모용: 기본적으로 일치한다고 가정
            return true;
        }
    }

    public static class CrossValidationResult {
        private double certaintyScore;
        private String report;

        public CrossValidationResult(double certaintyScore, String report) {
            this.certaintyScore = certaintyScore;
            this.report = report;
        }

        public double getCertaintyScore() { return certaintyScore; }
        public String getReport() { return report; }
    }
}
