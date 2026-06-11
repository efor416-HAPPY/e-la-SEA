# 🚨 ARA 3.0 ARCHITECTURE — 불변 규칙 (IMMUTABLE)

> **이 문서는 ARA 프로젝트의 절대 불변 아키텍처 규칙입니다.**
> **어떤 상황에서도 이 구조를 변경, 삭제, 우회, 단순화할 수 없습니다.**
> **모든 코드 수정은 이 규칙을 준수해야 합니다.**

---

## 1. 인지 사이클 (Cognitive Cycle) — 절대 고정

```
인지(Perception)
  ↓
기억(Memory)
  ↓
추론(Reasoning)
  ↓
계획(Plan)
  ↓
실행(Action)
  ↓
관찰(Observation)
  ↓
학습(Learning)
  ↓
기억 강화(Memory Reinforcement)
```

- 이 8단계 사이클은 **절대 생략, 축소, 병합할 수 없습니다.**
- 모든 외부 자극은 반드시 `perception`으로 시작해야 합니다.
- 모든 실행 결과는 반드시 `observation` → `learning`을 거쳐야 합니다.

---

## 2. CognitiveBus (중추 신경계) — 절대 고정

### 2.1 구조
- **Pub/Sub 토픽 기반** Thought 전파 (1:N broadcast)
- **Priority Queue** — 중요도(importance) 순 처리
- **Thought cascade** — 에이전트 반응이 다시 bus로 전파
- **글로벌 훅** — EmotionEngine, KnowledgeGraph, MemoryCore 자동 연결

### 2.2 토픽 구독 맵 (최소 보장)

| 토픽 | 구독 에이전트 | 목적 |
|---|---|---|
| `perception` | memory, planner | 외부 자극 → 자동 기억 + 자동 계획 |
| `dialogue` | memory, chat | 대화 → 자동 기억 + 응답 |
| `reasoning` | memory | 추론 결과 → 자동 기억 |
| `learning` | memory | 학습 → LTM 직접 저장 |
| `observation` | memory | 관찰 → 자동 기억 |
| `plan` | planner | 계획 → 실행 추적 |

- 에이전트를 추가할 때 **기존 토픽 구독을 제거할 수 없습니다.**
- 새 토픽은 추가 가능하지만 기존 맵은 불변입니다.

### 2.3 금지 사항
- ❌ 1:1 직접 dispatch만으로 시스템을 구성하는 것
- ❌ CognitiveBus를 우회하여 에이전트 간 직접 호출
- ❌ 글로벌 훅(Emotion, KnowledgeGraph, Memory)을 제거

---

## 3. Thought (인지 단위) — 절대 고정

### 3.1 필수 필드

```python
class Thought:
    id: str              # UUID
    parent_id: str       # 추론 체인 추적
    source: str          # 발신 에이전트
    thought_type: str    # THOUGHT_TYPES 중 하나
    content: str         # 핵심 내용
    importance: float    # 0.0 ~ 1.0
    emotion: dict        # 감정 컨텍스트
    context: dict        # 추가 맥락
    metadata: dict       # 메타데이터
    timestamp: float     # 생성 시각
    trace: list[str]     # 전파 경로
```

### 3.2 Thought Types (최소 보장)

```
perception, memory, reasoning, plan, action,
observation, learning, emotion, dialogue, system
```

- 이 10개 타입은 **삭제할 수 없습니다.**
- 새 타입은 추가 가능합니다.

---

## 4. 5계층 기억 시스템 (Memory) — 절대 고정

```
STM (단기기억, 30s~5min)
  ↓ decay + promote
MTM (중기기억, 1h~24h)
  ↓ consolidate
LTM (장기기억, 영구)
  ↕
Vector (벡터 유사도 검색)
  ↕
Episode (에피소드/경험 기억)
```

### 4.1 계층 규칙
- STM → MTM: 중요도 0.7 이상 또는 접근 3회 이상 시 자동 승격
- MTM → LTM: 접근 5회 이상 또는 중요도 0.8 이상 시 자동 통합
- 기억 통합(consolidation)은 **반드시 백그라운드 루프**로 수행
- `perceive()` API: Thought 기반 입력 → 중요도별 계층 자동 분배

### 4.2 금지 사항
- ❌ 단일 계층(store/search만)으로 퇴화시키는 것
- ❌ 자동 기억 통합(consolidation)을 제거하는 것
- ❌ 에피소드 기억을 제거하는 것

---

## 5. EmotionEngine (감정 엔진) — 절대 고정

### 5.1 감정 차원 (5차원)

