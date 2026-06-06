# -*- coding: utf-8 -*-
"""
================================================================================
🌱 ARA Organic Cognitive Core: Smart Resource Integrator (SmartResourceIntegrator)
================================================================================

This module implements a consolidated single-script cognitive core including:
  1. Multimodal Neural Network routing using PyTorch.
  2. Dynamic Brain Cell Network state management tied to system telemetry (psutil).
  3. Safe asynchronous directory monitoring (watchdog) and queues.
  4. Non-linear brain cell decay algorithms.
"""

import os
import sys
import io
import time
import threading
import queue

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
            return "mock_feature"

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
# 1. 멀티모달 신경망 인지 코어 (PyTorch) - 확장 파이프라인의 기점
# =====================================================================
class SmartResourceIntegrator(nn.Module):
    def __init__(self):
        super().__init__()
        self.hidden_dim = 64
        # 1. 코어 메모리 (기존 지식) 처리
        self.core_processor = nn.Linear(128, self.hidden_dim)
        
        # 2. 멀티 파이프라인 (확장 가능)
        self.ts_pipeline = nn.LSTM(input_size=5, hidden_size=self.hidden_dim, batch_first=True) # 시계열/CSV용
        self.text_pipeline = nn.Linear(300, self.hidden_dim)                                    # 텍스트/로그용
        self.sensor_pipeline = nn.Linear(12, self.hidden_dim)                                   # 센서/바이너리용
        
        # 3. 최종 분석부
        self.final_analyzer = nn.Sequential(
            nn.Linear(self.hidden_dim * 2, self.hidden_dim),
            nn.GELU(),
            nn.Linear(self.hidden_dim, 3) # 최종 출력 차원 (예: 3가지 상태 분류)
        )

    def forward(self, core_data, resource_tensor, resource_type):
        core_features = F.relu(self.core_processor(core_data))
        
        # [스마트 라우팅 기점] 데이터 타입에 따라 다른 뇌엽(레이어) 활성화
        if resource_type == "csv":
            _, (hidden, _) = self.ts_pipeline(resource_tensor)
            res_features = hidden[-1]
        elif resource_type in ["txt", "log"]:
            res_features = F.relu(self.text_pipeline(resource_tensor))
        else: # 기본 범용 센서 파이프라인
            res_features = F.relu(self.sensor_pipeline(resource_tensor))
            
        combined = torch.cat((core_features, res_features), dim=1)
        return self.final_analyzer(combined)


# =====================================================================
# 2. 정교한 뇌 세포 상태 및 컴퓨터 자원 관리 로직
# =====================================================================
class BrainCellNetwork:
    def __init__(self):
        self.activation_level = 0.0      
        self.base_stress = 0.0           # PC 자원(CPU/RAM)에 의한 스트레스
        self.cognitive_state = "IDLE"
        self.lock = threading.Lock()
        self.processed_files = 0

    def apply_stimulus(self, weight):
        with self.lock:
            # 최대 한계치 150% (오버클럭 상태 모사)
            self.activation_level = min(150.0, self.activation_level + weight)
            self.processed_files += 1

    def update_system_resources(self):
        """PC의 실제 CPU/RAM 사용량을 읽어와 기저 스트레스로 반영"""
        cpu_usage = psutil.cpu_percent()
        ram_usage = psutil.virtual_memory().percent
        self.base_stress = (cpu_usage + ram_usage) / 4.0 # 적절한 스케일링

    def stabilize(self):
        """비선형 감쇠 로직: 활성도가 높을수록 식는 속도도 빠름"""
        while True:
            time.sleep(0.5) # 0.5초 단위의 정밀 틱(Tick)
            self.update_system_resources()
            
            with self.lock:
                if self.activation_level > self.base_stress:
                    # 현재 수치에 비례하여 감쇠 (수치가 높을수록 많이 깎임)
                    decay_rate = 0.90 if self.activation_level > 80 else 0.95
                    self.activation_level *= decay_rate
                    
                    # 기저 스트레스 이하로 떨어지지 않게 방어
                    if self.activation_level < self.base_stress:
                        self.activation_level = self.base_stress
                else:
                    self.activation_level = self.base_stress

                self._evaluate_state()

    def _evaluate_state(self):
        if self.activation_level >= 100.0:
            self.cognitive_state = "\033[91mCRITICAL OVERLOAD (과부하 연산 중)\033[0m"
        elif self.activation_level >= 60.0:
            self.cognitive_state = "\033[93mDEEP ANALYSIS (심층 데이터 융합)\033[0m"
        elif self.activation_level >= 30.0:
            self.cognitive_state = "\033[92mACTIVE SENSING (적극적 수집)\033[0m"
        else:
            self.cognitive_state = "\033[94mSTABLE IDLE (안정 대기 및 자원 모니터링)\033[0m"


