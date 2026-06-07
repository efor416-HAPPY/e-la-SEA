# -*- coding: utf-8 -*-
"""
🌱 ARA IPC-Agent Platform Core
================================================================================
This module implements a modular system featuring:
  1. Swappable IPC Transport Layer (TCP Socket, Named Pipe, and Local IPC).
  2. Independent, decoupled services (News Collection, YouTube Monitoring, AI Agent, Process Execution).
  3. Separated cross-cutting concern modules via a middleware onion pipeline
     (Retry, Timeout, Auto-Recovery, Permission Management, and Audit Log).
  4. Real-time CLI Dashboard illustrating hot-swapping and pipeline operations.
================================================================================
"""

import os
import sys
import time
import json
import socket
import threading
import queue
import subprocess
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from multiprocessing.connection import Listener, Client
from typing import Callable, Dict, Any, List

# Ensure terminal outputs UTF-8 on Windows
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    os.system('') # Enable VT100 colors in Windows console

# =====================================================================
# 1. Swappable IPC Transport Modules
# =====================================================================

class IpcTransport:
    """Base interface for all exchangeable IPC transport layers."""
    def start(self, handler: Callable[[str], str]) -> None:
        raise NotImplementedError

    def stop(self) -> None:
        raise NotImplementedError

    def send_client_request(self, data_str: str) -> str:
        """Helper to send a request as a client on this transport and return the response."""
        raise NotImplementedError


class TcpTransport(IpcTransport):
    """TCP Socket based IPC transport running on a local port."""
    def __init__(self, host="127.0.0.1", port=9091):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.thread = None
        self.handler = None

    def start(self, handler: Callable[[str], str]) -> None:
        self.handler = handler
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        self.thread = threading.Thread(target=self._listen_loop, name="TCP_Listener", daemon=True)
        self.thread.start()

    def _listen_loop(self):
        while self.running:
            try:
                conn, addr = self.server_socket.accept()
                threading.Thread(target=self._handle_client, args=(conn,), daemon=True).start()
            except Exception:
                break

    def _handle_client(self, conn):
        try:
            conn.settimeout(5.0)
            data = conn.recv(65536)
            if data:
                req_str = data.decode('utf-8')
                res_str = self.handler(req_str)
                conn.sendall(res_str.encode('utf-8'))
        except Exception:
            pass
        finally:
            conn.close()

    def stop(self) -> None:
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
        if self.thread:
            self.thread.join(timeout=1.0)

    def send_client_request(self, data_str: str) -> str:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5.0)
        try:
            s.connect((self.host, self.port))
            s.sendall(data_str.encode('utf-8'))
            response = s.recv(65536)
            return response.decode('utf-8')
        except Exception as e:
            return json.dumps({"success": False, "error": f"TCP client connection failed: {e}"})
        finally:
            s.close()


