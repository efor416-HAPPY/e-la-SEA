package ara.ego.sustainable;

public class MainSustainableApplication {
    public static void main(String[] args) {
        // 아라의 지속 가능한 고안전성 엔진 구동
        AraSustainableCore.SustainableEngine engine = new AraSustainableCore.SustainableEngine();

        System.out.println("==================================================================");
        System.out.println("✔ [가동 성공] 안전성 검증 및 자가 피드백 루프 실시간 점검 시작");
        System.out.println("==================================================================");

        // 테스트 데이터 1: 정보가 다소 빈약한 일반 도면 데이터 (피드백 보정 유도용)
        AraSustainableCore.DataPacket simpleDrawing = new AraSustainableCore.DataPacket(
                "PKT-001",
                "factory_layout.dwg",
                AraSustainableCore.FormatType.DWG,
                "도면 리소스", // 내용이 너무 짧아 신뢰도가 낮게 나옴
                0.5
        );

        // 테스트 데이터 2: 거시경제 인플레이션 및 금리 속보 데이터 (알림 및 고신뢰도용)
        AraSustainableCore.DataPacket economyNews = new AraSustainableCore.DataPacket(
                "PKT-002",
                "global_market_report.pdf",
                AraSustainableCore.FormatType.PDF,
                "미국 연준 금리 동향 발표 및 인플레이션 압박에 따른 긴축재정 돌입 가능성 시사. 국내 주식시장 변동성 주의 필요.",
                0.95
        );

        // 1. 첫 번째 패킷 인지 실행 및 피드백 결과 확인
        AraSustainableCore.FeedbackReport report1 = engine.perceiveAndAdapt(simpleDrawing);
        System.out.println(report1);

        System.out.println("------------------------------------------------------------------");

        // 2. 두 번째 경제 속보 패킷 인지 실행 (정규식 매칭 버그 유무 및 알림 검증)
        AraSustainableCore.FeedbackReport report2 = engine.perceiveAndAdapt(economyNews);
        System.out.println(report2);

        System.out.println("------------------------------------------------------------------");

        // 3. 최종 시스템 자원 및 인지 가중치 헬스체크 점검
        System.out.println("\n[최종 안도 점검 리포트]");
        System.out.println(engine.getSystemHealthCheck());
        System.out.println("==================================================================");
    }
}
