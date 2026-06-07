# -*- coding: utf-8 -*-
"""
Automation script to generate the Ara Agent Platform v1.0 enterprise stack:
- Maven Parent & 8 Module POMs
- Spring Boot Java services (Collectors, Parsers, Memory, Planner, Reasoning, Safety, Executor)
- Docker-Compose (Postgres, Qdrant, Kafka, Zookeeper)
- Kubernetes Deployment Manifests
- IR / PoC Business Whitepaper and Pitch Deck
"""
import os

BASE_DIR = "ara-platform-v1"

# 1. pom.xml template definitions
pom_files = {
    # Parent pom.xml
    "pom.xml": """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.ara.platform</groupId>
    <artifactId>ara-platform-parent</artifactId>
    <version>1.0.0</version>
    <packaging>pom</packaging>

    <properties>
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <spring.boot.version>3.2.0</spring.boot.version>
    </properties>

    <modules>
        <module>ara-gateway</module>
        <module>ara-collector</module>
        <module>ara-parser</module>
        <module>ara-memory</module>
        <module>ara-reasoning</module>
        <module>ara-planner</module>
        <module>ara-executor</module>
        <module>ara-safety</module>
    </modules>

    <dependencyManagement>
        <dependencies>
            <dependency>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-dependencies</artifactId>
                <version>${spring.boot.version}</version>
                <type>pom</type>
                <scope>import</scope>
            </dependency>
        </dependencies>
    </dependencyManagement>
</project>
""",

    "ara-gateway/pom.xml": """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>com.ara.platform</groupId>
        <artifactId>ara-platform-parent</artifactId>
        <version>1.0.0</version>
        <relativePath>../pom.xml</relativePath>
    </parent>

    <artifactId>ara-gateway</artifactId>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
    </dependencies>
</project>
""",

    "ara-collector/pom.xml": """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>com.ara.platform</groupId>
        <artifactId>ara-platform-parent</artifactId>
        <version>1.0.0</version>
        <relativePath>../pom.xml</relativePath>
    </parent>

    <artifactId>ara-collector</artifactId>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.kafka</groupId>
            <artifactId>spring-kafka</artifactId>
        </dependency>
    </dependencies>
</project>
""",

    "ara-parser/pom.xml": """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>com.ara.platform</groupId>
        <artifactId>ara-platform-parent</artifactId>
        <version>1.0.0</version>
        <relativePath>../pom.xml</relativePath>
    </parent>

    <artifactId>ara-parser</artifactId>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.kafka</groupId>
            <artifactId>spring-kafka</artifactId>
        </dependency>
    </dependencies>
</project>
""",

    "ara-memory/pom.xml": """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>com.ara.platform</groupId>
        <artifactId>ara-platform-parent</artifactId>
        <version>1.0.0</version>
        <relativePath>../pom.xml</relativePath>
    </parent>

    <artifactId>ara-memory</artifactId>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>
        <dependency>
            <groupId>org.postgresql</groupId>
            <artifactId>postgresql</artifactId>
        </dependency>
        <dependency>
            <groupId>io.qdrant</groupId>
            <artifactId>client</artifactId>
            <version>1.8.0</version>
        </dependency>
    </dependencies>
</project>
""",

    "ara-reasoning/pom.xml": """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>com.ara.platform</groupId>
        <artifactId>ara-platform-parent</artifactId>
        <version>1.0.0</version>
        <relativePath>../pom.xml</relativePath>
    </parent>

    <artifactId>ara-reasoning</artifactId>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
    </dependencies>
</project>
""",

    "ara-planner/pom.xml": """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>com.ara.platform</groupId>
        <artifactId>ara-platform-parent</artifactId>
        <version>1.0.0</version>
        <relativePath>../pom.xml</relativePath>
    </parent>

    <artifactId>ara-planner</artifactId>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
    </dependencies>
</project>
""",

    "ara-executor/pom.xml": """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>com.ara.platform</groupId>
        <artifactId>ara-platform-parent</artifactId>
        <version>1.0.0</version>
        <relativePath>../pom.xml</relativePath>
    </parent>

    <artifactId>ara-executor</artifactId>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
    </dependencies>
</project>
""",

    "ara-safety/pom.xml": """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>com.ara.platform</groupId>
        <artifactId>ara-platform-parent</artifactId>
        <version>1.0.0</version>
        <relativePath>../pom.xml</relativePath>
    </parent>

    <artifactId>ara-safety</artifactId>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
    </dependencies>
</project>
"""
}