class NamedPipeTransport(IpcTransport):
    """Named Pipe based IPC transport using multiprocessing.connection."""
    def __init__(self):
        if os.name == 'nt':
            self.address = r'\\.\pipe\ara_ipc_pipe'
            self.family = 'AF_PIPE'
        else:
            self.address = './ara_ipc_pipe'
            self.family = 'AF_UNIX'
        self.listener = None
        self.running = False
        self.thread = None
        self.handler = None

    def start(self, handler: Callable[[str], str]) -> None:
        self.handler = handler
        # Clean up existing pipe file on non-Windows
        if os.name != 'nt' and os.path.exists(self.address):
            try:
                os.remove(self.address)
            except Exception:
                pass
        self.listener = Listener(self.address, self.family)
        self.running = True
        self.thread = threading.Thread(target=self._listen_loop, name="NP_Listener", daemon=True)
        self.thread.start()

    def _listen_loop(self):
        while self.running:
            try:
                conn = self.listener.accept()
                threading.Thread(target=self._handle_client, args=(conn,), daemon=True).start()
            except Exception:
                break

    def _handle_client(self, conn):
        try:
            # multiprocessing.connection transfers Python objects natively, but we will send
            # string messages to maintain exact parity with the TCP transport.
            req_str = conn.recv()
            if isinstance(req_str, bytes):
                req_str = req_str.decode('utf-8')
            res_str = self.handler(req_str)
            conn.send(res_str)
        except Exception:
            pass
        finally:
            conn.close()

    def stop(self) -> None:
        self.running = False
        if self.listener:
            try:
                self.listener.close()
            except Exception:
                pass
        if os.name != 'nt' and os.path.exists(self.address):
            try:
                os.remove(self.address)
            except Exception:
                pass
        if self.thread:
            self.thread.join(timeout=1.0)

    def send_client_request(self, data_str: str) -> str:
        try:
            conn = Client(self.address, self.family)
            conn.send(data_str)
            response = conn.recv()
            if isinstance(response, bytes):
                return response.decode('utf-8')
            return response
        except Exception as e:
            return json.dumps({"success": False, "error": f"Named Pipe client connection failed: {e}"})


class LocalIpcTransport(IpcTransport):
    """In-memory Local Queue-based IPC transport (low overhead, zero-copy)."""
    def __init__(self):
        self.request_queue = queue.Queue()
        self.running = False
        self.thread = None
        self.handler = None

    def start(self, handler: Callable[[str], str]) -> None:
        self.handler = handler
        self.running = True
        self.thread = threading.Thread(target=self._processing_loop, name="LocalIPC_Listener", daemon=True)
        self.thread.start()

    def _processing_loop(self):
        while self.running:
            try:
                # Blocks with timeout to check running flag
                req_item = self.request_queue.get(timeout=0.5)
                req_str, response_q = req_item
                try:
                    res_str = self.handler(req_str)
                    response_q.put(res_str)
                except Exception as e:
                    response_q.put(json.dumps({"success": False, "error": f"Local IPC handler failed: {e}"}))
                finally:
                    self.request_queue.task_done()
            except queue.Empty:
                continue
            except Exception:
                break

    def stop(self) -> None:
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)

    def send_client_request(self, data_str: str) -> str:
        if not self.running:
            return json.dumps({"success": False, "error": "Local IPC is not running."})
        res_queue = queue.Queue()
        self.request_queue.put((data_str, res_queue))
        try:
            return res_queue.get(timeout=5.0)
        except queue.Empty:
            return json.dumps({"success": False, "error": "Local IPC request timed out."})


class IpcManager:
    """Manages hot-swapping between transport protocols at runtime."""
    def __init__(self):
        self.transports: Dict[str, IpcTransport] = {
            "tcp": TcpTransport(),
            "named_pipe": NamedPipeTransport(),
            "local": LocalIpcTransport()
        }
        self.active_type = "local"
        self.handler = None
        self.lock = threading.Lock()

    def start(self, initial_type: str, handler: Callable[[str], str]) -> None:
        with self.lock:
            self.handler = handler
            self.active_type = initial_type
            self.transports[self.active_type].start(handler)

    def switch_transport(self, target_type: str) -> None:
        with self.lock:
            if target_type not in self.transports:
                raise ValueError(f"Unknown transport type: {target_type}")
            if target_type == self.active_type:
                return

            # Gracefully stop the current active transport
            self.transports[self.active_type].stop()
            
            # Switch and start the new transport
            self.active_type = target_type
            self.transports[self.active_type].start(self.handler)

    def stop(self) -> None:
        with self.lock:
            self.transports[self.active_type].stop()

    def send_client_request(self, data_str: str) -> str:
        with self.lock:
            return self.transports[self.active_type].send_client_request(data_str)


# =====================================================================
# 2. Independent decoupled Services (Workers)
# =====================================================================

class BaseService:
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError


