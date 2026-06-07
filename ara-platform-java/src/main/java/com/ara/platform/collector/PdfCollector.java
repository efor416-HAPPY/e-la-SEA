package com.ara.platform.collector;

import com.ara.platform.model.KnowledgePacket;
import java.util.ArrayList;
import java.util.List;

/**
 * 안전한 경로의 학술/매뉴얼 PDF 문서 전용 수집기
 */
public class PdfCollector implements KnowledgeCollector {
    private String directoryPath;

    public PdfCollector(String directoryPath) {
        this.directoryPath = directoryPath;
    }

    @Override
    public List<KnowledgePacket> collect() {
        System.out.println("[PdfCollector] 안전 디렉토리 (" + directoryPath + ") 스캔...");
        // 1. PDF 텍스트 추출
        return new ArrayList<>();
    }
}