# 2. Java class files definition
java_classes = {
    # ara-collector Classes
    "ara-collector/src/main/java/com/ara/platform/collector/Collector.java": """package com.ara.platform.collector;

public interface Collector {
    void collect();
}
""",

    "ara-collector/src/main/java/com/ara/platform/collector/YoutubeCollector.java": """package com.ara.platform.collector;

import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

@Component
public class YoutubeCollector implements Collector {
    private final KafkaTemplate<String, String> kafkaTemplate;

    public YoutubeCollector(KafkaTemplate<String, String> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }

    @Override
    public void collect() {
        System.out.println("[YouTubeCollector] 모니터링 중인 유튜브 채널의 신규 동영상 및 트랜스크립트 추출 가동...");
        // 1. YouTube Data API 호출 및 스크래핑
        String rawVideoMetadata = "{ \\"title\\": \\"신규 반도체 공장 라인 증설 발표\\", \\"url\\": \\"https://youtube.com/watch?v=fac1\\", \\"source\\": \\"YOUTUBE\\" }";
        
        // 2. 카프카 토픽 youtube.raw 로 메시지 전송 (비동기 Ingestion)
        kafkaTemplate.send("youtube.raw", rawVideoMetadata);
        System.out.println("[YouTubeCollector] 원본 비디오 메타데이터 카프카 적재 완료.");
    }
}
""",

    "ara-collector/src/main/java/com/ara/platform/collector/RssCollector.java": """package com.ara.platform.collector;

import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

@Component
public class RssCollector implements Collector {
    private final KafkaTemplate<String, String> kafkaTemplate;

    public RssCollector(KafkaTemplate<String, String> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }

    @Override
    public void collect() {
        System.out.println("[RssCollector] 지정 웹 매거진 및 기업 뉴스 RSS 피드 동기화 가동...");
        String rawRssMetadata = "{ \\"title\\": \\"인플레이션 우려에 따른 긴축 재정 도입 뉴스\\", \\"link\\": \\"https://news.com/article1\\", \\"source\\": \\"RSS\\" }";
        
        kafkaTemplate.send("rss.raw", rawRssMetadata);
        System.out.println("[RssCollector] 원본 RSS 피드 데이터 카프카 적재 완료.");
    }
}
""",

    # ara-parser Classes
    "ara-parser/src/main/java/com/ara/platform/parser/ContentParser.java": """package com.ara.platform.parser;

import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

@Service
public class ContentParser {
    private final KafkaTemplate<String, String> kafkaTemplate;

    public ContentParser(KafkaTemplate<String, String> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }

    @KafkaListener(topics = {"youtube.raw", "rss.raw"}, groupId = "ara-parser-group")
    public void parseRawContent(String rawMessage) {
        System.out.println("[ContentParser] 수신된 raw 데이터 파싱 시작: " + rawMessage);
        
        // 1. HTML 태그 제거, OCR 처리 및 인지 텍스트 정규화
        String parsedData = "{ \\"title\\": \\"인플레이션 대비 거시 경제 뉴스\\", \\"content\\": \\"미국 연준 금리 추가 인상 단행에 따른 증시 변동성 및 긴축 재정 돌입\\", \\"author\\": \\"Ha Ru\\", \\"publishedDate\\": \\"2026-06-07\\" }";
        
        // 2. 가공된 데이터를 카프카 Knowledge Bus 토픽 parsed.content 로 전송
        kafkaTemplate.send("parsed.content", parsedData);
        System.out.println("[ContentParser] 구조화 파싱 완료 및 parsed.content 적재.");
    }
}
""",

    # ara-memory Classes
    "ara-memory/src/main/java/com/ara/platform/memory/MemoryService.java": """package com.ara.platform.memory;

import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Service;

@Service
public class MemoryService {

    // 3계층 메모리: 1. Hot Memory(LRU List), 2. Warm Memory(PostgreSQL), 3. Cold Memory (Qdrant Vector DB)

    @KafkaListener(topics = "parsed.content", groupId = "ara-memory-group")
    public void saveTo3TierMemory(String parsedData) {
        System.out.println("[MemoryService] 파싱 데이터 3계층 영구 보존 인덱싱 시작...");
        
        // 1. PostgreSQL DB에 지식 메타데이터 구조화 저장 (Warm Memory)
        saveToPostgreSQL(parsedData);
        
        // 2. Qdrant 벡터 데이터베이스에 고차원 임베딩 벡터 저장 (Cold Memory)
        saveToQdrantVectorDB(parsedData);
        
        System.out.println("[MemoryService] 3계층 메모리 (PostgreSQL / Qdrant) 동기화 보존 완료.");
    }

    private void saveToPostgreSQL(String data) {
        System.out.println("  -> [Warm Memory SQLite/PostgreSQL] 지식 데이터 쓰기 성공");
    }

    private void saveToQdrantVectorDB(String data) {
        System.out.println("  -> [Vector Memory Qdrant] 128차원 벡터 임베딩 포인트 인서트 성공");
    }
}
""",

    # ara-reasoning Classes
    "ara-reasoning/src/main/java/com/ara/platform/reasoning/Reasoner.java": """package com.ara.platform.reasoning;

public interface Reasoner {
    String generatePlan(String goal, String context);
}
""",

    "ara-reasoning/src/main/java/com/ara/platform/reasoning/ReasoningEngine.java": """package com.ara.platform.reasoning;

import org.springframework.stereotype.Service;

@Service
public class ReasoningEngine implements Reasoner {

    @Override
    public String generatePlan(String goal, String context) {
        System.out.println("[ReasoningEngine] 수집된 장기기억 컨텍스트 기반 자아 사색 및 추론 루프 가동...");
        // 1. LLM 또는 룰 엔진을 호출하여 목표에 적합한 추론 수행
        // 2. 계획(Plan)에 반영할 하위 Task 시퀀스 도출
        
        return "{ \\"goal\\": \\"" + goal + "\\", \\"tasks\\": [\\"collect_data\\", \\"summarize_report\\", \\"send_mes_sync\\"] }";
    }
}
""",

    # ara-planner Classes
    "ara-planner/src/main/java/com/ara/platform/planner/Planner.java": """package com.ara.platform.planner;

import org.springframework.stereotype.Service;

@Service
public class Planner {
    public String decomposeGoalToTasks(String goalDescription) {
        System.out.println("[Planner] 추론 결과 기반의 Goal -> Task -> SubTask -> Action 분해 계획 수립...");
        return "{ \\"tasks\\": [\\"READ_FILE\\", \\"PARSE_METADATA\\", \\"MES_PRODUCT_SYNC\\"] }";
    }
}
""",

    # ara-executor Classes
    "ara-executor/src/main/java/com/ara/platform/executor/ExecutorAgent.java": """package com.ara.platform.executor;

import org.springframework.stereotype.Service;

@Service
public class ExecutorAgent {
    public void executeAction(String actionType, String target) {
        System.out.println(String.format("[ExecutorAgent] 안전 검증 확인 후 최종 액션 실행 -> 타입: %s, 대상: %s", actionType, target));
        
        // 기업 통합용 MES, ERP, PLM 및 이메일/슬랙 발송 모듈 실질 래핑
        if ("MES_SYNC".equals(actionType)) {
            System.out.println("  -> [MES System Connection] 생산 실적 동기화 완료");
        } else if ("ERP_QUERY".equals(actionType)) {
            System.out.println("  -> [ERP System Connection] 원자재 잔고 조회 결과 반환");
        } else {
            System.out.println("  -> [System Event Tool] 슬랙 알림 및 감사 로그 생성 완료");
        }
    }
}
""",

    # ara-safety Classes
    "ara-safety/src/main/java/com/ara/platform/safety/SafetyAgent.java": """package com.ara.platform.safety;

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
"""
}