class NewsService(threading.Thread, BaseService):
    """Independently monitors and fetches news updates."""
    def __init__(self):
        threading.Thread.__init__(self)
        self.name = "NewsServiceWorker"
        self.daemon = True
        self.running = True
        self.logs: List[str] = []
        self.lock = threading.Lock()
        self.crash_triggered = False

    def log(self, msg):
        with self.lock:
            self.logs.append(f"[{time.strftime('%H:%M:%S')}] {msg}")
            if len(self.logs) > 10:
                self.logs.pop(0)

    def run(self):
        self.log("News collection service started.")
        while self.running:
            if self.crash_triggered:
                self.log("NewsService simulated fatal exception. Crashing thread!")
                raise RuntimeError("NewsService thread crash simulation.")

            # Simulate scraping
            self.log("Scraped openculture.com/feed - found 1 new article.")
            # Sleep incrementally to allow quick interrupt / crash trigger
            for _ in range(80):
                if not self.running or self.crash_triggered:
                    break
                time.sleep(0.1)

    def stop(self) -> None:
        self.running = False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if action == "status":
            with self.lock:
                return {"success": True, "status": "running" if self.running else "stopped", "logs": list(self.logs)}
        elif action == "trigger_crash":
            self.crash_triggered = True
            return {"success": True, "result": "Crash trigger set. Thread will fail on next iteration."}
        elif action == "fetch_latest":
            # Simulate a network delay
            delay = params.get("delay", 0.0)
            if delay > 0:
                time.sleep(delay)
            # Simulate transient failure
            if params.get("simulate_fail", False):
                return {"success": False, "error": "Transient database connection pool exhaustion.", "error_type": "transient"}
            return {
                "success": True,
                "news": [
                    {"title": "Open Culture: The Philosophy of Zen in Design", "link": "https://www.openculture.com/zen-design"}
                ]
            }
        return {"success": False, "error": f"Unknown News action: {action}"}


class YouTubeService(threading.Thread, BaseService):
    """Independently monitors YouTube channel upload feeds."""
    def __init__(self):
        threading.Thread.__init__(self)
        self.name = "YouTubeServiceWorker"
        self.daemon = True
        self.running = True
        self.logs: List[str] = []
        self.lock = threading.Lock()

    def log(self, msg):
        with self.lock:
            self.logs.append(f"[{time.strftime('%H:%M:%S')}] {msg}")
            if len(self.logs) > 10:
                self.logs.pop(0)

    def run(self):
        self.log("YouTube monitor service started.")
        while self.running:
            self.log("Monitored channel UC18xqS40OGGyPVI-4sneOEA - no updates.")
            # Sleep incrementally to allow quick interrupt
            for _ in range(100):
                if not self.running:
                    break
                time.sleep(0.1)

    def stop(self) -> None:
        self.running = False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if action == "status":
            with self.lock:
                return {"success": True, "status": "running" if self.running else "stopped", "logs": list(self.logs)}
        elif action == "check_now":
            return {"success": True, "result": "Forced instant YouTube check successful. 0 new uploads."}
        return {"success": False, "error": f"Unknown YouTube action: {action}"}


class AiAgentService(BaseService):
    """Decoupled AI Agent service managing local reasoning requests."""
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if action == "generate_response":
            prompt = params.get("prompt", "")
            # Simulate a slow LLM inference
            if "slow" in prompt.lower():
                time.sleep(4.0)
            
            reply = f"아라(ARA)의 지혜로운 사색: '{prompt}'라는 화두는 숲의 사계절과 같습니다. 자연의 흐름처럼 순리를 따라 해결점을 찾아나아가길 권합니다. 🌱"
            return {"success": True, "reply": reply}
        return {"success": False, "error": f"Unknown AI Agent action: {action}"}


