package com.ara.platform.model;

import java.util.List;

/**
 * 저작권 및 리소스 절약을 위해 이미지 원본 대신 메타데이터화된 지식 스키마
 */
public class ImageKnowledge {
    private String sourceUrl;
    private String caption;
    private String ocrText;
    private List<String> detectedObjects;

    // Getters and Setters
    public String getSourceUrl() { return sourceUrl; }
    public void setSourceUrl(String sourceUrl) { this.sourceUrl = sourceUrl; }
    public String getCaption() { return caption; }
    public void setCaption(String caption) { this.caption = caption; }
    public String getOcrText() { return ocrText; }
    public void setOcrText(String ocrText) { this.ocrText = ocrText; }
    public List<String> getDetectedObjects() { return detectedObjects; }
    public void setDetectedObjects(List<String> detectedObjects) { this.detectedObjects = detectedObjects; }
}
