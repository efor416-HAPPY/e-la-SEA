# -*- coding: utf-8 -*-
"""
⚙️ ARA AI Action Core
Handles execution of local programs, opening files, and executing safe subprocess tasks.
"""

import os
import subprocess
import sys

class ActionCore:
    def __init__(self):
        self.allowed_apps = ["calc", "notepad", "mspaint"]

    def launch_app(self, app_name: str) -> bool:
        """Launches a whitelisted application in the background."""
        clean_app = app_name.lower().strip()
        if clean_app not in self.allowed_apps:
            print(f"⚠️ [ActionCore] Blocked launching unauthorized app: '{app_name}'")
            return False

        try:
            if os.name == 'nt':
                # Run asynchronously on Windows
                subprocess.Popen([clean_app], shell=True)
            else:
                subprocess.Popen([clean_app])
            print(f"✅ [ActionCore] Launched application: '{clean_app}'")
            return True
        except Exception as e:
            print(f"❌ [ActionCore] Failed to launch '{clean_app}': {e}")
            return False

    def open_file(self, file_path: str) -> bool:
        """Opens a local file in the system default reader safely."""
        abs_path = os.path.abspath(file_path)
        workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

        # Security check: Prevent Directory Traversal
        if os.path.commonpath([workspace_dir, abs_path]) != workspace_dir:
            print(f"⚠️ [ActionCore] Blocked access to path outside workspace: '{file_path}'")
            return False

        if not os.path.exists(abs_path):
            print(f"⚠️ [ActionCore] File does not exist: '{file_path}'")
            return False

        try:
            if os.name == 'nt':
                os.startfile(abs_path)
            elif sys.platform == 'darwin':
                subprocess.Popen(["open", abs_path])
            else:
                subprocess.Popen(["xdg-open", abs_path])
            print(f"✅ [ActionCore] Opened file: '{file_path}'")
            return True
        except Exception as e:
            print(f"❌ [ActionCore] Failed to open file: {e}")
            return False

    def run_task(self, task_cmd: str) -> bool:
        """Executes a system shell command safely."""
        # Check against simple injection vectors
        forbidden = ["sudo", "rm -rf", "drop table", "format c:"]
        cmd_lower = task_cmd.lower()
        if any(f in cmd_lower for f in forbidden):
            print(f"⚠️ [ActionCore] Blocked command containing forbidden phrase: '{task_cmd}'")
            return False

        try:
            subprocess.Popen(task_cmd, shell=True)
            print(f"✅ [ActionCore] Executing system task command: '{task_cmd}'")
            return True
        except Exception as e:
            print(f"❌ [ActionCore] Failed to execute task command: {e}")
            return False