class ProcessExecutionService(BaseService):
    """Decoupled utility to launch system applications safely."""
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if action == "execute":
            target = params.get("target", "").lower().strip()
            # Command validation is handled separately in the Permission Middleware.
            try:
                # Launch application in background
                if os.name == 'nt':
                    subprocess.Popen([target], shell=True)
                else:
                    # Non-Windows mock / run commands like echo
                    subprocess.Popen([target])
                return {"success": True, "result": f"Launched process '{target}' in background."}
            except Exception as e:
                return {"success": False, "error": f"System subprocess execution failure: {e}"}
        return {"success": False, "error": f"Unknown Process Execution action: {action}"}


# =====================================================================
# 3. Separated Cross-Cutting Concern Middleware
# =====================================================================

class Middleware:
    def process(self, request: Dict[str, Any], next_handler: Callable[[Dict[str, Any]], Dict[str, Any]]) -> Dict[str, Any]:
        raise NotImplementedError


class AuditLogMiddleware(Middleware):
    """Separated Module: GitOps compliant audit logger."""
    def __init__(self, log_path="downloads/ipc_audit.log"):
        self.log_path = log_path
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def process(self, request: Dict[str, Any], next_handler: Callable[[Dict[str, Any]], Dict[str, Any]]) -> Dict[str, Any]:
        req_id = request.get("request_id", "untracked")
        service = request.get("service", "unknown")
        action = request.get("action", "unknown")
        
        self._write_log(f"REQ | ID={req_id} | service={service} | action={action}")
        
        start_time = time.time()
        try:
            response = next_handler(request)
            duration = time.time() - start_time
            success = response.get("success", False)
            err = response.get("error", None)
            
            if success:
                self._write_log(f"RES | ID={req_id} | SUCCESS | duration={duration:.3f}s")
            else:
                self._write_log(f"RES | ID={req_id} | FAILED: {err} | duration={duration:.3f}s")
            return response
        except Exception as e:
            duration = time.time() - start_time
            self._write_log(f"ERR | ID={req_id} | CRASH: {e} | duration={duration:.3f}s")
            raise e

    def _write_log(self, msg: str):
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
        except Exception as e:
            print(f"Failed writing audit log: {e}", file=sys.stderr)


class PermissionMiddleware(Middleware):
    """Separated Module: Role-based privilege gate & injection screening."""
    def __init__(self):
        self.allowed_apps = ["calc", "notepad", "mspaint"]
        self.dangerous_keywords = ["rm -rf", "drop table", "delete from", "format c:"]

    def process(self, request: Dict[str, Any], next_handler: Callable[[Dict[str, Any]], Dict[str, Any]]) -> Dict[str, Any]:
        service = request.get("service")
        action = request.get("action")
        params = request.get("params", {})

        # 1. Block command execution of non-whitelisted binaries
        if service == "process_execution" and action == "execute":
            target = params.get("target", "").lower().strip()
            if target not in self.allowed_apps:
                return {
                    "success": False,
                    "error": f"Permission Denied: Execution of binary '{target}' is unauthorized.",
                    "error_type": "security"
                }

        # 2. Screening string parameters for command injection vulnerability
        for key, val in params.items():
            if isinstance(val, str):
                for keyword in self.dangerous_keywords:
                    if keyword in val.lower():
                        return {
                            "success": False,
                            "error": f"Security Violation: Dangerous pattern '{keyword}' block triggered in parameter '{key}'.",
                            "error_type": "security"
                        }

        return next_handler(request)


class TimeoutMiddleware(Middleware):
    """Separated Module: Execution time limiter."""
    def __init__(self, default_timeout=2.0):
        self.default_timeout = default_timeout
        self.executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix="IpcTimeoutWorker")

    def process(self, request: Dict[str, Any], next_handler: Callable[[Dict[str, Any]], Dict[str, Any]]) -> Dict[str, Any]:
        # Enforce timeout by executing the downstream handler in the thread pool
        future = self.executor.submit(next_handler, request)
        timeout = request.get("timeout", self.default_timeout)
        try:
            return future.result(timeout=timeout)
        except TimeoutError:
            return {
                "success": False,
                "error": f"Request Timeout: Execution exceeded authorized limit of {timeout}s.",
                "error_type": "timeout"
            }


