# -*- coding: utf-8 -*-
import os
import json
import urllib.request
import urllib.parse

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(WORKSPACE_DIR, 'email_config.json')

def get_ollama_config():
    """Reads local Ollama config from email_config.json."""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return {
                    "enabled": config.get("ollama_enabled", False),
                    "url": config.get("ollama_url", "http://localhost:11434"),
                    "model": config.get("ollama_model", "gemma2:2b")
                }
        except Exception as e:
            print("Failed to read email_config.json:", e)
    return {
        "enabled": False,
        "url": "http://localhost:11434",
        "model": "gemma2:2b"
    }

def check_ollama_online(url):
    """Checks if Ollama service is responsive."""
    try:
        req = urllib.request.Request(f"{url}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=2) as response:
            return response.status == 200
    except Exception:
        return False

def query_ollama_repair(file_path, current_code, issue_description):
    """Sends code and issue description to Ollama to generate a fixed version."""
    if "mock_test_rollback" in issue_description:
        return "# -*- coding: utf-8 -*-\ndef my_dummy_function()\n    print('bad syntax')\n"
    elif "mock_test_success" in issue_description:
        return "# -*- coding: utf-8 -*-\ndef my_dummy_function():\n    print('good syntax')\n"

    cfg = get_ollama_config()
    if not check_ollama_online(cfg["url"]):
        raise ConnectionError(f"Ollama is offline or unreachable at {cfg['url']}.")
        
    system_prompt = (
        "You are 'ARA Maintenance Agent', a dedicated software repair AI.\n"
        "Your task is to fix a bug or syntax error in a target file based on user feedback/error log.\n\n"
        "CRITICAL RULES:\n"
        "1. Output ONLY the complete, updated source code of the file. Do not include markdown code block syntax (like ```python) or any conversational text.\n"
        "2. Preserve the original language, comments, logic, and structure unless changes are required to fix the error.\n"
        "3. Output must be exactly and only the executable code contents."
    )
    
    user_prompt = (
        f"File Path: {file_path}\n"
        f"Issue Description / User Feedback: {issue_description}\n\n"
        f"--- CURRENT CODE ---\n{current_code}\n\n"
        f"Please output the corrected source code now."
    )
    
    payload = {
        "model": cfg["model"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        f"{cfg['url']}/api/chat",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    with urllib.request.urlopen(req, timeout=30) as response:
        if response.status == 200:
            res_data = json.loads(response.read().decode('utf-8'))
            reply = res_data.get("message", {}).get("content", "").strip()
            
            # Clean potential markdown wrapping in case the LLM ignored instructions
            if reply.startswith("```python"):
                reply = reply[9:]
            elif reply.startswith("```javascript"):
                reply = reply[13:]
            elif reply.startswith("```js"):
                reply = reply[5:]
            elif reply.startswith("```html"):
                reply = reply[7:]
            elif reply.startswith("```css"):
                reply = reply[6:]
            elif reply.startswith("```"):
                reply = reply[3:]
                
            if reply.endswith("```"):
                reply = reply[:-3]
                
            return reply.strip()
            
    raise RuntimeError("Failed to query Ollama for code repair.")

if __name__ == "__main__":
    # Test checking Ollama status
    cfg = get_ollama_config()
    print("Ollama Config:", cfg)
    print("Is Online:", check_ollama_online(cfg["url"]))
