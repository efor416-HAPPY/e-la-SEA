# -*- coding: utf-8 -*-
"""
🌱 ARA AI Modular Web App Backend (FastAPI Monolith)
Configures routing, middleware filters, security check validation, and hooks background agents.
All features are now routed through the AraKernel microkernel runtime.
"""

import os
import urllib.parse
from fastapi import FastAPI, Request, Response, HTTPException, Query, WebSocket, WebSocketDisconnect
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel

# Kernel Coordinator Import
from backend.kernel.kernel import kernel_instance
from backend.kernel.message import Message

app = FastAPI(title="ARA AI Modular Platform Kernel", version="3.5")

# Enable CORS for frontend web accessibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------------
# Security Guard Middleware (IP whitelist, Rate limiting, Audit log)
# -------------------------------------------------------------------------
@app.middleware("http")
async def security_guard_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "127.0.0.1"
    
    # 1. IP Whitelisting Check
    if not kernel_instance.security_core.is_ip_allowed(client_ip):
        kernel_instance.audit_core.log(
            "SECURITY_VIOLATION", client_ip, request.url.path, "Blocked by IP whitelist", "BLOCKED"
        )
        return JSONResponse(
            status_code=403,
            content={"error": "Forbidden: Untrusted network access blocked."}
        )

    # 2. Rate Limiting Check
    if not kernel_instance.security_core.is_rate_allowed(client_ip):
        kernel_instance.audit_core.log(
            "RATE_LIMIT_EXCEEDED", client_ip, request.url.path, "Too many requests", "BLOCKED"
        )
        return JSONResponse(
            status_code=429,
            content={"error": "Too Many Requests: Rate limit exceeded. Antigravity-Firewall Active."}
        )

    # Proceed with request
    response = await call_next(request)
    
    # Log successful operations to audit trail (excluding spammy polling telemetry)
    if not request.url.path.startswith(("/api/system", "/api/sensory")):
        kernel_instance.audit_core.log(
            "API_REQUEST", client_ip, request.url.path, f"Method: {request.method}", f"{response.status_code}"
        )
        
    return response

# -------------------------------------------------------------------------
# FastAPI Startup & Shutdown Event Lifecycle hooks
# -------------------------------------------------------------------------
@app.on_event("startup")
def startup_event():
    # Boot the ARA 2.0 Microkernel containing all agents and cores
    kernel_instance.start()
    kernel_instance.audit_core.log("SYSTEM_LIFECYCLE", "Kernel", "Startup", "ARA Core Backend started successfully.")

@app.on_event("shutdown")
def shutdown_event():
    # Gracefully shut down the microkernel
    kernel_instance.stop()
    kernel_instance.audit_core.log("SYSTEM_LIFECYCLE", "Kernel", "Shutdown", "ARA Core Backend stopped successfully.")

# -------------------------------------------------------------------------
# API Endpoints
# -------------------------------------------------------------------------

@app.get("/api/system")
def get_system():
    """Returns dynamic CPU/RAM load metrics via the MonitorAgent."""
    monitor = kernel_instance.bus.agents.get("monitor")
    if monitor:
        return monitor.get_system_metrics()
    return {"cpu_usage": 0.0, "ram_usage": 50.0}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            monitor = kernel_instance.bus.agents.get("monitor")
            metrics = monitor.get_system_metrics() if monitor else {"cpu_usage": 0.0, "ram_usage": 50.0}
            await websocket.send_json(metrics)
            await asyncio.sleep(2.0)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass

@app.get("/api/files")
def file_manager(action: str = "list", path: str = ""):
    """Provides a safe file browser within the workspace folder."""
    workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    
    # Defaults
    if not path or path == "내 PC":
        target_path = workspace_dir
    else:
        target_path = os.path.abspath(path)

    # Security check: Prevent Directory Traversal
    if os.path.commonpath([workspace_dir, target_path]) != workspace_dir:
        target_path = workspace_dir

    if not os.path.exists(target_path):
        raise HTTPException(status_code=404, detail="Path not found")

    if action == "list" and os.path.isdir(target_path):
        items = []
        try:
            for entry in os.scandir(target_path):
                if entry.name.startswith('.'):
                    continue  # skip hidden
                stat = entry.stat()
                items.append({
                    "name": entry.name,
                    "is_dir": entry.is_dir(),
                    "path": entry.path,
                    "size": stat.st_size if entry.is_file() else 0,
                    "modified": stat.st_mtime
                })
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        return {"current_path": target_path, "items": items}

    elif action == "read" and os.path.isfile(target_path):
        try:
            with open(target_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(50000)  # Read limit
            return {"path": target_path, "content": content}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
            
    raise HTTPException(status_code=400, detail="Invalid action or path type")

class ExecuteRequest(BaseModel):
    target: str

@app.post("/api/execute")
def execute_command(req: ExecuteRequest):
    """Safely runs local utility program (e.g. calculator, notepad) via ActionCore."""
    # Screen command for injection keywords
    is_safe, reason = kernel_instance.security_core.check_safety(req.target)
    if not is_safe:
        return {"status": "error", "message": f"Execution block: {reason}"}

    success = kernel_instance.action_core.launch_app(req.target)
    if success:
        return {"status": "success", "message": f"App '{req.target}' launched."}
    else:
        return {"status": "error", "message": f"Execution block: '{req.target}' is unauthorized or failed."}

@app.get("/api/scheduler/config")
def get_scheduler_config():
    """Returns email notification configurations."""
    return {
        "configured": True,
        "enabled": False,
        "recipient": "efor6@naver.com",
        "times": ["08:00 KST", "20:00 KST"]
    }

@app.get("/api/brain/wisdom")
def get_wisdom():
    """Retrieves all archived knowledge from the 3-tier database."""
    items = kernel_instance.memory_core.manager.warm_db.query_recent(limit=30)
    return items

class ChatRequest(BaseModel):
    message: str
    persona: str = "friend"

@app.post("/api/brain/chat")
def brain_chat(req: ChatRequest):
    """Dialogue handler. Ingests user input -> safety check -> AgentBus dispatch -> response."""
    # Check Safety Gate
    is_safe, reason = kernel_instance.security_core.check_safety(req.message)
    if not is_safe:
        return {"text": f"⚠️ [보안 위반] {reason}", "pulse": 0.5, "stance": "neutral", "innerJoy": 0.0}

    # Dispatch to chat agent via the central AgentBus
    msg = Message(
        source="web_api",
        target="chat",
        action="chat",
        payload={"message": req.message, "persona": req.persona}
    )
    
    success = kernel_instance.bus.dispatch(msg)
    reply = msg.payload.get("result", "대화 처리 실패🌱") if success else "대화 처리 중 오류가 발생했습니다.🌱"
    
    # Calculate synapse pulse rate
    pulse = 1.2
    if len(req.message) > 40:
        pulse = 2.0
    if req.persona == "supporter":
        pulse = 2.5
        
    return {
        "text": reply,
        "pulse": pulse,
        "stance": "wise_companion",
        "innerJoy": 0.5
    }

# Mocking sensory logs (used by front-end)
sensory_logs = []

@app.get("/api/sensory/history")
def get_sensory_history():
    return sensory_logs[-10:]

class SensoryLog(BaseModel):
    location: str = ""
    person: str = ""
    objects: str = ""

@app.post("/api/sensory/log")
def add_sensory_log(log: SensoryLog):
    import time
    log_entry = {
        "time": time.strftime('%H:%M:%S'),
        "location": log.location,
        "person": log.person,
        "objects": log.objects
    }
    sensory_logs.append(log_entry)
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)
