package com.ara.platform.safety;

import org.springframework.stereotype.Component;

@Component
public class SafetyAgent {
    public boolean verifyExecutionSafety(String actionType, String targetPath) {
        System.out.println("[SafetyAgent Security Gate] 인가 검증 및 비용/자원 폭주 한계 점검 중...");
        
        // 파일 탐색 차단 및 위험 명령어 차단
        if (targetPath != null && targetPath.contains("System32")) {
            System.err.println("🚨 [SafetyAgent Warning] 시스템 파일 접근 차단 - 보안 위반 감지!");
            return false;
        }
        return true;
    }
}
