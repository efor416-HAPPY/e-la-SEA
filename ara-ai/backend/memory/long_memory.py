# -*- coding: utf-8 -*-
"""
💾 ARA AI Knowledge Subsystem: Long Memory
Implements the 3-tier memory scheme:
  - Hot Cache (RAM, thread-safe, fast active context)
  - Warm DB (SQLite, structured queries, indexed)
  - Cold Storage (JSON, deep archival, de-duplicated)
"""

import os
import json
import sqlite3
import threading

class HotMemoryCache:
    """RAM-based cache for active reasoning context."""
    def __init__(self, limit=50):
        self.limit = limit
        self.cache = []
        self.lock = threading.Lock()

    def add(self, item: dict):
        with self.lock:
            # Prevent duplicate links
            self.cache = [x for x in self.cache if x.get('link') != item.get('link')]
            self.cache.insert(0, item)
            if len(self.cache) > self.limit:
                self.cache.pop()

    def get_all(self) -> list[dict]:
        with self.lock:
            return list(self.cache)

class WarmMemoryDB:
    """SQLite database for fast structured querying and indexing."""
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

    def insert_or_update(self, item: dict):
        with sqlite3.connect(self.db_path) as conn:
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

    def get_count(self) -> int:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM warm_wisdom")
                return cursor.fetchone()[0]
        except Exception:
            return 0

    def query_recent(self, limit=30) -> list[dict]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM warm_wisdom ORDER BY scraped_at DESC LIMIT ?", (limit,))
                rows = cursor.fetchall()
                return [dict(r) for r in rows]
        except Exception:
            return []

class LongMemoryManager:
    """Coordinates Hot (RAM), Warm (SQLite), and Cold (JSON) memory tiers."""
    def __init__(self, db_path="downloads/ara_warm_memory.db", cold_file="downloads/accumulated_wisdom.json"):
        self.hot_memory = HotMemoryCache(limit=50)
        self.warm_db = WarmMemoryDB(db_path)
        self.cold_file = cold_file
        self.lock = threading.Lock()

    def store_wisdom(self, item: dict):
        """Stores knowledge across all 3 tiers."""
        # 1. Hot Cache (RAM)
        self.hot_memory.add(item)

        # 2. Warm SQLite DB
        try:
            self.warm_db.insert_or_update(item)
        except Exception as e:
            print(f"❌ Warm Memory DB storage failed: {e}")

        # 3. Cold JSON Archive
        with self.lock:
            cold_items = []
            if os.path.exists(self.cold_file):
                try:
                    with open(self.cold_file, 'r', encoding='utf-8') as f:
                        cold_items = json.load(f)
                except Exception:
                    pass

            # De-duplicate and insert newest
            cold_items = [x for x in cold_items if x.get('link') != item.get('link')]
            cold_items.insert(0, item)
            cold_items.sort(key=lambda x: x.get('scraped_at', ''), reverse=True)

            try:
                with open(self.cold_file, 'w', encoding='utf-8') as f:
                    json.dump(cold_items, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"❌ Cold Memory file storage failed: {e}")

    def get_stats(self) -> tuple[int, int, int]:
        """Returns counts for Hot, Warm, and Cold tiers."""
        hot_count = len(self.hot_memory.get_all())
        warm_count = self.warm_db.get_count()

        cold_count = 0
        if os.path.exists(self.cold_file):
            try:
                with open(self.cold_file, 'r', encoding='utf-8') as f:
                    cold_count = len(json.load(f))
            except Exception:
                pass
        return hot_count, warm_count, cold_count

    def search_memory(self, query: str) -> list[dict]:
        """Search memory for keywords in title/description (basic text search)."""
        results = []
        recent_items = self.warm_db.query_recent(limit=100)
        query_lower = query.lower()
        for item in recent_items:
            if query_lower in item.get('title', '').lower() or query_lower in item.get('description', '').lower():
                results.append(item)
        return results

# Global long memory coordinator
long_memory = LongMemoryManager()
