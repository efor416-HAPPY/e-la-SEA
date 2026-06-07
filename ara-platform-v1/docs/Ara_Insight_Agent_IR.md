# Ara Insight Agent - 기업용 AI 인텔리전스 플랫폼

## 1. 제품 개요
**Ara Insight Agent**는 글로벌 언론 매체(미국, 중국, 유럽, 신흥국 등)와 경제 지표(FRED, OECD), 그리고 소셜 미디어(YouTube) 데이터를 실시간으로 수집·분석하여 경영진에게 확실성 높은 투자/경영 인사이트를 제공하는 **B2B AI 인텔리전스 에이전트 플랫폼**입니다.

단순한 뉴스 스크랩 서비스가 아닙니다. 자체적인 **교차 검증(Cross-Validation) 엔진**을 통해 전 세계 10여 개국 매체의 논조를 비교 분석하여 정보의 진위를 파악하고, MES/ERP 등 기업 내부 시스템과 연계하여 즉각적이고 실행 가능한 비즈니스 시나리오를 도출합니다.

## 2. 핵심 차별성 (Core Competencies)

### 글로벌 매체 교차 검증 (Global Cross-Validation)
- 뉴욕타임스(미국), 인민일보(중국), 파이낸셜타임스(영국), 르몽드(프랑스) 및 브라질/인도네시아/베트남 등 글로벌 주요 매체 실시간 크롤링.
- **CrossValidationEngine**: 상반된 보도나 가짜 뉴스를 필터링하여 정보의 '확실성 점수(Certainty Score)'를 부여. 확실성이 검증된 사실만을 바탕으로 인사이트 제공.

### 3계층 자아 인지 및 피드백 (Self-Awareness & Feedback)
- 수집된 정보의 신뢰도에 따라 에이전트 스스로 학습 가중치 조절 (`self_adaptation_weight`).
- **DLQ 및 Circuit Breaker (`resilience4j`)** 적용으로 API Rate Limit나 예외 상황에도 중단 없는 엔터프라이즈급 안정성 보장.

### 제조업/엔터프라이즈 연계 (MES/ERP/PLM Integration)
- 산출된 경제적 영향도(예: 금리 변동이 특정 원자재 가격에 미치는 영향)를 기업의 공급망 관리 시스템(SCM) 및 MES/ERP 요원으로 실시간 전송(`alert.generated` 토픽).

## 3. 기술 아키텍처 (Ara Enterprise Architecture v1.0)

- **Collector Layer**: `GlobalNewsCollector`, `YoutubeCollector`, `EconomicDataCollector` 병렬 구동.
- **Parser Layer**: `SimHash` 기반 유사도 분석으로 중복 정보 90% 이상 차단.
- **Reasoning Layer**: 교차 검증 및 이벤트 엔진 기반 실시간 알림 생성.
- **Memory Layer**: Qdrant Vector DB(비정형 문맥 보존)와 PostgreSQL(정형 알림/스코어 보존)의 하이브리드 구조.
- **Infrastructure**: 컨테이너화된 마이크로서비스(Docker/Kubernetes), Kafka 기반 이벤트 스트리밍.

## 4. 시장 진입 전략 및 PoC
- **Target**: 글로벌 공급망을 가진 제조/무역 기업의 C-Level 및 전략 기획실.
- **PoC 제안**: 기업의 기존 ERP 데이터 베이스 1개와 Ara Insight Agent를 연동하여 특정 원자재(예: 반도체, 구리) 시장 변화에 대한 실시간 알림 데모 시연.
