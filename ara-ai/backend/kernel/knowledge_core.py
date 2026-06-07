# -*- coding: utf-8 -*-
"""
📚 ARA AI Knowledge Core
Coordinates scanning and ingestion from RSS feeds, YouTube, PDFs, and local files.
"""

import os
import re
import time
from typing import List, Dict
from backend.news.rss_collector import RSSCollector
from backend.news.youtube_collector import YouTubeCollector

try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False


class KnowledgeCore:
    def __init__(self, target_dir="./ara_input_data"):
        self.target_dir = target_dir
        os.makedirs(self.target_dir, exist_ok=True)
        self.news_collector = RSSCollector("https://www.openculture.com/feed")
        self.youtube_collector = YouTubeCollector("UC18xqS40OGGyPVI-4sneOEA")

    def ingest_news(self) -> List[Dict]:
        """Scrapes news articles from standard intellectual RSS feeds."""
        items = self.news_collector.collect_items(max_items=3)
        return [
            {
                "title": item["title"],
                "link": item["link"],
                "description": item["description"],
                "source": "Ara News Collector"
            }
            for item in items
        ]

    def ingest_youtube(self) -> List[Dict]:
        """Scrapes video metadata from target YouTube channels using RSS feeds."""
        videos = self.youtube_collector.collect_videos(max_items=3)
        return [
            {
                "title": video["title"],
                "link": video["link"],
                "description": video["description"],
                "source": "Ara YouTube Collector"
            }
            for video in videos
        ]

    def ingest_pdf(self) -> List[Dict]:
        """Extracts and archives intellectual text from local PDF documents."""
        packets = []
        if not os.path.exists(self.target_dir):
            return packets

        for name in os.listdir(self.target_dir):
            if name.lower().endswith('.pdf'):
                full_path = os.path.join(self.target_dir, name)
                extracted_text = ""
                try:
                    if HAS_PYPDF:
                        with open(full_path, "rb") as f:
                            reader = pypdf.PdfReader(f)
                            for page in reader.pages[:2]:  # scan first 2 pages
                                text = page.extract_text()
                                if text:
                                    extracted_text += text + "\n"
                    else:
                        extracted_text = f"PDF Metadata extracted. Size: {os.path.getsize(full_path)/1024:.1f} KB"
                except Exception as e:
                    extracted_text = f"PDF scanning failure: {e}"

                summary = extracted_text[:150].replace("\n", " ").strip() + "..." if len(extracted_text) > 150 else extracted_text
                packets.append({
                    "title": f"PDF 지식 패킷: {name}",
                    "link": f"local-pdf://{name}",
                    "description": f"문서명: {name} | 크기: {os.path.getsize(full_path)/1024:.1f} KB | 내용: {summary}",
                    "source": "Ara PDF Collector"
                })
        return packets

    def ingest_files(self) -> List[Dict]:
        """Extracts and indexes plain text files inside the sandbox input path."""
        packets = []
        if not os.path.exists(self.target_dir):
            return packets

        valid_exts = ('.txt', '.md', '.json', '.py')
        for name in os.listdir(self.target_dir):
            if name.lower().endswith(valid_exts):
                full_path = os.path.join(self.target_dir, name)
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(500)
                    summary = content[:150].replace("\n", " ").strip() + "..." if len(content) > 150 else content
                    packets.append({
                        "title": f"로컬 파일 지식: {name}",
                        "link": f"local-file://{name}",
                        "description": f"파일명: {name} | 내용: {summary}",
                        "source": "Ara File Collector"
                    })
                except Exception as e:
                    print(f"❌ File scanning failed for {name}: {e}")
        return packets