class RetryMiddleware(Middleware):
    """Separated Module: Automated retry with exponential backoff on transient errors."""
    def __init__(self, max_retries=3, initial_delay=0.1):
        self.max_retries = max_retries
        self.initial_delay = initial_delay

    def process(self, request: Dict[str, Any], next_handler: Callable[[Dict[str, Any]], Dict[str, Any]]) -> Dict[str, Any]:
        retries = 0
        delay = self.initial_delay
        
        while True:
            response = next_handler(request)
            
            # Retry only on failures flagged as transient
            if not response.get("success") and response.get("error_type") == "transient":
                if retries < self.max_retries:
                    retries += 1
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                    continue
            return response


# =====================================================================
# 4. Service Auto-Recovery Subsystem (Watchdog)
# =====================================================================

class AutoRecoveryModule(threading.Thread):
    """Separated Module: Watchdog daemon to recover crashed background services."""
    def __init__(self, services_map: Dict[str, BaseService]):
        super().__init__()
        self.name = "AutoRecoveryWatchdog"
        self.daemon = True
        self.services = services_map
        self.running = False
        self.logs: List[str] = []
        self.lock = threading.Lock()

    def log(self, msg):
        with self.lock:
            self.logs.append(f"[{time.strftime('%H:%M:%S')}] {msg}")
            if len(self.logs) > 10:
                self.logs.pop(0)

    def start_watchdog(self):
        self.running = True
        self.start()

    def stop_watchdog(self):
        self.running = False

    def run(self):
        self.log("Auto-Recovery Watchdog started.")
        while self.running:
            time.sleep(3.0)  # Scan service states every 3 seconds
            for name, service in self.services.items():
                # Verify if service is supposed to run as thread and check if thread is alive
                if isinstance(service, threading.Thread):
                    if not service.is_alive() and getattr(service, 'running', False):
                        self.log(f"🚨 Crash detected in service '{name}'! Re-initializing and restarting...")
                        
                        # Re-instantiate and restart the thread class to bypass Python thread reuse limit
                        if name == "news":
                            new_service = NewsService()
                        elif name == "youtube":
                            new_service = YouTubeService()
                        else:
                            continue
                        
                        self.services[name] = new_service
                        new_service.start()
                        self.log(f"✅ Service '{name}' recovered successfully.")


# =====================================================================
# 5. Core Platform Kernel & Middleware Orchestration
# =====================================================================

class PlatformKernel:
    """Combines transports, services, and middlewares into a unified system."""
    def __init__(self):
        # 1. Instantiate Independent Services
        self.services: Dict[str, BaseService] = {
            "news": NewsService(),
            "youtube": YouTubeService(),
            "ai_agent": AiAgentService(),
            "process_execution": ProcessExecutionService()
        }

        # 2. Instantiate Separate Middleware Layers
        self.middlewares: List[Middleware] = [
            RetryMiddleware(),
            AuditLogMiddleware(),
            PermissionMiddleware(),
            TimeoutMiddleware()
        ]

        # 3. Instantiate Watchdog Recovery
        self.watchdog = AutoRecoveryModule(self.services)

        # 4. Instantiate swappable IPC Manager
        self.ipc_manager = IpcManager()

    def start(self):
        # Start threading services
        for service in self.services.values():
            if isinstance(service, threading.Thread):
                service.start()
        
        # Start watchdog
        self.watchdog.start_watchdog()

        # Wire up central request router
        self.ipc_manager.start("local", self.route_ipc_request)

    def stop(self):
        self.ipc_manager.stop()
        self.watchdog.stop_watchdog()
        for service in self.services.values():
            if isinstance(service, threading.Thread):
                service.stop()

    def route_ipc_request(self, req_str: str) -> str:
        """Central entrypoint. Resolves request, applies middleware pipeline, routes to target service."""
        try:
            request = json.loads(req_str)
        except Exception as e:
            return json.dumps({"success": False, "error": f"JSON parse error: {e}"})

        # Build execution handler
        def final_handler(req: Dict[str, Any]) -> Dict[str, Any]:
            service_name = req.get("service")
            action = req.get("action")
            params = req.get("params", {})
            
            service = self.services.get(service_name)
            if not service:
                return {"success": False, "error": f"Service '{service_name}' not found."}
            
            try:
                return service.execute(action, params)
            except Exception as e:
                return {"success": False, "error": f"Internal service execution crash: {e}"}

        # Compose onion middleware pipeline: middlewares[0] -> ... -> middlewares[n] -> final_handler
        def build_onion(index: int) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
            if index == len(self.middlewares):
                return final_handler
            return lambda req: self.middlewares[index].process(req, build_onion(index + 1))

        pipeline_run = build_onion(0)
        res_dict = pipeline_run(request)
        return json.dumps(res_dict, ensure_ascii=False)


