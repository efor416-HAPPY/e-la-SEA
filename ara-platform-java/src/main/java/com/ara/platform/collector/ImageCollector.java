package com.ara.platform.collector;

import com.ara.platform.model.KnowledgePacket;
import java.util.ArrayList;
import java.util.List;

/**
 * 이미지 설명 및 객체 인식 기반 메타데이터 추출 수집기 (저작권 세이프)
 */
public class ImageCollector implements KnowledgeCollector {
    @Override
    public List<KnowledgePacket> collect() {
        System.out.println("[ImageCollector] 로컬/웹 이미지 인지 변환 가동...");
        // 1. 이미지 캡션 생성 및 OCR 텍스트 추출
        // 2. YOLO/COCO-SSD 객체 메타데이터 추출
        return new ArrayList<>();
    }
}
