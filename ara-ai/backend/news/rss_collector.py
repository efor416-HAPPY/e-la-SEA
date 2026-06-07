# -*- coding: utf-8 -*-
"""
📰 ARA AI Gathering Subsystem: RSS News Collector
Parses generic RSS feeds and converts them into standardized knowledge transfer schemas.
"""

import urllib.request
import re
import xml.etree.ElementTree as ET

class RSSCollector:
    """Scrapes news articles from public RSS XML feeds."""
    def __init__(self, rss_url: str):
        self.rss_url = rss_url

    def collect_items(self, max_items=3) -> list[dict]:
        """Fetches and parses feed entries."""
        items = []
        try:
            req = urllib.request.Request(
                self.rss_url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            with urllib.request.urlopen(req, timeout=8) as response:
                xml_data = response.read().decode('utf-8', errors='ignore')
                
                # Extract item/entry tags
                item_blocks = re.findall(r'<item>(.*?)</item>', xml_data, re.DOTALL)
                if not item_blocks:
                    item_blocks = re.findall(r'<entry>(.*?)</entry>', xml_data, re.DOTALL)

                for block in item_blocks[:max_items]:
                    title_match = re.search(r'<title>(.*?)</title>', block, re.DOTALL)
                    
                    href_match = re.search(r'<link[^>]*href=["\']([^"\']+)["\']', block)
                    if href_match:
                        link = href_match.group(1)
                    else:
                        link_match = re.search(r'<link>(.*?)</link>', block, re.DOTALL)
                        link = link_match.group(1) if link_match else ""

                    desc_match = re.search(r'<description>(.*?)</description>', block, re.DOTALL)
                    if not desc_match:
                        desc_match = re.search(r'<summary>(.*?)</summary>', block, re.DOTALL)
                    
                    title = title_match.group(1) if title_match else "No Title"
                    link = link.strip()
                    desc = desc_match.group(1) if desc_match else ""

                    # Clean CDATA sections
                    if title.startswith('<![CDATA['):
                        title = title.replace('<![CDATA[', '').replace(']]>', '')
                    if link.startswith('<![CDATA['):
                        link = link.replace('<![CDATA[', '').replace(']]>', '')
                    if desc.startswith('<![CDATA['):
                        desc = desc.replace('<![CDATA[', '').replace(']]>', '')

                    # Clean HTML tags
                    desc_clean = re.sub('<[^<]+?>', '', desc).strip()
                    desc_clean = desc_clean.replace('&nbsp;', ' ').replace('&quot;', '"').replace('&amp;', '&')
                    desc_clean = desc_clean[:200] + "..." if len(desc_clean) > 200 else desc_clean

                    items.append({
                        "title": title.strip(),
                        "link": link,
                        "description": desc_clean
                    })
        except Exception as e:
            print(f"❌ RSS collection failed from {self.rss_url}: {e}")
        return items