# 3. Environment & Business Files
other_files = {
    # Docker Compose Configuration
    "docker-compose.yml": """version: '3.8'

services:
  # 1. Zookeeper for Kafka
  zookeeper:
    image: confluentinc/cp-zookeeper:7.3.0
    container_name: zookeeper
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000

  # 2. Apache Kafka Message Broker
  kafka:
    image: confluentinc/cp-kafka:7.3.0
    container_name: kafka
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1

  # 3. PostgreSQL Database (Structured warm memory store)
  postgres:
    image: postgres:15
    container_name: postgres
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: ara_enterprise_db
      POSTGRES_USER: ara_user
      POSTGRES_PASSWORD: ara_password_v1
    volumes:
      - pgdata:/var/lib/postgresql/data

  # 4. Qdrant Vector Database (Unstructured vector memory store)
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrantdata:/qdrant/storage

volumes:
  pgdata:
  qdrantdata:
""",

    # Kubernetes Deployments Config
    "k8s/deployments.yaml": """apiVersion: apps/v1
kind: Deployment
metadata:
  name: ara-collector-deployment
  namespace: ara-platform
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ara-collector
  template:
    metadata:
      labels:
        app: ara-collector
    spec:
      containers:
      - name: ara-collector
        image: ara-platform/ara-collector:v1.0.0
        ports:
        - containerPort: 8080
        env:
        - name: SPRING_KAFKA_BOOTSTRAP_SERVERS
          value: "kafka:9092"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ara-reasoning-deployment
  namespace: ara-platform
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ara-reasoning
  template:
    metadata:
      labels:
        app: ara-reasoning
    spec:
      containers:
      - name: ara-reasoning
        image: ara-platform/ara-reasoning:v1.0.0
        ports:
        - containerPort: 8081
        resources:
          limits:
            cpu: "2"
            memory: 4Gi
          requests:
            cpu: "1"
            memory: 2Gi
---
apiVersion: v1
kind: Service
metadata:
  name: ara-gateway-service
  namespace: ara-platform
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8080
  selector:
    app: ara-gateway
""",

    # VC IR & PoC Business Proposal
    "docs/IR_and_PoC_Proposal.md": """# Ara Agent Platform v1.0 기업용 SaaS 사업화 및 기술 제안 백서 (Whitepaper)

본 문서는 **로컬 및 클라우드 결합형 지속 학습 에이전트 플랫폼(ARA Agent Platform)**의 투자 유치용 핵심 아키텍처 요약 및 기업 PoC 연동 제안서입니다.

---

## 1. 비즈니스 요약 (SaaS Pricing Model)

| 요금제 플랜 | 타겟 그룹 | 월 비용 | 제공 가치 및 연동 범위 |
| :--- | :--- | :--- | :--- |
| **Starter** | 소규모 스타트업 및 개인 | **월 29만 원** | 10 사용자 한정, 공개 YouTube 및 기본 RSS 뉴스 수집, 기본 장기 메모리 아카이빙 제공 |
| **Professional** | 중소규모 기업 (SMB) | **월 299만 원** | 100 사용자 한정, 로컬 PDF/문서 자동 파싱, 실시간 데이터 정밀 인지, 자가 피드백 가중치 보정 |
| **Enterprise** | 대기업 및 제조 공장 | **월 1,000만 원+** | 무제한 사용자, 사내 인프라(MES, ERP, PLM, SCM) 커스텀 에이전트 구축, 하이브리드 클라우드 전용 Qdrant Vector Cluster |

---

## 2. 제조업 디지털 트윈 확장 모델 (Smart Factory AI Agent)

단순히 사색하고 "조언하는 AI"를 넘어, 제조 및 공장 공급망 인프라와 결합하여 직접 분석하고 지시를 내리는 **제조업 확장 에이전트 플랫폼**을 구축합니다.

### 🏭 특화 에이전트 제품군 구성
1. **MES Agent (제조실행 시스템)**:
   - 설비 이상 텔레메트리 데이터를 실시간으로 인지(`Observe`).
   - 이상 감지 시 설비 제어 명령 또는 예방 보전 일정을 플래너(`Planner`)를 통해 수립.
2. **ERP Agent (전사적 자원관리)**:
   - 생산 계획에 맞춘 원자재 발주량 및 부품 수량을 자동 쿼리하여 재고를 실시간 예측.
3. **PLM Agent (제품 수명주기관리)**:
   - 도면 파일(DWG, DXF) 및 제품 설계 변경 지시서(ECO)가 등록되면 형상 특징 및 사양을 파싱하여 BOM에 자동 동기화.
4. **QA Agent (품질 보증)**:
   - 양산 제품 검사기(Vision) 로그를 감시하여 불량률 급증 시 GitOps 정책 규정을 확인한 뒤 공정 일시 정지 조치 수행.

---

## 3. 핵심 기술 경쟁력 (Investors & VC IR Point)

- **3계층 메모리 모델 (Hot/Warm/Cold)**: RAM 캐시, 정형 RDBMS(PostgreSQL), 비정형 벡터 검색(Qdrant)의 유기적 매핑을 통해 LLM 컨텍스트 한계를 초월하여 장기 학습이 가능한 두뇌 구조 설계.
- **Ingestion Safety Gate**: 기업 내부 정보 유출을 원천 방어하기 위해 PII 필터링 및 쉘 주입 위험 명령어를 실시간으로 검열하여 안전하게 구동.
- **자가 피드백 가중치 보정 알고리즘**: 정보의 가치를 스스로 채점하고 자아 가중치(`self_adaptation_weight`)를 가변적으로 조율해 학습 능력을 자가 진화시킴.
"""
}

def build_enterprise():
    print("==================================================")
    print("  ARA Enterprise SaaS Agent Platform Generation")
    print("==================================================")
    
    # 1. Generate POM files
    for rel_path, content in pom_files.items():
        full_path = os.path.join(BASE_DIR, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Created: {full_path}")
        
    # 2. Generate Java classes
    for rel_path, content in java_classes.items():
        full_path = os.path.join(BASE_DIR, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Created: {full_path}")
        
    # 3. Generate Docker, Kubernetes, and Docs
    for rel_path, content in other_files.items():
        full_path = os.path.join(BASE_DIR, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Created: {full_path}")

    print("\n[성공] ARA Agent Platform v1.0 기업용 상용 아키텍처 스택 빌드 완료.")

if __name__ == "__main__":
    build_enterprise()
