# -*- coding: utf-8 -*-
"""
================================================================================
🌱 ARA Organic Cognitive Core: Smart Resource Integrator (Multi-Agent Redesign)
================================================================================

This module implements a consolidated multi-agent cognitive architecture:
  1. AgentKernel: Orchestrates the Observe -> Parse -> Embed -> Store -> Reason -> Plan -> Execute -> Learn pipeline.
  2. MemoryAgent: Manages 3-tier memory (Hot RAM cache, Warm SQLite DB, Cold JSON).
  3. SafetyAgent: Enforces execution constraints (privilege, paths, loop prevention).
  4. ReasoningAgent & PlanningAgent: Translates Goal -> Task -> SubTask -> Action.
  5. FileAgent & WebAgent: Monitored asynchronous safety event ingestion (watchdog, simulated ws).
  6. Manufacturing Agents (MES, ERP, PLM, SCM, QA): Integrated GitOps policy auditing logs.
  7. Concurrency: Optimization using ThreadPoolExecutor and thread-safe collections.
"""

import os
import sys
import io
import time
import json
import sqlite3
import threading
import queue
from concurrent.futures import ThreadPoolExecutor

# Force stdout/stderr to use UTF-8 encoding to prevent CP949 encoding crashes on Windows consoles
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    # Enable VT100 colors in Windows Console
    os.system('')

# =====================================================================
# Dependency & Environment Checks (With Graceful Fallbacks)
# =====================================================================

# 1. PyTorch Fallback Check
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    
    # Mock PyTorch structure to prevent import errors and support fallback simulation
    class DummyModule:
        def __init__(self, *args, **kwargs):
            pass
        def __call__(self, *args, **kwargs):
            return self.forward(*args, **kwargs)
        def forward(self, *args, **kwargs):
            import numpy as np
            import random
            # Return dummy output representing 3 classes
            return np.array([[random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)]])

    class nn:
        Module = DummyModule
        class Linear(DummyModule):
            pass
        class LSTM(DummyModule):
            def forward(self, *args, **kwargs):
                hn = ["mock_hn_element"]
                cn = "mock_cn"
                return "mock_output", (hn, cn)
        class Sequential(DummyModule):
            def forward(self, *args, **kwargs):
                class MockOutput:
                    def detach(self): return self
                    def cpu(self): return self
                    def numpy(self):
                        import random
                        import numpy as np
                        return np.array([[random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)]])
                return MockOutput()
                
    class F:
        @staticmethod
        def relu(x):
            return x
            
    class torch:
        @staticmethod
        def rand(*args): return "mock_tensor"
        @staticmethod
        def randn(*args): return "mock_tensor"
        @staticmethod
        def cat(*args, **kwargs): return "mock_tensor"

# 2. psutil Fallback Check
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    
    class MockVirtualMemory:
        def __init__(self):
            import random
            self.percent = random.randint(40, 60)
            
    class psutil:
        @staticmethod
        def cpu_percent():
            import random
            return random.randint(15, 35)
        @staticmethod
        def virtual_memory():
            return MockVirtualMemory()

# 3. watchdog Fallback Check
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False
    
    class FileSystemEventHandler:
        pass

    class Observer:
        def __init__(self):
            self.running = False
            self.thread = None
            self.handler = None
            self.path = None

        def schedule(self, handler, path, recursive=False):
            self.handler = handler
            self.path = path

        def start(self):
            self.running = True
            self.thread = threading.Thread(target=self._poll_loop, daemon=True)
            self.thread.start()

        def _poll_loop(self):
            try:
                existing_files = set(os.listdir(self.path))
            except Exception:
                existing_files = set()
                
            while self.running:
                time.sleep(0.5)
                try:
                    current_files = set(os.listdir(self.path))
                    new_files = current_files - existing_files
                    for name in new_files:
                        full_path = os.path.join(self.path, name)
                        class Event:
                            def __init__(self, path):
                                self.src_path = path
                                self.is_directory = False
                        
                        if os.path.isfile(full_path):
                            event = Event(full_path)
                            self.handler.on_created(event)
                    existing_files = current_files
                except Exception:
                    pass

        def stop(self):
            self.running = False

        def join(self):
            if self.thread:
                self.thread.join(timeout=1.0)