# =====================================================================
# 6. Live Dashboard & Interactive Simulation
# =====================================================================

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def draw_console_dashboard(kernel: PlatformKernel):
    clear_screen()
    
    # Read service states
    news_active = kernel.services["news"].is_alive()
    yt_active = kernel.services["youtube"].is_alive()
    
    # Read watchdog logs
    with kernel.watchdog.lock:
        watchdog_logs = list(kernel.watchdog.logs)[-4:]
    
    # Read core audit logs
    audit_lines = []
    log_path = "downloads/ipc_audit.log"
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                audit_lines = f.readlines()[-6:]
        except Exception:
            pass

    print("\033[1m" + "="*70 + "\033[0m")
    print(" 🚀 ARA IPC-AGENT SERVICE KERNEL (DYNAMIC SWAPPABLE ARCHITECTURE)")
    print("\033[1m" + "="*70 + "\033[0m\n")
    
    print(f" 🔌 Active IPC Transport Mode : \033[1;92m{kernel.ipc_manager.active_type.upper()}\033[0m")
    print("   └─ Quick switch key commands:")
    print("      [1] Switch to TCP Socket Transport (Port 9091)")
    print("      [2] Switch to Named Pipe Transport (Windows native AF_PIPE)")
    print("      [3] Switch to Local Message Queue Transport")
    print()
    
    print(" [⚙️ Independent Worker Services]")
    print(f"   ├─ NewsServiceWorker      : {chr(9989) if news_active else chr(10060)} "
          f"{'\033[92mACTIVE\033[0m' if news_active else '\033[91mCRASHED/STOPPED\033[0m'}")
    print(f"   ├─ YouTubeServiceWorker   : {chr(9989) if yt_active else chr(10060)} "
          f"{'\033[92mACTIVE\033[0m' if yt_active else '\033[91mCRASHED/STOPPED\033[0m'}")
    print("   ├─ AiAgentService         : ✅ \033[92mAVAILABLE\033[0m (On-demand inference)")
    print("   └─ ProcessExecutionService: ✅ \033[92mAVAILABLE\033[0m (Subprocess runner)")
    print()
    
    print(" [🛡️ Isolated Cross-Cutting Middleware Pipeline]")
    print("   ├─ [1] AuditLogMiddleware  : Appends standard audit trails securely")
    print("   ├─ [2] PermissionGate      : Screens command injections & checks process whitelist")
    print("   ├─ [3] TimeoutGate         : ThreadPool-based time-limiter validation")
    print("   └─ [4] RetryGate           : Handles transient network drops with backoff")
    print()

    print(" [🛡️ Auto-Recovery Watchdog Logs]")
    if not watchdog_logs:
        print("   (Watchdog telemetry idle)")
    for wl in watchdog_logs:
        print(f"   {wl.strip()}")
    print()
    
    print(" [📝 Central GitOps Audit Trail (downloads/ipc_audit.log)]")
    if not audit_lines:
        print("   (Audit records empty)")
    for line in audit_lines:
        print(f"   {line.strip()}")
        
    print("\n" + "-"*70)
    print(" \033[90mPress [c] to trigger NewsService crash (test watchdog recovery)")
    print(" Press [e] to run whitelisted process (notepad)")
    print(" Press [u] to run unauthorized process (calc.exe - blocked by gate)")
    print(" Press [t] to test Timeout gate (Slow AI Agent prompt)")
    print(" Press [r] to test Retry gate (Transient News service query)")
    print(" Press [q] to exit application safely.\033[0m")
    print("-"*70 + "\n")


