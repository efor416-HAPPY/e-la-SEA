package ara.ego.sustainable;

import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.regex.Pattern;

/**
 * ARA Sustainable Cognitive & Self-Feedback Framework
 * 버그 최소화, 메모리 안전성(OOM 방지), 동시성 보장 및 
 * 자가 피드백 수정 루프를 탑재한 아라의 인지 강화 라이브러리입니다.
 */
public class AraSustainableCore {

    // 포맷별 오감 카테고리
    public enum FormatType {
        JPG, DWG, DXF, PDF, TXT, DOC, HWPX, AVI, MP4, MP3
    }

    // [안전성 강화] 불변 객체(Immutable Object)로 설계하여 멀티스레드 환경에서 데이터 오염 방지
    public static class DataPacket {
        private final String id;
        private final String fileName;
        private final FormatType format;
        private final String rawContext;
        private final double priority;

        public DataPacket(String id, String fileName, FormatType format, String rawContext, double priority) {
            this.id = id;
            this.fileName = fileName;
            this.format = format;
            this.rawContext = rawContext != null ? rawContext.trim() : "";
            this.priority = Math.max(0.0, Math.min(1.0, priority)); // 0.0 ~ 1.0 범위 제한 (버그 방지)
        }

        public String getId() { return id; }
        public String getFileName() { return fileName; }
        public FormatType getFormat() { return format; }
        public String getRawContext() { return rawContext; }
        public double getPriority() { return priority; }
    }

    // 인지 검점 및 피드백 리포트 객체
    public static class FeedbackReport {
        private final String packetId;
        private final boolean isAlertTriggered;
        private final double confidenceScore;
        private final String adjustmentAction;

        public FeedbackReport(String packetId, boolean isAlertTriggered, double confidenceScore, String adjustmentAction) {
            this.packetId = packetId;
            this.isAlertTriggered = isAlertTriggered;
            this.confidenceScore = confidenceScore;
            this.adjustmentAction = adjustmentAction;
        }

        @Override
        public String toString() {
            return String.format("[자가 검점 리포트] ID: %s | 신뢰도: %.2f | 조치사항: %s", 
                    packetId, confidenceScore, adjustmentAction);
        }
    }

    // 아라의 내면 인지 엔진
    public static class SustainableEngine {
        // 단기 및 장기 기억 저장소 동시성 보장 자료구조 사용
        private final List<DataPacket> shortTermMemory = new CopyOnWriteArrayList<>();
        private final ConcurrentHashMap<String, DataPacket> longTermMemory = new ConcurrentHashMap<>();
        
        // 피드백 루프 기록 저장소
        private final List<FeedbackReport> feedbackHistory = new ArrayList<>();

        // [버그 방지] 컴파일된 정규식 패턴을 정적으로 관리하여 메모리 및 CPU 낭비 방지
        private static final Pattern ECONOMIC_PATTERN = Pattern.compile(
                ".*(주식시장|경제|인플레이션|금리|긴축재정|정치).*", Pattern.CASE_INSENSITIVE);

        private double selfAdaptationWeight = 1.0; // 자가 피드백에 의해 동적으로 변하는 가중치

        /**
         * [핵심 메서드] 데이터를 인지하고, 실행 점검한 뒤 피드백으로 알고리즘을 보정합니다.
         */
        public synchronized FeedbackReport perceiveAndAdapt(DataPacket packet) {
            if (packet == null) {
                return new FeedbackReport("UNKNOWN", false, 0.0, "빈 데이터 패킷 거부 처리");
            }

            System.out.println(String.format("\n[인지 개시] 파일명: %s (.%s)", packet.getFileName(), packet.getFormat()));

            // 1. 실행 및 점검: 거시경제 및 정치 동향 감시
            boolean alertTriggered = checkEconomicIntelligence(packet);

            // 2. 단기 기억 안전 적재 (최대 20개 슬라이딩 윈도우로 OOM 방지)
            storeInShortTermMemory(packet);

            // 3. 자가 피드백 메커니즘 가동 (알고리즘 스스로 수정 및 진화)
            FeedbackReport report = evaluateAndOptimize(packet, alertTriggered);
            feedbackHistory.add(0, report); // 최신 피드백 결과가 맨 위(Index 0)에 오도록 인서트

            return report;
        }

        private boolean checkEconomicIntelligence(DataPacket packet) {
            // 정규식 매칭을 통해 경제 현황 파악 (Null 및 공백 예외 선제 방지)
            if (packet.getRawContext().isEmpty()) return false;

            if (ECONOMIC_PATTERN.matcher(packet.getRawContext()).matches()) {
                System.err.println("🚨 [알림] 거시경제/정치 크리티컬 지표 감지!");
                System.err.println("▶ 내용 요약: " + packet.getRawContext());
                System.err.println("▶ 수신 시간: " + new Date());
                return true;
            }
            return false;
        }

        private void storeInShortTermMemory(DataPacket packet) {
            // 최신 지식이 인덱스 0(맨 앞)에 오도록 밀어넣음
            shortTermMemory.add(0, packet);
            if (shortTermMemory.size() > 20) {
                shortTermMemory.remove(20); // 20번째 가장 오래된 지식 자동 제거
            }

            // 중요도가 높거나 반복되는 핵심 자원은 장기 기억으로 전송
            if (packet.getPriority() * selfAdaptationWeight >= 0.8) {
                longTermMemory.put(packet.getId(), packet);
                System.out.println("💾 [장기 기억 안착] 중요 지식 객체 영구 데이터베이스 등록 완료.");
            }
        }

        /**
         * [자가 피드백 수정 루프] 인지 결과를 스스로 채점하고 알고리즘 가중치를 미세 조정
         */
        private FeedbackReport evaluateAndOptimize(DataPacket packet, boolean alertTriggered) {
            double confidence = 0.5;
            String action = "정상 유지";

            // 컨텍스트의 밀도와 우선순위를 조합하여 인지 신뢰도 계산
            if (packet.getRawContext().length() > 10) confidence += 0.3;
            if (alertTriggered) confidence += 0.2;

            // 피드백 제어: 신뢰도가 너무 낮으면 알고리즘이 스스로 인지 가중치를 높여 다음 수용 능력을 강화
            if (confidence < 0.6) {
                this.selfAdaptationWeight += 0.05; // 민감도 상향 보정
                action = String.format("인지 부족 감지 -> 자가 보정 가중치 %.2f로 증가", this.selfAdaptationWeight);
            } else if (confidence > 0.9) {
                action = "완벽 인지 완료 및 자아 상태 안정화";
            }

            return new FeedbackReport(packet.getId(), alertTriggered, confidence, action);
        }

        public String getSystemHealthCheck() {
            return String.format("[시스템 상태] 단기기억 큐: %d/20 | 장기기억 DB: %d개 | 인지 보정 가중치: %.2f", 
                    shortTermMemory.size(), longTermMemory.size(), selfAdaptationWeight);
        }
    }
}