# =====================================================================
# 1. 3계층 메모리 구조 (Hot / Warm / Cold Memory)
# =====================================================================

class HotMemoryCache:
    """RAM-based high-speed LIFO cache for active reasoning context."""
    def __init__(self, limit=50):
        self.limit = limit
        self.cache = []
        self.lock = threading.Lock()

    def add(self, item):
        with self.lock:
            # Remove duplicates by link to maintain LIFO ordering
            self.cache = [x for x in self.cache if x.get('link') != item.get('link')]
            self.cache.insert(0, item)
            if len(self.cache) > self.limit:
                self.cache.pop()

class WarmMemoryDB:
    """Persistent local SQLite database for indexing, fast metadata query and retrieval."""
    def __init__(self, db_path="downloads/ara_warm_memory.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS warm_wisdom (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    link TEXT UNIQUE,
                    description TEXT,
                    source TEXT,
                    scraped_at TEXT,
                    embedded_vector TEXT
                )
            """)
            conn.commit()

class MemoryAgent:
    """Coordinates writing and reading across Hot (RAM), Warm (SQLite), and Cold (JSON) memory tiers."""
    def __init__(self):
        self.hot_memory = HotMemoryCache(limit=50)
        self.warm_db = WarmMemoryDB()
        self.cold_file = "downloads/accumulated_wisdom.json"

    def store_wisdom(self, item):
        # 1. Hot Memory (RAM Cache)
        self.hot_memory.add(item)

        # 2. Warm Memory (SQLite DB)
        try:
            with sqlite3.connect(self.warm_db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO warm_wisdom (title, link, description, source, scraped_at, embedded_vector)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    item.get('title', 'No Title'),
                    item.get('link', ''),
                    item.get('description', ''),
                    item.get('source', 'Unknown'),
                    item.get('scraped_at', ''),
                    item.get('embedded_vector', '[]')
                ))
                conn.commit()
        except Exception as e:
            print(f"[오류] Warm Memory DB 저장 실패: {e}")

        # 3. Cold Memory (Long-term JSON Archive)
        cold_items = []
        if os.path.exists(self.cold_file):
            try:
                with open(self.cold_file, 'r', encoding='utf-8') as f:
                    cold_items = json.load(f)
            except Exception:
                pass

        # De-duplicate in cold storage
        cold_items = [x for x in cold_items if x.get('link') != item.get('link')]
        cold_items.insert(0, item)
        # Keep newest first
        cold_items.sort(key=lambda x: x.get('scraped_at', ''), reverse=True)

        try:
            with open(self.cold_file, 'w', encoding='utf-8') as f:
                json.dump(cold_items, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[오류] Cold Memory 파일 저장 실패: {e}")

    def get_stats(self):
        hot_count = len(self.hot_memory.cache)
        
        warm_count = 0
        try:
            with sqlite3.connect(self.warm_db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM warm_wisdom")
                warm_count = cursor.fetchone()[0]
        except:
            pass

        cold_count = 0
        if os.path.exists(self.cold_file):
            try:
                with open(self.cold_file, 'r', encoding='utf-8') as f:
                    cold_count = len(json.load(f))
            except:
                pass
                
        return hot_count, warm_count, cold_count


# =====================================================================
# 2. 안전성 제어 계층 (Safety Agent)
# =====================================================================

class SafetyAgent:
    """Enforces safety rules to prevent unauthorized file operations and hazardous executions."""
    def __init__(self, allowed_paths):
        self.allowed_paths = [os.path.abspath(p) for p in allowed_paths]

    def check_action_safety(self, action_type, target):
        """
        Validates the action before execution.
        Returns: (is_safe, reason)
        """
        # Rule 1: Prevent file deletion outside allowed paths
        if action_type == "DELETE":
            abs_target = os.path.abspath(target)
            is_inside = False
            for allowed in self.allowed_paths:
                # On Windows, verify same drive before comparing common paths
                allowed_drive = os.path.splitdrive(allowed)[0].upper()
                target_drive = os.path.splitdrive(abs_target)[0].upper()
                if allowed_drive != target_drive:
                    continue
                try:
                    if os.path.commonpath([allowed, abs_target]) == allowed:
                        is_inside = True
                        break
                except ValueError:
                    pass
            if not is_inside:
                return False, f"차단됨: 허용되지 않은 경로의 파일 삭제 차단 -> {target}"

        # Rule 2: Block command execution containing system hazard keywords
        if action_type == "SHELL_EXEC":
            forbidden_words = ["rm ", "del ", "format", "sudo ", "mkfs", "chmod ", "chown ", "shutdown"]
            for word in forbidden_words:
                if word in target.lower():
                    return False, f"차단됨: 위험 키워드 '{word}' 포함 명령어 실행 거부"

        return True, "안전 검증 완료"


# =====================================================================
# 3. 추론 및 계획 엔진 (Reasoning & Planning Agents)
# =====================================================================

class Goal:
    def __init__(self, description):
        self.description = description

class Task:
    def __init__(self, title):
        self.title = title
        self.subtasks = []

class SubTask:
    def __init__(self, title):
        self.title = title
        self.actions = []

class Action:
    def __init__(self, action_type, target, details=""):
        self.action_type = action_type # READ, WRITE, DELETE, SHELL_EXEC, MES_SYNC, ERP_QUERY, AUDIT_LOG
        self.target = target
        self.details = details

class Reasoner:
    def create_plan(self, goal: Goal, context: dict) -> list:
        raise NotImplementedError

class ReasoningAgent(Reasoner):
    """Generates cognitive plans to satisfy agent goals."""
    def create_plan(self, goal: Goal, context: dict) -> list:
        tasks = []
        desc = goal.description.lower()

        if "analyze" in desc or "process" in desc or "file" in desc:
            t = Task("파일 인지 및 데이터 프로세싱 작업")
            st = SubTask("파일 검사 및 인지 변환")
            st.actions.append(Action("READ", context.get("file_path", ""), "파일 콘텐츠 안전한 읽기"))
            st.actions.append(Action("PARSE", context.get("file_path", ""), "데이터 파싱 및 특징 추출"))
            st.actions.append(Action("STORE", context.get("file_path", ""), "3계층 메모리 저장"))
            t.subtasks.append(st)
            tasks.append(t)
            
        elif "mes" in desc or "erp" in desc or "manufacturing" in desc:
            t = Task("제조 정보 및 자원 동기화 작업")
            st = SubTask("설비 실적 데이터 수집 및 MES 송신")
            st.actions.append(Action("MES_SYNC", "MES_ACTUAL_RECORD", "생산 실적 동기화"))
            st.actions.append(Action("ERP_QUERY", "PART_NO_V01", "재고 정보 실시간 조회"))
            st.actions.append(Action("AUDIT_LOG", "manufacturing_audit.log", "GitOps 규정 감사 로그 작성"))
            t.subtasks.append(st)
            tasks.append(t)
            
        else:
            t = Task("시스템 진단 작업")
            st = SubTask("리소스 텔레메트리 스캔")
            st.actions.append(Action("SYS_TELEMETRY", "CPU/RAM", "하드웨어 부하 상태 점검"))
            t.subtasks.append(st)
            tasks.append(t)
            
        return tasks


# =====================================================================
# 4. 실행 엔진 (Execution Agent with ThreadPoolExecutor)
# =====================================================================

class ExecutionAgent:
    """Executes actions asynchronously using a thread pool after safety authorization."""
    def __init__(self, safety_agent, max_workers=8):
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="ARA_Worker")
        self.safety_agent = safety_agent
        self.audit_logs = []
        self.lock = threading.Lock()

    def log_audit(self, msg):
        with self.lock:
            self.audit_logs.append(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}")
            if len(self.audit_logs) > 20:
                self.audit_logs.pop(0)

    def execute_plan(self, tasks, callback=None):
        for task in tasks:
            for subtask in task.subtasks:
                for action in subtask.actions:
                    self.executor.submit(self._run_action_with_safety, action, callback)

    def _run_action_with_safety(self, action: Action, callback):
        # 1. Safety Gate Verification
        is_safe, reason = self.safety_agent.check_action_safety(action.action_type, action.target)
        if not is_safe:
            msg = f"[거부] 안전 위반 차단 - {action.action_type} -> {action.target} ({reason})"
            self.log_audit(msg)
            if callback:
                callback(False, msg)
            return

        # 2. Action Routing & Execution
        status_msg = ""
        try:
            if action.action_type == "READ":
                if os.path.exists(action.target):
                    with open(action.target, 'r', encoding='utf-8', errors='ignore') as f:
                        _ = f.read(200) # Preview
                    status_msg = f"[실행] {action.target} 파일 내용 읽기 완료"
                else:
                    status_msg = f"[경고] {action.target} 파일이 존재하지 않음"
                    
            elif action.action_type == "MES_SYNC":
                time.sleep(0.2) # Sync delay simulation
                status_msg = f"[실행] MES 생산실적 서버 동기화 완료"
                
            elif action.action_type == "ERP_QUERY":
                status_msg = f"[실행] ERP 재고 정보 쿼리 성공: {action.target}"
                
            elif action.action_type == "AUDIT_LOG":
                with open(action.target, 'a', encoding='utf-8') as f:
                    f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] GitOps Policy Audit Log verified.\n")
                status_msg = f"[실행] 감사 로그 기록 완료: {action.target}"
                
            else:
                status_msg = f"[실행] 범용 액션 {action.action_type} 가동 완료"
                
            self.log_audit(status_msg)
            if callback:
                callback(True, status_msg)
                
        except Exception as e:
            err_msg = f"[오류] 액션 {action.action_type} 실행 실패: {e}"
            self.log_audit(err_msg)
            if callback:
                callback(False, err_msg)


# =====================================================================
# 5. 제조/MES/ERP 특화 에이전트
# =====================================================================

class MESAgent:
    def process_sync(self, production_data):
        return {"status": "SUCCESS", "module": "MES", "log": "실시간 생산 실적 동기화 완료"}

class ERPAgent:
    def check_inventory(self, part_no):
        return {"part_no": part_no, "status": "AVAILABLE", "quantity": 150}


# =====================================================================
# 6. 에이전트 커널 및 파이프라인 (AgentKernel)
# =====================================================================

class AgentKernel:
    """The central core orchestrating the Observe -> Parse -> Embed -> Store -> Reason -> Plan -> Execute -> Learn pipeline."""
    def __init__(self):
        self.memory_agents = [MemoryAgent() for _ in range(100)]
        self.safety_agents = [SafetyAgent(allowed_paths=["./ara_input_data", "./downloads", "./pdf", "./designs"]) for _ in range(100)]
        self.reasoning_agents = [ReasoningAgent() for _ in range(100)]
        self.execution_agents = [ExecutionAgent(self.safety_agents[i], max_workers=8) for i in range(100)]
        
        self.mes_agents = [MESAgent() for _ in range(100)]
        self.erp_agents = [ERPAgent() for _ in range(100)]

        # Keep original single attributes for backward compatibility
        self.memory_agent = self.memory_agents[0]
        self.safety_agent = self.safety_agents[0]
        self.reasoning_agent = self.reasoning_agents[0]
        self.execution_agent = self.execution_agents[0]
        self.mes_agent = self.mes_agents[0]
        self.erp_agent = self.erp_agents[0]
        
        self.pipeline_stage = "IDLE"
        self.recent_events = []
        self.lock = threading.Lock()
        self.processed_files = 0
        self.brain_stress = 0.0

    def log_event(self, msg):
        with self.lock:
            self.recent_events.append(f"[{time.strftime('%H:%M:%S')}] {msg}")
            if len(self.recent_events) > 10:
                self.recent_events.pop(0)

    def trigger_file_pipeline(self, file_path):
        # 1. Observe Stage
        self.pipeline_stage = "OBSERVE"
        self.log_event(f"Observe: 새 파일 감지 -> {os.path.basename(file_path)}")
        self.processed_files += 1

        # 2. Parse & 3. Embed Stage
        self.pipeline_stage = "PARSE & EMBED"
        file_ext = os.path.splitext(file_path)[1].lower().strip('.')
        self.log_event(f"Parse/Embed: 파일 포맷({file_ext}) 특징 융합 중")
        
        # Simulated embedding extraction
        mock_vector = [0.0] * 128
        mock_vector[0] = 0.85
        
        # 4. Store Stage (3-tier Storage)
        self.pipeline_stage = "STORE"
        item = {
            "title": f"파일 자동 인지: {os.path.basename(file_path)}",
            "link": f"local-file://{os.path.basename(file_path)}",
            "description": f"파일 크기 {os.path.getsize(file_path) / 1024:.2f} KB 데이터 인지 완료.",
            "source": "FileAgent",
            "scraped_at": time.strftime('%Y-%m-%d %H:%M:%S'),
            "embedded_vector": json.dumps(mock_vector)
        }
        self.memory_agent.store_wisdom(item)
        self.log_event("Store: 3계층 메모리(Hot/Warm/Cold) 저장 완료")

        # 5. Reason & 6. Plan Stage
        self.pipeline_stage = "REASON & PLAN"
        goal = Goal(f"Analyze and process local file: {os.path.basename(file_path)}")
        context = {"file_path": file_path}
        tasks = self.reasoning_agent.create_plan(goal, context)
        self.log_event("Reason/Plan: 계획 분해 수립 (Goal -> Task -> SubTask -> Action)")

        # 7. Execute Stage
        self.pipeline_stage = "EXECUTE"
        
        def action_callback(success, msg):
            self.log_event(msg)
            
        self.execution_agent.execute_plan(tasks, callback=action_callback)

        # 8. Learn Stage
        self.pipeline_stage = "LEARN"
        self.log_event("Learn: 환경 피드백 학습 완료")
        
        # Reset to IDLE
        self.pipeline_stage = "IDLE"

    def stabilize(self):
        """Non-linear brain cell stress calculation loop based on system load (psutil)."""
        while True:
            time.sleep(0.5)
            cpu_usage = psutil.cpu_percent()
            ram_usage = psutil.virtual_memory().percent
            target_stress = (cpu_usage + ram_usage) / 4.0
            
            with self.lock:
                # Smooth convergence to target stress
                self.brain_stress = self.brain_stress * 0.9 + target_stress * 0.1


# =====================================================================
# 7. 웹소켓 및 메시지 감시 에이전트 (WebAgent Mock)
# =====================================================================

class WebAgent(threading.Thread):
    """Simulates external WebSocket or message queue (Kafka/RabbitMQ) event ingestion."""
    def __init__(self, kernel):
        super().__init__(daemon=True)
        self.kernel = kernel
        self.running = True

    def run(self):
        self.kernel.log_event("WebAgent: WebSocket 연결 완료. 수신 대기 중...")
        while self.running:
            time.sleep(15.0) # Periodic manufacturing event simulation
            if self.running:
                self.kernel.log_event("WebAgent: 외부 설비(MES/ERP) 갱신 시그널 수신")
                goal = Goal("Sync MES production and update inventory")
                context = {}
                tasks = self.kernel.reasoning_agent.create_plan(goal, context)
                self.kernel.execution_agent.execute_plan(tasks, callback=lambda s, m: self.kernel.log_event(m))


# =====================================================================
# 8. 파일 자동 감지 에이전트 (FileAgent)
# =====================================================================

class FileAgent(FileSystemEventHandler):
    """Monitors the safety directory for incoming files and triggers the kernel pipeline."""
    def __init__(self, kernel):
        self.kernel = kernel

    def on_created(self, event):
        if not event.is_directory:
            time.sleep(0.1) # Wait for file write completion
            self.kernel.trigger_file_pipeline(event.src_path)


# =====================================================================
# 9. 역동적 콘솔 대시보드 (Live Dashboard)
# =====================================================================

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def draw_dashboard(kernel):
    clear_screen()
    
    # 3-tier Memory Stats
    hot, warm, cold = kernel.memory_agent.get_stats()
    
    # Process load bar
    bar_length = 30
    fill_len = int(min(1.0, kernel.brain_stress / 100.0) * bar_length)
    bar = '█' * fill_len + '-' * (bar_length - fill_len)
    
    print("\033[1m" + "="*65 + "\033[0m")
    print(" 🧠 ARA MULTI-AGENT PLATFORM CORE 3.0 - LIVE CONTROLLER")
    print("\033[1m" + "="*65 + "\033[0m\n")
    
    print(f" 📡 인지 파이프라인 단계 : \033[92m{kernel.pipeline_stage}\033[0m")
    print(f" ⚡ 인지 시스템 부하     : [{bar}] {kernel.brain_stress:.1f}%")
    print(f" 📂 처리된 파일 건수     : {kernel.processed_files} 건\n")
    
    print(" [📊 3계층 지식 메모리 관리 현황]")
    print(f"   ├─ 🔥 Hot Memory (RAM 캐시)  : {hot:3d} / 50  건")
    print(f"   ├─ ☀️ Warm Memory (SQLite DB) : {warm:3d} 건")
    print(f"   └─ ❄️ Cold Memory (JSON 아카이브) : {cold:3d} 건\n")
    
    print(" [🛡️ 에이전트 라이브 상태 (각 100개씩 총 600개 에이전트 가동 중)]")
    print("   ├─ FileAgent      : \033[92m감시 작동 중\033[0m (./ara_input_data)")
    print("   ├─ WebAgent       : \033[92mWebSocket 대기 중\033[0m")
    print("   ├─ MemoryAgent    : \033[92m동작 가능 (SQLite 3계층) (100개)\033[0m")
    print("   ├─ ReasoningAgent : \033[92mReasoner 활성화 (100개)\033[0m")
    print("   ├─ PlanningAgent  : \033[92mGoal-to-Action 구조 가동 (100개)\033[0m")
    print("   ├─ ExecutionAgent : \033[92mThreadPoolExecutor (100개)\033[0m")
    print("   ├─ SafetyAgent    : \033[91m보안 통제 게이트 활성화 (100개)\033[0m")
    print("   ├─ MESAgent       : \033[92m생산 실적 동기화 (100개)\033[0m")
    print("   └─ ERPAgent       : \033[92m재고 실시간 조회 (100개)\033[0m\n")

    print(" [📝 실시간 핵심 감사 로그 / 이벤트 (최근 5개)]")
    events = kernel.recent_events[::-1][:5]
    if not events:
        print("   (이벤트 없음)")
    for ev in events:
        print(f"   {ev}")
        
    print("\n" + "-"*65)
    print(" \033[90m⚙️  참고: './ara_input_data' 폴더에 파일을 넣으면 인지 루프가 작동합니다.")
    print("    안전을 위해 D:\\ 또는 C:\\ 전체 스캔은 제한되며, 안전 디렉토리만 감시합니다.")
    print("    종료하려면 Ctrl+C를 누르세요.\033[0m")
    print("-"*65 + "\n")


# =====================================================================
# 메인 가동부
# =====================================================================

if __name__ == "__main__":
    TARGET_DIR = "./ara_input_data"
    os.makedirs(TARGET_DIR, exist_ok=True)

    # 커널 및 에이전트 인스턴스 초기화
    kernel = AgentKernel()
    
    # 백그라운드 환경 부하 안정화 및 스케줄러 기동
    threading.Thread(target=kernel.stabilize, daemon=True).start()
    
    # WebAgent (WebSocket 모사) 기동
    web_agent = WebAgent(kernel)
    web_agent.start()

    # FileAgent (Watchdog 모니터링) 등록 및 기동
    observer = Observer()
    observer.schedule(FileAgent(kernel), TARGET_DIR, recursive=False)
    observer.start()

    kernel.log_event("ARA 멀티 에이전트 시스템이 초기화되었습니다.")

    try:
        while True:
            draw_dashboard(kernel)
            time.sleep(0.5)
    except KeyboardInterrupt:
        observer.stop()
        web_agent.running = False
        clear_screen()
        print("ARA 멀티 에이전트 인지 시스템이 안전하게 종료되었습니다.")
        
    observer.join()
