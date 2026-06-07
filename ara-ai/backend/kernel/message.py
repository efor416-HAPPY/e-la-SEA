# -*- coding: utf-8 -*-
"""
✉️ ARA AI Message Structure
Represents structured message payloads passed between agents and socket layers.
"""

import json
from typing import Any

class Message:
    def __init__(self, source: str, target: str, action: str, payload: Any):
        self.source = source
        self.target = target
        self.action = action
        self.payload = payload

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "target": self.target,
            "action": self.action,
            "payload": self.payload
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        data = json.loads(json_str)
        return cls(
            source=data.get("source", ""),
            target=data.get("target", ""),
            action=data.get("action", ""),
            payload=data.get("payload", "")
        )

    def __repr__(self) -> str:
        return f"Message(source='{self.source}', target='{self.target}', action='{self.action}', payload={self.payload})"
