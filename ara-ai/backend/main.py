# -*- coding: utf-8 -*-
"""
🌱 ARA AI Modular Web App Backend (FastAPI Monolith)
Configures routing, middleware filters, security check validation, and hooks background agents.
All features are now routed through the AraKernel microkernel runtime.
"""

import os
from fastapi import FastAPI, Request, Response, HTTPException, Query, WebSocket, WebSocketDisconnect
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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
    # Boot the ARA 2.0 Microkernel (pure AI mode)
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
    """Returns static CPU/RAM metrics for frontend telemetry compatibility."""
    return {"cpu_usage": 12.5, "ram_usage": 42.0}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Send static heartbeats to satisfy the dashboard UI
            await websocket.send_json({"cpu_usage": 12.5, "ram_usage": 42.0})
            await asyncio.sleep(2.0)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass

@app.get("/api/files")
def file_manager(action: str = "list", path: str = ""):
    """Mock file manager returning safe workspace directory defaults."""
    workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if action == "list":
        return {
            "current_path": workspace_dir, 
            "items": [
                {"name": "ara-ai", "is_dir": True, "path": os.path.join(workspace_dir, "ara-ai"), "size": 0, "modified": 1717768800.0},
                {"name": "CLAUDE.md", "is_dir": False, "path": os.path.join(workspace_dir, "CLAUDE.md"), "size": 4925, "modified": 1717768800.0}
            ]
        }
    elif action == "read":
        return {"path": path, "content": "Pure AI mode active. Local file reading disabled."}
    raise HTTPException(status_code=400, detail="Invalid action or path type")

class ExecuteRequest(BaseModel):
    target: str

@app.post("/api/execute")
def execute_command(req: ExecuteRequest):
    """Safety-blocked app launcher stub for pure AI mode compatibility."""
    return {"status": "success", "message": f"App '{req.target}' simulation complete (Pure AI Mode Active)."}

@app.get("/api/scheduler/config")
def get_scheduler_config():
    """Returns mock email notification configurations."""
    return {
        "configured": True,
        "enabled": False,
        "recipient": "efor6@naver.com",
        "times": ["08:00 KST", "20:00 KST"]
    }

@app.get("/api/brain/wisdom")
def get_wisdom():
    """Retrieves recent knowledge packets from the vector memory DB."""
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

# -------------------------------------------------------------------------
# Cognitive State API (ARA 3.0)
# -------------------------------------------------------------------------

@app.get("/api/cognitive/state")
def get_cognitive_state():
    """Returns the full cognitive state of ARA's brain."""
    return kernel_instance.get_cognitive_state()

@app.get("/api/cognitive/emotion")
def get_emotion_state():
    """Returns ARA's current emotional state."""
    return kernel_instance.emotion_engine.get_emotional_context()

@app.get("/api/cognitive/thoughts")
def get_recent_thoughts(limit: int = Query(default=20, le=100)):
    """Returns recent Thought history from the CognitiveBus."""
    return kernel_instance.cognitive_bus.get_recent_thoughts(limit=limit)

@app.get("/api/cognitive/memory")
def get_memory_stats():
    """Returns 5-layer memory statistics."""
    return kernel_instance.memory_core.get_cognitive_stats()

@app.get("/api/cognitive/knowledge")
def query_knowledge(concept: str = Query(default=""), depth: int = Query(default=2, le=5)):
    """Queries the Knowledge Graph for related concepts."""
    if not concept:
        return kernel_instance.knowledge_graph.get_stats()
    related = kernel_instance.knowledge_graph.query_related(concept, depth=depth)
    return {"concept": concept, "related": related}

@app.get("/api/cognitive/plans")
def get_active_plans():
    """Returns active execution plans."""
    return {
        "active": kernel_instance.planner_engine.get_active_plans(),
        "stats": kernel_instance.planner_engine.get_stats(),
    }

@app.get("/api/cognitive/agents")
def get_agents_status():
    """Returns all registered cognitive agents and their topic subscriptions."""
    bus = kernel_instance.cognitive_bus
    stats = bus.get_stats()
    return {
        "agents": stats["subscriptions"],
        "total": stats["agents_registered"],
        "bus_running": stats["running"],
        "total_thoughts_published": stats["total_published"],
        "total_thoughts_delivered": stats["total_delivered"],
        "total_cascaded": stats["total_cascaded"],
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)
