# -*- coding: utf-8 -*-
"""
🌱 ARA AI Modular Web App Backend (FastAPI Monolith)
Configures routing, middleware filters, security check validation, and hooks background agents.
"""

import os
import urllib.parse
from fastapi import FastAPI, Request, Response, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel

# Security Subsystem Imports
from backend.security.firewall import check_ip_whitelist, global_limiter
from backend.security.safety_gate import SafetyGate
from backend.security.audit import audit_logger

# Knowledge Subsystem Imports
from backend.memory.long_memory import long_memory

# Voice Layer Imports
from backend.voice.stt import stt_engine
from backend.voice.tts import tts_engine

# Agents Subsystem Imports
from backend.agents.chat_agent import chat_agent
from backend.agents.monitor_agent import monitor_agent

app = FastAPI(title="ARA AI Modular Platform Kernel", version="3.5")

# Enable CORS for frontend web accessibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize global safety gate
safety_gate = SafetyGate()

# -------------------------------------------------------------------------
# Security Guard Middleware (IP whitelist, Rate limiting, Audit log)
# -------------------------------------------------------------------------
@app.middleware("http")
async def security_guard_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "127.0.0.1"
    
    # 1. IP Whitelisting Check
    if not check_ip_whitelist(client_ip):
        audit_logger.log("SECURITY_VIOLATION", client_ip, request.url.path, "Blocked by IP whitelist", "BLOCKED")
        return JSONResponse(
            status_code=403,
            content={"error": "Forbidden: Untrusted network access blocked."}
        )

    # 2. Rate Limiting Check
    if not global_limiter.is_allowed(client_ip):
        audit_logger.log("RATE_LIMIT_EXCEEDED", client_ip, request.url.path, "Too many requests", "BLOCKED")
        return JSONResponse(
            status_code=429,
            content={"error": "Too Many Requests: Rate limit exceeded. Antigravity-Firewall Active."}
        )

    # Proceed with request
    response = await call_next(request)
    
    # Log successful operations to audit trail (excluding spammy polling telemetry)
    if not request.url.path.startswith(("/api/system", "/api/sensory")):
        audit_logger.log("API_REQUEST", client_ip, request.url.path, f"Method: {request.method}", f"{response.status_code}")
        
    return response

# -------------------------------------------------------------------------
# FastAPI Startup & Shutdown Event Lifecycle hooks
# -------------------------------------------------------------------------
@app.on_event("startup")
def startup_event():
    # Start the monitor agent background threads & schedulers
    monitor_agent.start()
    audit_logger.log("SYSTEM_LIFECYCLE", "Kernel", "Startup", "ARA Core Backend started successfully.")

@app.on_event("shutdown")
def shutdown_event():
    # Gracefully shut down monitor agents
    monitor_agent.stop()
    audit_logger.log("SYSTEM_LIFECYCLE", "Kernel", "Shutdown", "ARA Core Backend stopped successfully.")

# -------------------------------------------------------------------------
# API Endpoints
# -------------------------------------------------------------------------

@app.get("/api/system")
def get_system():
    """Returns dynamic CPU/RAM load metrics."""
    metrics = monitor_agent.get_system_metrics()
    return metrics

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
    """Safely runs local utility program (e.g. calculator, notepad) if verified."""
    target_clean = req.target.lower().strip()
    
    # Simple whitelist validation
    allowed_apps = ["calc", "notepad", "mspaint"]
    if target_clean not in allowed_apps:
        return {"status": "error", "message": f"Execution block: '{req.target}' is unauthorized."}
        
    try:
        import subprocess
        # Run in background asynchronously without blocking FastAPI
        if os.name == 'nt':
            subprocess.Popen([target_clean], shell=True)
        else:
            subprocess.Popen([target_clean])
            
        return {"status": "success", "message": f"App '{req.target}' launched."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to execute: {e}"}

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
    items = long_memory.warm_db.query_recent(limit=30)
    return items

class ChatRequest(BaseModel):
    message: str
    persona: str = "friend"

@app.post("/api/brain/chat")
def brain_chat(req: ChatRequest):
    """Dialogue handler. Ingests user input -> summaries -> long-term memory -> API response."""
    # Check Safety Gate
    is_safe, reason = safety_gate.check_text_safety(req.message)
    if not is_safe:
        return {"text": f"⚠️ [보안 위반] {reason}", "pulse": 0.5, "stance": "neutral", "innerJoy": 0.0}

    # Generate response
    reply = chat_agent.generate_response(req.message, req.persona)
    
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
    log_entry = {
        "time": time.strftime('%H:%M:%S') if 'time' not in dir() else '00:00:00',
        "location": log.location,
        "person": log.person,
        "objects": log.objects
    }
    import time
    log_entry["time"] = time.strftime('%H:%M:%S')
    sensory_logs.append(log_entry)
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)