def main_interactive_loop():
    kernel = PlatformKernel()
    kernel.start()

    # Give services a second to spin up
    time.sleep(0.5)

    req_seq = 1

    try:
        while True:
            draw_console_dashboard(kernel)
            # Simple non-blocking keyboard input check would be nice, but standard input works cleanly
            sys.stdout.write("Command choice: ")
            sys.stdout.flush()
            
            # Simple command parser
            choice = sys.stdin.readline().strip().lower()
            if not choice:
                continue

            request_id = f"cli-req-{req_seq}"
            req_seq += 1

            if choice == '1':
                kernel.ipc_manager.switch_transport("tcp")
                time.sleep(0.2)
            elif choice == '2':
                kernel.ipc_manager.switch_transport("named_pipe")
                time.sleep(0.2)
            elif choice == '3':
                kernel.ipc_manager.switch_transport("local")
                time.sleep(0.2)
            elif choice == 'c':
                # Trigger thread crash
                req = {
                    "request_id": request_id,
                    "service": "news",
                    "action": "trigger_crash",
                    "params": {}
                }
                kernel.ipc_manager.send_client_request(json.dumps(req))
                time.sleep(0.5)
            elif choice == 'e':
                # Whitelisted calc target
                req = {
                    "request_id": request_id,
                    "service": "process_execution",
                    "action": "execute",
                    "params": {"target": "notepad"}
                }
                kernel.ipc_manager.send_client_request(json.dumps(req))
                time.sleep(0.5)
            elif choice == 'u':
                # Non-whitelisted binary
                req = {
                    "request_id": request_id,
                    "service": "process_execution",
                    "action": "execute",
                    "params": {"target": "cmd.exe"}
                }
                kernel.ipc_manager.send_client_request(json.dumps(req))
                time.sleep(0.5)
            elif choice == 't':
                # Timeout test: prompt containing 'slow' triggers 4s sleep, timeout limit set to 1.5s
                req = {
                    "request_id": request_id,
                    "service": "ai_agent",
                    "action": "generate_response",
                    "timeout": 1.5,
                    "params": {"prompt": "Solve this slow problem"}
                }
                kernel.ipc_manager.send_client_request(json.dumps(req))
                time.sleep(0.5)
            elif choice == 'r':
                # Retry test: request flags a simulated transient error
                req = {
                    "request_id": request_id,
                    "service": "news",
                    "action": "fetch_latest",
                    "params": {"simulate_fail": True}
                }
                kernel.ipc_manager.send_client_request(json.dumps(req))
                time.sleep(0.5)
            elif choice == 'q':
                break
            else:
                # Treat as normal chat command
                req = {
                    "request_id": request_id,
                    "service": "ai_agent",
                    "action": "generate_response",
                    "params": {"prompt": choice}
                }
                kernel.ipc_manager.send_client_request(json.dumps(req))
                time.sleep(0.5)

    except KeyboardInterrupt:
        pass
    finally:
        kernel.stop()
        clear_screen()
        print("ARA IPC-Agent Platform Core shut down gracefully.")


if __name__ == "__main__":
    main_interactive_loop()
