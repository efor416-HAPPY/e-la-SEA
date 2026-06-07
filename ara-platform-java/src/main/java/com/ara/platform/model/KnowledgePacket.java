package com.ara.platform.model;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 모듈러 수집 엔진에 의해 표준화된 지식 데이터 패킷
 */
public class KnowledgePacket {
    private String id;
    private String title;
    private String sourceUrl;
    private String description;
    private String contentSummary;
    private String sourceType; // YOUTUBE, NEWS, RSS, IMAGE, PDF
    private LocalDateTime collectedAt;
    private List<Float> embeddingVector;

    // Getters and Setters
    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }
    public String getSourceUrl() { return sourceUrl; }
    public void setSourceUrl(String sourceUrl) { this.sourceUrl = sourceUrl; }
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
    public String getContentSummary() { return contentSummary; }
    public void setContentSummary(String contentSummary) { this.contentSummary = contentSummary; }
    public String getSourceType() { return sourceType; }
    public void setSourceType(String sourceType) { this.sourceType = sourceType; }
    public LocalDateTime getCollectedAt() { return collectedAt; }
    public void setCollectedAt(LocalDateTime collectedAt) { this.collectedAt = collectedAt; }
    public List<Float> getEmbeddingVector() { return embeddingVector; }
    public void setEmbeddingVector(List<Float> embeddingVector) { this.embeddingVector = embeddingVector; }
}
