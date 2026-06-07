# -*- coding: utf-8 -*-
"""
🎥 ARA AI Gathering Subsystem: YouTube Channel Collector
Scrapes video updates from specific YouTube channels using XML feeds.
"""

import urllib.request
import re

class YouTubeCollector:
    """Retrieves public updates from a YouTube channel RSS feed without needing OAuth."""
    def __init__(self, channel_id="UC18xqS40OGGyPVI-4sneOEA"):
        self.channel_id = channel_id
        self.feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

    def collect_videos(self, max_items=3) -> list[dict]:
        """Reads entries from YouTube channel XML feed."""
        videos = []
        try:
            req = urllib.request.Request(
                self.feed_url,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req, timeout=8) as response:
                xml_data = response.read().decode('utf-8', errors='ignore')
                entries = re.findall(r'<entry>(.*?)</entry>', xml_data, re.DOTALL)
                
                for entry in entries[:max_items]:
                    title_match = re.search(r'<title>(.*?)</title>', entry, re.DOTALL)
                    link_match = re.search(r'<link[^>]*href=["\']([^"\']+)["\']', entry)
                    desc_match = re.search(r'<media:description>(.*?)</media:description>', entry, re.DOTALL)
                    
                    title = title_match.group(1) if title_match else "No Title"
                    link = link_match.group(1) if link_match else ""
                    desc = desc_match.group(1) if desc_match else ""
                    
                    if title.startswith('<![CDATA['):
                        title = title.replace('<![CDATA[', '').replace(']]>', '')
                    if desc.startswith('<![CDATA['):
                        desc = desc.replace('<![CDATA[', '').replace(']]>', '')
                    
                    summary = desc[:150] + "..." if len(desc) > 150 else desc
                    
                    videos.append({
                        "title": title.strip(),
                        "link": link.strip(),
                        "description": summary.strip(),
                        "channel_id": self.channel_id
                    })
        except Exception as e:
            print(f"❌ YouTube XML scrape failed: {e}")
        return videos