# =====================================================================
# 3. 비동기 와치독 (안전한 파일 감지 및 대기열 처리)
# =====================================================================
class AsyncDataWatcher(FileSystemEventHandler):
    def __init__(self, task_queue):
        self.task_queue = task_queue

    def on_created(self, event):
        if not event.is_directory:
            # 파일이 완전히 써질 때까지 0.1초 대기 (안정성 강화)
            time.sleep(0.1) 
            self.task_queue.put(event.src_path)


def worker_thread_logic(task_queue, brain, neural_net):
    """큐에 쌓인 파일을 꺼내 신경망 파이프라인으로 넘기는 백그라운드 워커"""
    core_memory = torch.rand(1, 128) # 시뮬레이션용 코어 메모리

    while True:
        file_path = task_queue.get()
        if file_path is None: break # 종료 시그널
        
        file_ext = os.path.splitext(file_path)[1].lower().strip('.')
        
        try:
            file_size_kb = os.path.getsize(file_path) / 1024
            stimulus = min(60.0, max(10.0, file_size_kb * 2)) # 파일 크기에 비례한 자극
        except:
            stimulus = 15.0

        # 1. 뇌에 자극 전달
        brain.apply_stimulus(stimulus)
        
        # 2. 멀티모달 신경망 라우팅을 위한 가상 텐서 생성
        if file_ext == 'csv':
            input_tensor = torch.randn(1, 30, 5) # 시계열 형태
        elif file_ext in ['txt', 'log', 'json']:
            input_tensor = torch.randn(1, 300)   # 텍스트 형태
        else:
            input_tensor = torch.randn(1, 12)    # 기타 센서 형태
            file_ext = 'sensor'

        # 3. 신경망 추론 (Smart Routing)
        try:
            _ = neural_net(core_memory, input_tensor, file_ext)
        except Exception as e:
            pass # 데모 환경에서의 안전한 예외 처리
            
        task_queue.task_done()


# =====================================================================
# 4. 역동적 콘솔 대시보드 (Live UI)
# =====================================================================
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def draw_dashboard(brain):
    clear_screen()
    bar_length = 40
    fill_length = int(min(1.0, brain.activation_level / 150.0) * bar_length)
    bar = '█' * fill_length + '-' * (bar_length - fill_length)
    
    # 색상 적용
    if brain.activation_level > 100: color = '\033[91m' # Red
    elif brain.activation_level > 60: color = '\033[93m' # Yellow
    else: color = '\033[92m' # Green

    print("\033[1m" + "="*60 + "\033[0m")
    print(" 🧠 ARA COGNITIVE CORE 2.0 - LIVE TELEMETRY")
    print("\033[1m" + "="*60 + "\033[0m\n")
    
    print(f" 📡 인지 상태   : {brain.cognitive_state}")
    print(f" ⚡ 뇌 활성도   : {color}[{bar}] {brain.activation_level:05.1f}%\033[0m")
    print(f" 💻 PC 자원 부하 : CPU {psutil.cpu_percent()}% | RAM {psutil.virtual_memory().percent}%  (기저 스트레스: {brain.base_stress:.1f}%)")
    print(f" 📂 처리된 파일 : {brain.processed_files} 건\n")
    
    # Indicate mock modes if any dependencies are missing
    dependency_notes = []
    if not HAS_TORCH: dependency_notes.append("PyTorch 미설치 (시뮬레이션 가동)")
    if not HAS_PSUTIL: dependency_notes.append("psutil 미설치 (자원 스트레스 가상 시뮬레이션)")
    if not HAS_WATCHDOG: dependency_notes.append("watchdog 미설치 (폴링 대기열 감시 작동)")
    
    if dependency_notes:
        print(f" \033[90m⚙️  참고: {', '.join(dependency_notes)}\033[0m")
        
    print("\033[90m [시스템 메시지] './ara_input_data' 폴더에 파일을 드래그하여 드롭하세요.")
    print(" [시스템 메시지] (종료하려면 Ctrl+C를 누르세요)\033[0m\n")


# =====================================================================
# Main Execution
# =====================================================================
if __name__ == "__main__":
    TARGET_DIR = "./ara_input_data"
    if not os.path.exists(TARGET_DIR): os.makedirs(TARGET_DIR)

    # 핵심 컴포넌트 초기화
    brain = BrainCellNetwork()
    neural_net = SmartResourceIntegrator()
    task_queue = queue.Queue()

    # 백그라운드 스레드 가동 (감쇠, 데이터 처리 워커)
    threading.Thread(target=brain.stabilize, daemon=True).start()
    threading.Thread(target=worker_thread_logic, args=(task_queue, brain, neural_net), daemon=True).start()

    # 옵저버 (와치독) 설정
    observer = Observer()
    observer.schedule(AsyncDataWatcher(task_queue), TARGET_DIR, recursive=False)
    observer.start()

    try:
        while True:
            draw_dashboard(brain)
            time.sleep(0.5) # 0.5초마다 콘솔 화면 갱신 (역동적 애니메이션)
    except KeyboardInterrupt:
        observer.stop()
        clear_screen()
        print("시스템이 안전하게 종료되었습니다.")
    
    observer.join()