| 차원 | 설명 | 범위 |
|---|---|---|
| `curiosity` | 탐구심 | 0.0 ~ 1.0 |
| `confidence` | 확신 | 0.0 ~ 1.0 |
| `attention` | 주의력 | 0.0 ~ 1.0 |
| `fatigue` | 피로도 | 0.0 ~ 1.0 |
| `empathy` | 공감 | 0.0 ~ 1.0 |

### 5.2 규칙
- 모든 Thought는 EmotionEngine을 통과해야 합니다 (CognitiveBus 글로벌 훅)
- 감정은 응답 톤, 기억 중요도, 추론 깊이에 영향을 줍니다
- 시간에 따른 baseline 수렴(decay)이 항상 동작해야 합니다

### 5.3 금지 사항
- ❌ 감정 엔진을 비활성화하거나 우회하는 것
- ❌ 5개 차원 중 하나라도 삭제하는 것

---

## 6. KnowledgeGraph (지식 그래프) — 절대 고정

### 6.1 구조
- 노드(KnowledgeNode): 개념 (label, concept_type, properties)
- 엣지(KnowledgeEdge): 관계 (relation, weight, reinforcement)
- BFS 탐색으로 관련 개념 발견
- 경로 탐색(find_path)으로 개념 간 연결 추론

### 6.2 규칙
- 모든 Thought에서 자동 개념 추출 (CognitiveBus 글로벌 훅)
- 동시 등장 개념 간 `co_occurs` 관계 자동 강화
- 시드 개념(경제/시사) 삭제 금지

### 6.3 금지 사항
- ❌ 지식 그래프를 제거하는 것
- ❌ 자동 추출 훅을 비활성화하는 것

---

## 7. PlannerEngine (계획 엔진) — 절대 고정

### 7.1 계획 수명
```
Goal → Plan → Steps → Execute → Observe → Adapt → Learn
```

### 7.2 규칙
- 중요도 0.7 이상 perception → 자동 계획 생성
- 각 단계(PlanStep)는 상태 추적: pending → running → completed/failed
- 실행 결과 관찰(observation) 후 계획 적응(adaptation) 가능
- 완료된 계획은 에피소드 기억으로 기록

### 7.3 금지 사항
- ❌ if/elif 분기 기반 계획으로 퇴화시키는 것
- ❌ 실행 추적 없이 계획을 수립하는 것

---

## 8. AgentRuntime + RecoveryEngine (자가 치유) — 절대 고정

### 8.1 규칙
- 모든 인지 에이전트는 ICognitiveAgent를 상속해야 합니다
- 헬스체크 모니터링이 항상 실행되어야 합니다
- 장애 감지 시 스냅샷 복원 → 자동 재시작 (최대 3회)
- 에이전트 상태 스냅샷이 주기적으로 저장되어야 합니다

### 8.2 금지 사항
- ❌ 에이전트를 IAgent(레거시)로 새로 만드는 것
- ❌ RecoveryEngine을 비활성화하는 것

---

## 9. 커널 구조 (AraKernel) — 절대 고정

```
AraKernel
├── CognitiveBus        (중추 신경계)
├── MemoryCore           (5계층 기억)
├── EmotionEngine        (감정 엔진)
├── KnowledgeGraph       (지식 그래프)
├── ReasoningCore        (추론 엔진)
├── PlannerEngine        (계획 엔진)
├── SecurityCore         (보안)
├── AuditCore            (감사)
├── AgentRuntime         (에이전트 수명 관리)
├── RecoveryEngine       (자가 치유)
└── Agents               (인지 에이전트들)
```

- 이 11개 모듈은 **절대 제거할 수 없습니다.**
- 새 모듈은 추가 가능하지만 기존 모듈은 불변입니다.
- 부팅 시 모든 서브시스템 상태가 출력되어야 합니다.

---

## 10. 하위 호환성 — 절대 유지

| 기존 API | 보장 방법 |
|---|---|
| `kernel.bus.dispatch(Message)` | CognitiveBus.dispatch() 래퍼 |
| `memory_core.store(MemoryItem)` | STM + LTM 동시 저장 |
| `memory_core.search(query)` | 다계층 통합 검색 |
| `memory_core.get_stats()` | (hot, warm, cold) 튜플 반환 |
| `IAgent.process(Message)` | ICognitiveAgent.process() 자동 변환 |

- 기존 FastAPI 엔드포인트는 항상 동작해야 합니다.
- 레거시 API를 제거할 수 없습니다.

---

> **⚠️ 이 문서를 위반하는 어떤 코드 변경도 거부되어야 합니다.**
> **이 규칙은 ARA 프로젝트가 존재하는 한 영구적으로 적용됩니다.**
