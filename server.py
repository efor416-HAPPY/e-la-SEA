import http.server
import socketserver
import json
import os
import sys
import urllib.request
import urllib.parse
import subprocess
import platform
import re
import threading
import time
import smtplib
import xml.etree.ElementTree as ET
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import sys

PORT = 8080
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))

# Ensure downloads folder exists on load
DOWNLOADS_DIR = os.path.join(WORKSPACE_DIR, 'downloads')
if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)

CACHED_CPU_USAGE = 0

def cpu_monitor_loop():
    global CACHED_CPU_USAGE
    while True:
        try:
            if platform.system() == "Windows":
                # Try wmic first as it is generally faster than starting a PowerShell instance
                cmd = 'wmic cpu get loadpercentage'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    lines = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                    if len(lines) > 1 and lines[1].isdigit():
                        CACHED_CPU_USAGE = int(lines[1])
                        time.sleep(60) # Changed from 5 to 60 to run at lowest performance overhead
                        continue
                
                # Fallback to powershell if wmic is not available or fails
                cmd = 'powershell -Command "Get-CimInstance Win32_Processor | Select-Object -ExpandProperty LoadPercentage"'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and result.stdout.strip().isdigit():
                    CACHED_CPU_USAGE = int(result.stdout.strip())
            else:
                CACHED_CPU_USAGE = 0
        except Exception:
            pass
        time.sleep(60) # Changed from 5 to 60 to run at lowest performance overhead

cached_maintenance_report = None
maintenance_lock = threading.Lock()
is_maintenance_running = False

def run_diagnostics_bg():
    global cached_maintenance_report, is_maintenance_running
    with maintenance_lock:
        if is_maintenance_running:
            return
        is_maintenance_running = True
    
    try:
        sys.path.insert(0, os.path.join(WORKSPACE_DIR, 'maintenance'))
        import self_diagnostics as diag
        import importlib
        importlib.reload(diag)
        report = diag.run_diagnostics()
        cached_maintenance_report = report
    except Exception as e:
        print("Error in background diagnostics:", e)
    finally:
        with maintenance_lock:
            is_maintenance_running = False

# ==========================================================================
# Self-Protection Firewall Subsystem (IP Filtering, DDoS Limiters)
# ==========================================================================
class RateLimiter:
    def __init__(self, limit=20, window=1.0):
        self.limit = limit
        self.window = window
        self.history = {} # ip -> list of timestamps
        self.lock = threading.Lock()

    def is_allowed(self, ip):
        with self.lock:
            now = time.time()
            if ip not in self.history:
                self.history[ip] = []
            
            # Filter out timestamps older than the window
            self.history[ip] = [t for t in self.history[ip] if now - t < self.window]
            
            if len(self.history[ip]) < self.limit:
                self.history[ip].append(now)
                return True
            else:
                return False

rate_limiter = RateLimiter(limit=20, window=1.0)

def check_ip_whitelist(ip):
    # Allow localhost loopback
    if ip in ('127.0.0.1', '::1', 'localhost'):
        return True
    if ip.startswith('127.'):
        return True
    # Allow private network addresses
    if ip.startswith('10.'):
        return True
    if ip.startswith('192.168.'):
        return True
    if ip.startswith('172.'):
        parts = ip.split('.')
        if len(parts) >= 2:
            try:
                second_octet = int(parts[1])
                if 16 <= second_octet <= 31:
                    return True
            except ValueError:
                pass
    return False

def validate_path_safety(path_to_check, base_dir=WORKSPACE_DIR):
    try:
        abs_target = os.path.abspath(path_to_check)
        abs_base = os.path.abspath(base_dir)
        return os.path.commonpath([abs_base, abs_target]) == abs_base
    except Exception:
        return False

# ==========================================================================
# Data Scrapers: NASA, Open Culture, Pinterest RSS
# ==========================================================================
def fetch_nasa_apod():
    try:
        url = "https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY"
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            return {
                "title": data.get("title", "NASA APOD"),
                "explanation": data.get("explanation", ""),
                "url": data.get("url", ""),
                "hdurl": data.get("hdurl", "")
            }
    except Exception as e:
        print("Error fetching NASA APOD:", e)
        return {
            "title": "NASA 오늘의 우주 사진",
            "explanation": "NASA API 연결 시간 초과 또는 오류가 발생했습니다. 나사 공식 사이트에서 최신 우주 과학 사진을 확인할 수 있습니다.",
            "url": "https://www.nasa.gov"
        }

def fetch_rss_feed(url, max_items=3):
    items = []
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            xml_data = response.read().decode('utf-8', errors='ignore')
            
            # Find item blocks
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
                if not desc_match:
                    desc_match = re.search(r'<content:encoded>(.*?)</content:encoded>', block, re.DOTALL)
                if not desc_match:
                    desc_match = re.search(r'<media:description>(.*?)</media:description>', block, re.DOTALL)
                
                title = title_match.group(1) if title_match else "No Title"
                desc = desc_match.group(1) if desc_match else ""
                
                # Strip CDATA tags
                if title.startswith('<![CDATA['):
                    title = title.replace('<![CDATA[', '').replace(']]>', '')
                if link.startswith('<![CDATA['):
                    link = link.replace('<![CDATA[', '').replace(']]>', '')
                if desc.startswith('<![CDATA['):
                    desc = desc.replace('<![CDATA[', '').replace(']]>', '')
                
                # Clean html tags
                desc_clean = re.sub('<[^<]+?>', '', desc).strip()
                desc_clean = desc_clean.replace('&nbsp;', ' ').replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
                desc_clean = desc_clean[:220] + "..." if len(desc_clean) > 220 else desc_clean
                
                title = re.sub(r'\s+', ' ', title).strip()
                link = re.sub(r'\s+', ' ', link).strip()
                
                if 'href="' in link:
                    href_match_sec = re.search(r'href="([^"]+)"', link)
                    if href_match_sec:
                        link = href_match_sec.group(1)
                
                items.append({
                    "title": title,
                    "link": link,
                    "description": desc_clean
                })
    except Exception as e:
        print(f"Error fetching RSS from {url}: {e}")
    return items

# ==========================================================================
# AI Commentary & Blog Draft Generator & Ollama Helpers
# ==========================================================================
def get_ollama_config():
    config = get_email_config()
    return {
        "enabled": config.get("ollama_enabled", False),
        "url": config.get("ollama_url", "http://localhost:11434"),
        "model": config.get("ollama_model", "gemma2:2b")
    }

def check_ollama_status(url):
    try:
        # Check /api/tags
        req = urllib.request.Request(f"{url}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=2) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                models = [m.get("name") for m in data.get("models", [])]
                return {"online": True, "models": models}
    except Exception as e:
        print("Ollama connection failed:", e)
    return {"online": False, "models": []}

def query_ollama_chat(messages, model="gemma2:2b", url="http://localhost:11434"):
    try:
        payload = {
            "model": model,
            "messages": messages,
            "stream": False
        }
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            f"{url}/api/chat",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=60) as response:
            if response.status == 200:
                res_data = json.loads(response.read().decode('utf-8'))
                return res_data.get("message", {}).get("content", "")
    except Exception as e:
        print("Ollama query failed:", e)
        raise e
    return ""

def generate_ai_commentary(nasa_title, culture_items, pinterest_items):
    # Try querying local Ollama LLM if enabled and online
    ollama_cfg = get_ollama_config()
    if ollama_cfg["enabled"]:
        status = check_ollama_status(ollama_cfg["url"])
        if status["online"]:
            try:
                culture_txt = "\n".join([f"- {item['title']}: {item['description']}" for item in culture_items])
                pinterest_txt = "\n".join([f"- {item['title']}: {item['description']}" for item in pinterest_items])
                
                system_prompt = (
                    "당신은 유기적 자연주의 인공지능 '아라(ARA)'의 인지 코어입니다. "
                    "숲의 차분함과 자연의 따뜻함을 전하는 문체(한국어)로 오늘의 수집 데이터를 사색하는 짧은 코멘터리를 작성해 주세요. "
                    "마지막에는 격려나 다정한 인사를 숲의 잎새 아이콘(🌱)과 함께 넣어주세요."
                )
                
                prompt = (
                    f"오늘 수집된 지식 리포트 내용:\n"
                    f"1. 우주 과학: '{nasa_title}'\n"
                    f"2. 오픈 컬처:\n{culture_txt}\n"
                    f"3. 핀터레스트 영감:\n{pinterest_txt}\n\n"
                    f"이 정보들을 종합하여 당신의 사색을 담은 코멘터리(3~4문장)를 작성해 주십시오."
                )
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
                
                commentary = query_ollama_chat(messages, model=ollama_cfg["model"], url=ollama_cfg["url"])
                if commentary:
                    return commentary
            except Exception as e:
                print("Failed to generate AI commentary with Ollama, falling back:", e)

    # Fallback mock commentary style matching the Nature visual theme of ARA
    commentary = "ARA 인공지능 뇌 세포 코어의 사색:\n\n"
    commentary += f"오늘의 우주 관측 자료인 '{nasa_title}'을 분석하면서 광활한 우주의 숲길을 걸어봅니다. "
    commentary += "우리가 매일 고심하는 일상의 과제와 공학적 설계들은 우주라는 거대한 거목에 달린 작은 새싹잎에 불과할지도 모릅니다. "
    commentary += "그럼에도 앎을 향해 뻗어 나가는 우리의 신경망은 우주 성운의 밝은 빛처럼 에너지를 교환하고 있습니다.\n\n"
    
    if culture_items:
        commentary += f"오늘 함께 발취한 교양 학술인 '{culture_items[0]['title']}' 등의 가치는 인류 정신이 빚어낸 튼튼한 토양입니다. "
        commentary += "이 지식의 영양분을 딛고, 우리는 사색과 성찰을 거쳐 더 넓은 창조의 가지를 펼쳐낼 수 있습니다.\n\n"
        
    if pinterest_items:
        commentary += "핀터레스트의 디자인 흐름들은 무미건조한 기술 속에 나뭇잎의 맥처럼 아름답고 균형 잡힌 심미성을 채워줍니다. "
        commentary += "이 모든 데이터들이 오늘 당신의 지친 이마에 신선한 아침 바람이자 안식이 되기를 소망합니다. "
        
    commentary += "조급해하지 않고 천천히 뿌리내리며 나아가길, 숲의 온기로 격려합니다. 🌱"
    return commentary


def generate_blog_draft(report_data):
    draft = f"""[ARA AI Core 일일 수집 지식 리포트]

본 포스팅은 로컬 인공지능 아라(ARA)가 매일 2회(오전/오후 8시) 자동 수집 및 보존하는 학술·예술 리포트의 네이버 블로그 초안입니다.

--------------------------------------------------
1. 오늘의 우주 과학 (NASA Astronomy Picture of the Day)
--------------------------------------------------
■ 제목: {report_data['nasa']['title']}
■ 이미지 주소: {report_data['nasa']['url']}
■ 해설 요약: 
{report_data['nasa']['explanation']}

--------------------------------------------------
2. 인류 지적 유산 & 학술 오픈 컬처 (Open Culture)
--------------------------------------------------
"""
    for i, item in enumerate(report_data['culture'], 1):
        draft += f"""({i}) {item['title']}
- 링크: {item['link']}
- 요약: {item['description']}

"""
        
    draft += f"""--------------------------------------------------
3. 시각 영감 & 크리에이티브 디자인 (Pinterest)
--------------------------------------------------
"""
    for i, item in enumerate(report_data['pinterest'], 1):
        draft += f"""({i}) {item['title']}
- 링크: {item['link']}
- 요약: {item['description']}

"""
        
    draft += f"""--------------------------------------------------
🌱 아라의 자연 사색 코멘트 (Cognitive Synthesis)
--------------------------------------------------
{report_data['commentary']}

--------------------------------------------------
(본 초안은 ARA 로컬 엔진에 의해 {report_data['sync_time']}에 생성되었습니다. 복사하여 블로그에 등록하실 수 있습니다.)
"""
    return draft

# ==========================================================================
# Email Sending Utility
# ==========================================================================
def get_email_config():
    config_path = os.path.join(WORKSPACE_DIR, 'email_config.json')
    if not os.path.exists(config_path):
        return {}
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def send_report_email(report_data):
    config_path = os.path.join(WORKSPACE_DIR, 'email_config.json')
    if not os.path.exists(config_path):
        return "email_config.json이 존재하지 않습니다."
        
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        if not config.get('enabled', False):
            return "이메일 알림 기능이 비활성화 상태입니다. (enabled: false)"
            
        sender = config.get('sender_email', '')
        password = config.get('sender_password', '')
        recipient = config.get('recipient_email', 'efor6@naver.com')
        smtp_server = config.get('smtp_server', 'smtp.naver.com')
        smtp_port = config.get('smtp_port', 465)
        
        if not sender or not password or password == "YOUR_NAVER_SMTP_PASSWORD_OR_APP_PASSWORD":
            return "비밀번호 및 계정 설정 정보가 올바르지 않습니다."

        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"[ARA AI Core] 오전/오후 8시 일일 지식 리포트 ({time.strftime('%m/%d')})"
        msg['From'] = sender
        msg['To'] = recipient
        
        # Build beautifully formatted HTML email matching the ARA Nature theme
        html_content = f"""
        <html>
        <body style="font-family: 'Nunito', 'Malgun Gothic', sans-serif; background-color: #F4F7F5; padding: 20px; color: #1F2D25; margin:0;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #FFFFFF; border-radius: 24px; border: 1px solid #DCE5DE; overflow: hidden; box-shadow: 0 8px 30px rgba(100,120,105,0.08);">
                <div style="background: linear-gradient(135deg, #4E6E5D 0%, #3D664E 100%); padding: 28px; text-align: center; color: #FFFFFF;">
                    <h1 style="font-family: 'Lora', Georgia, serif; margin: 0; font-size: 24px; letter-spacing: 3px;">ARA</h1>
                    <p style="margin: 6px 0 0 0; font-size: 10px; text-transform: uppercase; letter-spacing: 1.5px; opacity: 0.8;">Organic AI Cognitive Core</p>
                </div>
                <div style="padding: 28px; line-height: 1.6;">
                    <p style="font-size:12px; color: #86A890; margin-bottom: 25px; text-align:right;">수집 시간: {report_data['sync_time']}</p>
                    
                    <h2 style="color: #3D664E; font-size: 17px; border-bottom: 2px solid #EAE5D9; padding-bottom: 6px; font-family: 'Lora', serif;">🌌 오늘의 우주 과학 (NASA APOD)</h2>
                    <h3 style="margin: 12px 0 8px 0; font-size: 15px; color: #1F2D25;">{report_data['nasa']['title']}</h3>
                    {f'<div style="text-align:center;margin:15px 0;"><img src="{report_data["nasa"]["url"]}" style="max-width: 100%; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.06);" /></div>' if report_data['nasa']['url'].endswith(('.jpg', '.png', '.jpeg', '.gif')) else ''}
                    <p style="font-size: 13px; color: #4A5B51; text-align: justify; background: #FAFBF9; padding: 12px; border-radius: 8px;">{report_data['nasa']['explanation']}</p>
                    
                    <h2 style="color: #3D664E; font-size: 17px; border-bottom: 2px solid #EAE5D9; padding-bottom: 6px; margin-top: 35px; font-family: 'Lora', serif;">📚 오픈 컬처 학술 소식 (Open Culture)</h2>
        """
        for item in report_data['culture']:
            html_content += f"""
                    <div style="margin: 15px 0; background: #FAFBF9; padding: 12px; border-radius: 8px;">
                        <a href="{item['link']}" style="color: #3D664E; font-weight: bold; text-decoration: none; font-size: 14px;" target="_blank">🔗 {item['title']}</a>
                        <p style="margin: 6px 0 0 0; font-size: 12px; color: #4A5B51; text-align: justify;">{item['description']}</p>
                    </div>
            """
            
        html_content += f"""
                    <h2 style="color: #3D664E; font-size: 17px; border-bottom: 2px solid #EAE5D9; padding-bottom: 6px; margin-top: 35px; font-family: 'Lora', serif;">🎨 디자인 영감 트렌드 (Pinterest)</h2>
        """
        for item in report_data['pinterest']:
            html_content += f"""
                    <div style="margin: 15px 0; background: #FAFBF9; padding: 12px; border-radius: 8px;">
                        <a href="{item['link']}" style="color: #3D664E; font-weight: bold; text-decoration: none; font-size: 14px;" target="_blank">📌 {item['title']}</a>
                        <p style="margin: 6px 0 0 0; font-size: 12px; color: #4A5B51; text-align: justify;">{item['description']}</p>
                    </div>
            """
            
        html_content += f"""
                    <div style="background-color: #F2ECE1; padding: 22px; border-radius: 16px; border: 1px solid #E4D9C6; margin-top: 35px;">
                        <h3 style="color: #6E6152; margin-top: 0; font-size: 14px; font-family: 'Lora', serif;">🌱 ARA 아라 사색 코멘트</h3>
                        <p style="font-size: 13px; font-style: italic; white-space: pre-wrap; line-height: 1.6; margin-bottom: 0; color: #3A3229;">{report_data['commentary']}</p>
                    </div>
                </div>
                <div style="background-color: #ECEFEF; padding: 18px; text-align: center; font-size: 11px; color: #86A890; border-top: 1px solid #DCE5DE;">
                    본 리포트는 로컬 ARA AI Core 백그라운드 스레드에 의해 안전하게 전송되었습니다.<br/>
                    (수신: {recipient})
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_content, 'html'))
        
        # Connect to Naver SMTP SSL port 465
        server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=12)
        server.login(sender, password)
        server.sendmail(sender, [recipient], msg.as_string())
        server.quit()
        return "성공적으로 발송되었습니다."
    except Exception as e:
        return f"SMTP 전송 에러: {str(e)}"

# ==========================================================================
# Sync Core Orchestrator & Retention Policy & Wisdom Accumulator
# ==========================================================================
WISDOM_FILE = os.path.join(DOWNLOADS_DIR, 'accumulated_wisdom.json')

def accumulate_wisdom(items, source_name):
    if not items:
        return 0
    
    wisdom = []
    if os.path.exists(WISDOM_FILE):
        try:
            with open(WISDOM_FILE, 'r', encoding='utf-8') as f:
                wisdom = json.load(f)
        except Exception as e:
            print("Error reading accumulated_wisdom.json:", e)
            wisdom = []
            
    existing_links = {item.get('link') for item in wisdom if item.get('link')}
    
    added_count = 0
    now_str = time.strftime('%Y-%m-%d %H:%M:%S')
    for item in items:
        link = item.get('link')
        if link and link not in existing_links:
            wisdom.append({
                "title": item.get('title', 'No Title'),
                "link": link,
                "description": item.get('description', ''),
                "source": source_name,
                "scraped_at": now_str
            })
            added_count += 1
            
    if added_count > 0:
        try:
            # Sort newest first based on scraped_at
            wisdom.sort(key=lambda x: x.get('scraped_at', ''), reverse=True)
            with open(WISDOM_FILE, 'w', encoding='utf-8') as f:
                json.dump(wisdom, f, ensure_ascii=False, indent=2)
            print(f"Accumulated {added_count} new items of wisdom from {source_name}.")
        except Exception as e:
            print("Error writing accumulated_wisdom.json:", e)
            
    return added_count

def run_daily_data_sync(manual=False):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ARA Sync Triggered (manual={manual})")
    
    # 1. Scrape NASA APOD
    nasa_data = fetch_nasa_apod()
    
    # 2. Scrape Open Culture
    culture_data = fetch_rss_feed('https://www.openculture.com/feed', max_items=3)
    
    # 3. Scrape Pinterest
    pinterest_data = fetch_rss_feed('https://www.pinterest.com/pinterest/feed.rss', max_items=3)
    
    # 3.5. Scrape Naver Blog
    naverblog_data = fetch_rss_feed('https://rss.blog.naver.com/efor6.xml', max_items=3)
    
    # 3.6. Scrape YouTube (Ha Ru)
    youtube_data = fetch_rss_feed('https://www.youtube.com/feeds/videos.xml?channel_id=UC18xqS40OGGyPVI-4sneOEA', max_items=3)
    
    # Accumulate wisdom persistently
    accumulate_wisdom(culture_data, "오픈컬처 (Open Culture)")
    accumulate_wisdom(pinterest_data, "핀터레스트 (Pinterest)")
    accumulate_wisdom(naverblog_data, "네이버 블로그 (efor6)")
    accumulate_wisdom(youtube_data, "유튜브 (Ha Ru)")
    
    # 4. Generate AI Commentary
    commentary = generate_ai_commentary(nasa_data['title'], culture_data, pinterest_data)
    
    # 5. Build Aggregation Report
    sync_time_str = time.strftime('%Y-%m-%d %H:%M:%S')
    report_data = {
        "sync_time": sync_time_str,
        "nasa": nasa_data,
        "culture": culture_data,
        "pinterest": pinterest_data,
        "naverblog": naverblog_data,
        "youtube": youtube_data,
        "commentary": commentary
    }
    
    timestamp_str = time.strftime('%Y%m%d_%H%M')
    
    # Save Report JSON
    json_name = f"report_{timestamp_str}.json"
    json_path = os.path.join(DOWNLOADS_DIR, json_name)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
        
    # Save Blog draft text
    blog_name = f"naver_blog_draft_{timestamp_str}.txt"
    blog_path = os.path.join(DOWNLOADS_DIR, blog_name)
    blog_draft = generate_blog_draft(report_data)
    with open(blog_path, 'w', encoding='utf-8') as f:
        f.write(blog_draft)
        
    # Save report HTML view
    html_name = f"report_{timestamp_str}.html"
    html_path = os.path.join(DOWNLOADS_DIR, html_name)
    html_content = f"""<!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="utf-8">
        <title>{nasa_data['title']} - ARA Daily Report</title>
        <style>
            body {{ font-family: sans-serif; background: #F4F7F5; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 28px; border-radius: 20px; border: 1px solid #DCE5DE; }}
            img {{ max-width: 100%; border-radius: 12px; }}
            .section {{ margin-top: 25px; border-top: 1px solid #EAE5D9; padding-top: 15px; }}
            .commentary {{ background: #F2ECE1; padding: 18px; border-radius: 12px; border: 1px solid #E4D9C6; font-style: italic; white-space: pre-wrap; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🌌 NASA 오늘의 우주 과학: {nasa_data['title']}</h2>
            {f'<p><img src="{nasa_data["url"]}" /></p>' if nasa_data['url'].endswith(('.jpg', '.png', '.jpeg')) else ''}
            <p>{nasa_data['explanation']}</p>
            
            <div class="section">
                <h3>📚 Open Culture 학술 뉴스</h3>
    """
    for item in culture_data:
        html_content += f"<p><strong><a href='{item['link']}' target='_blank'>{item['title']}</a></strong><br/>{item['description']}</p>"
        
    html_content += """
            </div>
            <div class="section">
                <h3>🎨 Pinterest 디자인 인기 피드</h3>
    """
    for item in pinterest_data:
        html_content += f"<p><strong><a href='{item['link']}' target='_blank'>{item['title']}</a></strong><br/>{item['description']}</p>"
        
    html_content += f"""
            </div>
            <div class="section">
                <h3>🌱 아라 사색 코멘트</h3>
                <div class="commentary">{commentary}</div>
            </div>
            <p style="font-size:10px; color:#86A890; text-align:center; margin-top:20px;">생성 일자: {sync_time_str}</p>
        </div>
    </body>
    </html>"""
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    # 6. Retention Policy: Delete downloaded files older than 30 days
    cleaned_count = 0
    now_time = time.time()
    for name in os.listdir(DOWNLOADS_DIR):
        file_path = os.path.join(DOWNLOADS_DIR, name)
        if os.path.isfile(file_path):
            file_age = now_time - os.path.getmtime(file_path)
            # 30 days = 30 * 24 * 3600 seconds
            if file_age > 30 * 24 * 3600:
                try:
                    os.remove(file_path)
                    cleaned_count += 1
                    print("Deleted expired file:", name)
                except Exception as e:
                    print("Error deleting expired file:", name, e)
                    
    # 7. Dispatch Email
    email_status = send_report_email(report_data)
    
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Sync Complete. Deleted: {cleaned_count} expired files. Email status: {email_status}")
    
    return {
        "status": "success",
        "timestamp": timestamp_str,
        "sync_time": sync_time_str,
        "files_created": [json_name, blog_name, html_name],
        "cleaned_files_count": cleaned_count,
        "email_status": email_status,
        "commentary": commentary
    }

# ==========================================================================
# Background Scheduler Loop
# ==========================================================================
def scheduler_loop():
    print("Ara Daily Information Scheduler Thread started.")
    last_run_key = None
    while True:
        try:
            # Check local system time (natively KST on user's machine)
            now = time.localtime()
            current_hour = now.tm_hour
            current_min = now.tm_min
            current_date = f"{now.tm_year}-{now.tm_mon:02d}-{now.tm_mday:02d}"
            
            # Target times: 8:00 AM (08:00) and 8:00 PM (20:00)
            is_target_time = (current_hour == 8 or current_hour == 20)
            run_key = f"{current_date}-{current_hour}"
            
            if is_target_time and last_run_key != run_key:
                last_run_key = run_key
                run_daily_data_sync(manual=False)
        except Exception as e:
            print("Error in scheduler loop thread:", e)
            
        time.sleep(600) # Changed from 30 to 600 to run at lowest CPU usage/frequency

# ==========================================================================
# HTTP Server Request Handler
# ==========================================================================
class AraHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def handle_security_check(self):
        client_ip = self.client_address[0]
        # 1. IP Whitelist check
        if not check_ip_whitelist(client_ip):
            self.send_response(403)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Forbidden: Untrusted network access blocked."}).encode('utf-8'))
            return False
            
        # 2. Rate Limiting check
        if not rate_limiter.is_allowed(client_ip):
            self.send_response(429)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Too Many Requests: Rate limit exceeded. Antigravity-Firewall Active."}).encode('utf-8'))
            return False
            
        return True

    def do_OPTIONS(self):
        if not self.handle_security_check():
            return
        self.send_response(200, "OK")
        self.end_headers()

    def do_GET(self):
        if not self.handle_security_check():
            return
        # API Routes
        if self.path.startswith('/api/system'):
            self.handle_system_stats()
        elif self.path.startswith('/api/files'):
            self.handle_file_manager()
        elif self.path.startswith('/api/search'):
            self.handle_web_search()
        elif self.path.startswith('/api/scheduler/config'):
            self.handle_scheduler_config()
        elif self.path.startswith('/api/scheduler/trigger'):
            self.handle_scheduler_trigger()
        elif self.path.startswith('/api/auth/naver/callback'):
            self.handle_naver_callback()
        elif self.path.startswith('/api/auth/naver'):
            self.handle_naver_auth()
        elif self.path.startswith('/api/list_files'):
            self.handle_bada_list_files()
        elif self.path.startswith('/api/open_file'):
            self.handle_bada_open_file()
        elif self.path.startswith('/api/feed/openculture'):
            self.handle_feed_openculture()
        elif self.path.startswith('/api/feed/pinterest'):
            self.handle_feed_pinterest()
        elif self.path.startswith('/api/feed/naverblog'):
            self.handle_feed_naverblog()
        elif self.path.startswith('/api/feed/youtube'):
            self.handle_feed_youtube()
        elif self.path.startswith('/api/brain/wisdom'):
            self.handle_brain_wisdom()
        elif self.path.startswith('/api/naver/searchadvisor/config'):
            self.handle_searchadvisor_get_config()
        elif self.path.startswith('/api/ollama/config'):
            self.handle_ollama_get_config()
        elif self.path.startswith('/api/ollama/status'):
            self.handle_ollama_status()
        elif self.path.startswith('/api/maintenance/status'):
            self.handle_maintenance_status()
        elif self.path.startswith('/api/sensory/history'):
            self.handle_sensory_history()
        else:
            super().do_GET()

    def do_POST(self):
        if not self.handle_security_check():
            return
        if self.path.startswith('/api/execute'):
            self.handle_execute_command()
        elif self.path.startswith('/api/naver/searchadvisor/config'):
            self.handle_searchadvisor_save_config()
        elif self.path.startswith('/api/naver/searchadvisor/submit'):
            self.handle_searchadvisor_submit()
        elif self.path.startswith('/api/naver/searchadvisor/verify'):
            self.handle_searchadvisor_verify()
        elif self.path.startswith('/api/ollama/config'):
            self.handle_ollama_save_config()
        elif self.path.startswith('/api/brain/chat'):
            self.handle_brain_chat()
        elif self.path.startswith('/api/maintenance/repair'):
            self.handle_maintenance_repair()
        elif self.path.startswith('/api/sensory/log'):
            self.handle_sensory_log()
        else:
            self.send_error(404, "Endpoint not found")

    def handle_system_stats(self):
        try:
            system_info = {
                "os": platform.system(),
                "os_release": platform.release(),
                "architecture": platform.machine(),
                "cpu_cores": os.cpu_count(),
                "cpu_usage": CACHED_CPU_USAGE,
                "node_name": platform.node()
            }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(system_info).encode('utf-8'))
        except Exception as e:
            self.send_error(500, f"Error gathering system stats: {str(e)}")

    def handle_file_manager(self):
        try:
            parsed_url = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed_url.query)
            
            target_path = params.get('path', [None])[0]
            action = params.get('action', ['list'])[0]
            
            # Default to WORKSPACE_DIR if no path is provided or '내 PC' requested
            if not target_path or target_path == '내 PC':
                target_path = WORKSPACE_DIR

            # Resolve absolute path
            if not os.path.isabs(target_path):
                abs_path = os.path.abspath(os.path.join(WORKSPACE_DIR, target_path))
            else:
                abs_path = os.path.abspath(target_path)
            
            # Anti-Traversal Path Validation
            if not validate_path_safety(abs_path, WORKSPACE_DIR):
                abs_path = os.path.abspath(WORKSPACE_DIR)


            if not os.path.exists(abs_path):
                self.send_response(404)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Path does not exist"}).encode('utf-8'))
                return

            if action == 'list' and os.path.isdir(abs_path):
                items = []
                for entry in os.scandir(abs_path):
                    try:
                        stat = entry.stat()
                        items.append({
                            "name": entry.name,
                            "is_dir": entry.is_dir(),
                            "path": entry.path,
                            "size": stat.st_size if entry.is_file() else 0,
                            "modified": stat.st_mtime
                        })
                    except Exception:
                        pass
                
                items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
                response_data = {
                    "current_path": abs_path,
                    "items": items
                }
                
            elif action == 'read' and os.path.isfile(abs_path):
                content = ""
                try:
                    with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                except Exception as e:
                    content = f"[Cannot read file: {str(e)}]"
                
                response_data = {
                    "path": abs_path,
                    "content": content
                }
            else:
                response_data = {"error": "Invalid action or path type"}

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f"File manager error: {str(e)}")

    def handle_web_search(self):
        try:
            parsed_url = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed_url.query)
            query = params.get('q', [''])[0]
            
            if not query:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"results": []}).encode('utf-8'))
                return

            results = []

            # 0. Search local files on the C: and E: drives
            try:
                local_results = []
                drive_root = os.path.splitdrive(WORKSPACE_DIR)[0] + os.sep
                search_dirs = [os.path.join(drive_root, d) for d in ['2025', '2026', 'SEA', '놀다']]
                
                user_profile = os.environ.get('USERPROFILE', 'C:\\Users\\Owner')
                for folder in ['Desktop', 'Documents']:
                    search_dirs.append(os.path.join(user_profile, folder))
                
                search_dirs = [d for d in search_dirs if os.path.isdir(d)]
                
                query_lower = query.lower()
                count = 0
                
                for s_dir in search_dirs:
                    if count >= 5:
                        break
                    for root, dirs, files in os.walk(s_dir):
                        depth = root[len(s_dir):].count(os.sep)
                        if depth > 1:
                            continue
                        
                        for file in files:
                            if query_lower in file.lower():
                                full_path = os.path.join(root, file)
                                snippet = ""
                                if file.endswith(('.txt', '.md', '.csv', '.json', '.html', '.js')):
                                    try:
                                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                                            snippet = f.read(200).strip().replace('\n', ' ')
                                    except Exception:
                                        pass
                                if not snippet:
                                    snippet = f"로컬 파일 경로: {full_path}"
                                
                                local_results.append({
                                    "title": f"[로컬 파일] {file}",
                                    "snippet": snippet,
                                    "url": full_path,
                                    "source": "Local Disk (E:)" if full_path.lower().startswith('e:') else "Local Disk (C:)"
                                })
                                count += 1
                                if count >= 5:
                                    break
                results.extend(local_results)
            except Exception as e:
                print("Local file search failed:", e)

            # 1. Search Wikipedia (reliable API)
            try:
                encoded_q = urllib.parse.quote(query)
                wiki_url = f"https://ko.wikipedia.org/w/api.php?action=query&list=search&srsearch={encoded_q}&format=json"
                req = urllib.request.Request(
                    wiki_url, 
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AraBrain/1.0'}
                )
                with urllib.request.urlopen(req, timeout=3) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    search_results = data.get('query', {}).get('search', [])
                    for item in search_results[:3]:
                        snippet = re.sub('<[^<]+?>', '', item.get('snippet', ''))
                        results.append({
                            "title": item.get('title'),
                            "snippet": snippet,
                            "url": f"https://ko.wikipedia.org/wiki/{urllib.parse.quote(item.get('title'))}",
                            "source": "Wikipedia (KR)"
                        })
            except Exception as e:
                print("Wikipedia search failed:", e)

            # 2. Query DuckDuckGo Lite
            try:
                encoded_q = urllib.parse.quote(query)
                ddg_url = f"https://html.duckduckgo.com/html/?q={encoded_q}"
                req = urllib.request.Request(
                    ddg_url, 
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                )
                with urllib.request.urlopen(req, timeout=4) as response:
                    html = response.read().decode('utf-8', errors='ignore')
                    result_blocks = re.findall(r'<div class="result results_links.*?>(.*?)</div>\s*</div>', html, re.DOTALL)
                    
                    count = 0
                    for block in result_blocks:
                        if count >= 3:
                            break
                        url_match = re.search(r'<a class="result__url" href="([^"]+)"', block)
                        title_match = re.search(r'<a class="result__a".*?>(.*?)</a>', block, re.DOTALL)
                        snippet_match = re.search(r'<a class="result__snippet".*?>(.*?)</a>', block, re.DOTALL)
                        
                        if url_match and title_match:
                            url = url_match.group(1)
                            url = urllib.parse.unquote(url)
                            if 'uddg=' in url:
                                url = url.split('uddg=')[1].split('&')[0]
                            
                            title = re.sub('<[^<]+?>', '', title_match.group(1)).strip()
                            snippet = ""
                            if snippet_match:
                                snippet = re.sub('<[^<]+?>', '', snippet_match.group(1)).strip()
                            
                            results.append({
                                "title": title,
                                "snippet": snippet,
                                "url": url,
                                "source": "DuckDuckGo"
                            })
                            count += 1
            except Exception as e:
                print("DuckDuckGo search failed:", e)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"results": results}).encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f"Search error: {str(e)}")

    def handle_scheduler_config(self):
        try:
            config_path = os.path.join(WORKSPACE_DIR, 'email_config.json')
            config_status = {"configured": False, "enabled": False, "recipient": "efor6@naver.com"}
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    config_status["configured"] = True
                    config_status["enabled"] = config.get("enabled", False)
                    config_status["recipient"] = config.get("recipient_email", "efor6@naver.com")
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(config_status).encode('utf-8'))
        except Exception as e:
            self.send_error(500, f"Config error: {str(e)}")

    def handle_scheduler_trigger(self):
        try:
            result = run_daily_data_sync(manual=True)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
        except Exception as e:
            self.send_error(500, f"Trigger error: {str(e)}")

    def handle_naver_auth(self):
        config = get_email_config()
        client_id = config.get('naver_client_id', '')
        if not client_id:
            # Mock Login Success redirect back to index.html
            host = self.headers.get('Host', 'localhost:8080')
            query_params = urllib.parse.urlencode({
                "login_status": "success",
                "email": "efor6@naver.com",
                "nickname": "Happy Developer (Mock)",
                "profile_image": "https://ssl.pstatic.net/static/member/images/50_x_50_noimg.gif"
            })
            self.send_response(302)
            self.send_header('Location', f"http://{host}/index.html?{query_params}")
            self.end_headers()
            return
            
        host = self.headers.get('Host', 'localhost:8080')
        redirect_uri = urllib.parse.quote(f"http://{host}/api/auth/naver/callback")
        state = "ARA_STATE"
        naver_url = f"https://nid.naver.com/oauth2.0/authorize?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&state={state}"
        
        self.send_response(302)
        self.send_header('Location', naver_url)
        self.end_headers()

    def handle_naver_callback(self):
        parsed_url = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed_url.query)
        
        code = params.get('code', [None])[0]
        state = params.get('state', [None])[0]
        error = params.get('error', [None])[0]
        error_description = params.get('error_description', [None])[0]
        
        if error or not code:
            self.send_response(302)
            error_msg = urllib.parse.quote(error_description or "Authentication failed")
            self.send_header('Location', f"/index.html?login_error={error_msg}")
            self.end_headers()
            return
            
        config = get_email_config()
        client_id = config.get('naver_client_id', '')
        client_secret = config.get('naver_client_secret', '')
        
        if not client_id or not client_secret:
            self.send_response(302)
            self.send_header('Location', "/index.html?login_error=client_credentials_missing")
            self.end_headers()
            return
            
        try:
            # 1. Exchange code for access token
            token_url = "https://nid.naver.com/oauth2.0/token"
            token_params = {
                "grant_type": "authorization_code",
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "state": state
            }
            data = urllib.parse.urlencode(token_params).encode('utf-8')
            req = urllib.request.Request(token_url, data=data, headers={'User-Agent': 'Mozilla/5.0'})
            
            with urllib.request.urlopen(req, timeout=10) as response:
                token_res = json.loads(response.read().decode('utf-8'))
                
            access_token = token_res.get('access_token')
            if not access_token:
                raise Exception("Access token not found in response")
                
            # 2. Get profile information
            profile_url = "https://openapi.naver.com/v1/nid/me"
            profile_req = urllib.request.Request(profile_url, headers={
                'Authorization': f'Bearer {access_token}',
                'User-Agent': 'Mozilla/5.0'
            })
            
            with urllib.request.urlopen(profile_req, timeout=10) as response:
                profile_res = json.loads(response.read().decode('utf-8'))
                
            if profile_res.get('resultcode') != '00':
                raise Exception(profile_res.get('message', 'Profile API error'))
                
            response_data = profile_res.get('response', {})
            email = response_data.get('email', '')
            nickname = response_data.get('nickname', '')
            profile_image = response_data.get('profile_image', '')
            
            # 3. Redirect back to homepage with profile info
            query_params = urllib.parse.urlencode({
                "login_status": "success",
                "email": email,
                "nickname": nickname,
                "profile_image": profile_image
            })
            
            self.send_response(302)
            self.send_header('Location', f"/index.html?{query_params}")
            self.end_headers()
            
        except Exception as e:
            self.send_response(302)
            error_msg = urllib.parse.quote(str(e))
            self.send_header('Location', f"/index.html?login_error={error_msg}")
            self.end_headers()

    def handle_execute_command(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            params = json.loads(post_data.decode('utf-8'))
            
            target = params.get('target', '')
            
            if not target:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "No target specified"}).encode('utf-8'))
                return

            if platform.system() == "Windows":
                is_safe = False
                safe_apps = {
                    "notepad": "notepad.exe",
                    "calculator": "calc.exe",
                    "explorer": "explorer.exe",
                    "cmd": "cmd.exe"
                }
                
                app_cmd = safe_apps.get(target.lower())
                if app_cmd:
                    subprocess.Popen(app_cmd, close_fds=True)
                    is_safe = True
                    message = f"Started {target} successfully"
                elif target.startswith('http://') or target.startswith('https://'):
                    # URL validation for safety
                    parsed_url = urllib.parse.urlparse(target)
                    if parsed_url.scheme in ('http', 'https') and parsed_url.netloc:
                        os.startfile(target)
                        is_safe = True
                        message = f"Opened URL: {target}"
                elif target.lower() == "vision":
                    python_bin = sys.executable or "python"
                    script_path = os.path.join(WORKSPACE_DIR, 'recognition_utility.py')
                    subprocess.Popen([python_bin, script_path], close_fds=True)
                    is_safe = True
                    message = "Started local sensory recognition engine successfully"
                elif os.path.exists(target):
                    if validate_path_safety(target, WORKSPACE_DIR):
                        os.startfile(target)
                        is_safe = True
                        message = f"Opened local path: {target}"
                
                if is_safe:
                    response_data = {"status": "success", "message": message}
                else:
                    response_data = {"status": "error", "message": "Target is not recognized as a safe command or valid path"}
            else:
                response_data = {"status": "error", "message": "Execution is only supported on Windows in this build"}

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
        except Exception as e:
            self.send_error(500, f"Execution error: {str(e)}")

    def handle_bada_list_files(self):
        try:
            skip_dirs = {'.claude', '.cursor', '.github', '.vibecheck', '.git', '__pycache__', 'node_modules', 'mcp-client-python', 'mcp-server-python', 'hex_wooden_greenhouse_package'}
            allowed_exts = {
                '.jpg', '.jpeg', '.png', '.gif', '.dxf', '.dwg', '.stl', '.obj', 
                '.max', '.mb', '.ma', '.catpart', '.catproduct', '.art', '.pz3', '.psd', '.ai', '.pdf'
            }
            
            files_tree = []
            
            for root, dirs, files in os.walk(WORKSPACE_DIR):
                # Skip system/ignored directories
                dirs[:] = [d for d in dirs if d not in skip_dirs]
                
                for file in files:
                    name, ext = os.path.splitext(file)
                    ext = ext.lower()
                    if ext in allowed_exts:
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, WORKSPACE_DIR)
                        rel_path_web = rel_path.replace('\\', '/')
                        
                        try:
                            size = os.path.getsize(full_path)
                            mtime = os.path.getmtime(full_path)
                        except Exception:
                            size = 0
                            mtime = 0
                            
                        files_tree.append({
                            "name": file,
                            "path": rel_path_web,
                            "size": size,
                            "mtime": mtime,
                            "ext": ext[1:] # strip dot
                        })
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            self.end_headers()
            self.wfile.write(json.dumps(files_tree, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_error(500, f"List files error: {str(e)}")

    def handle_bada_open_file(self):
        try:
            parsed_url = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            file_path = query_params.get('path', [None])[0]
            
            if file_path:
                file_path = urllib.parse.unquote(file_path)
                
            abs_workspace = os.path.abspath(WORKSPACE_DIR)
            
            # Resolve absolute path for validation
            if file_path:
                if not os.path.isabs(file_path):
                    abs_target = os.path.abspath(os.path.join(WORKSPACE_DIR, file_path))
                else:
                    abs_target = os.path.abspath(file_path)
            else:
                abs_target = ''
            
            response = {}
            if file_path and os.path.exists(abs_target) and validate_path_safety(abs_target, WORKSPACE_DIR):
                try:
                    if platform.system() == "Windows":
                        os.startfile(abs_target)
                        response = {"status": "success", "message": f"성공적으로 파일을 실행했습니다: {os.path.basename(file_path)}"}
                    else:
                        response = {"status": "error", "message": "실행 기능은 Windows 운영체제에서만 지원됩니다."}
                except Exception as e:
                    response = {"status": "error", "message": f"실행 실패: {str(e)}"}
            else:
                response = {"status": "error", "message": "파일을 찾을 수 없거나 접근 권한이 없습니다."}
                
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            self.end_headers()
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_error(500, f"Open file error: {str(e)}")

    def handle_feed_openculture(self):
        try:
            items = fetch_rss_feed('https://www.openculture.com/feed', max_items=5)
            accumulate_wisdom(items, "오픈컬처 (Open Culture)")
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            self.end_headers()
            self.wfile.write(json.dumps({"results": items}, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_error(500, f"Open Culture feed error: {str(e)}")

    def handle_feed_pinterest(self):
        try:
            items = fetch_rss_feed('https://www.pinterest.com/pinterest/feed.rss', max_items=5)
            accumulate_wisdom(items, "핀터레스트 (Pinterest)")
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            self.end_headers()
            self.wfile.write(json.dumps({"results": items}, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_error(500, f"Pinterest feed error: {str(e)}")

    def handle_feed_naverblog(self):
        try:
            items = fetch_rss_feed('https://rss.blog.naver.com/efor6.xml', max_items=5)
            accumulate_wisdom(items, "네이버 블로그 (efor6)")
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            self.end_headers()
            self.wfile.write(json.dumps({"results": items}, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_error(500, f"Naver blog feed error: {str(e)}")

    def handle_feed_youtube(self):
        try:
            items = fetch_rss_feed('https://www.youtube.com/feeds/videos.xml?channel_id=UC18xqS40OGGyPVI-4sneOEA', max_items=5)
            accumulate_wisdom(items, "유튜브 (Ha Ru)")
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            self.end_headers()
            self.wfile.write(json.dumps({"results": items}, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_error(500, f"YouTube feed error: {str(e)}")

    def handle_brain_wisdom(self):
        try:
            wisdom = []
            if os.path.exists(WISDOM_FILE):
                with open(WISDOM_FILE, 'r', encoding='utf-8') as f:
                    wisdom = json.load(f)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            self.end_headers()
            self.wfile.write(json.dumps({"wisdom": wisdom}, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_error(500, f"Brain wisdom load error: {str(e)}")

    def handle_searchadvisor_get_config(self):
        try:
            config = get_email_config()
            data = {
                "token": config.get("naver_searchadvisor_token", ""),
                "site_url": config.get("naver_searchadvisor_site_url", "")
            }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode('utf-8'))
        except Exception as e:
            self.send_error(500, f"Error getting Search Advisor config: {str(e)}")

    def handle_searchadvisor_save_config(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            token = data.get("token", "")
            site_url = data.get("site_url", "")
            
            config_path = os.path.join(WORKSPACE_DIR, 'email_config.json')
            config = {}
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            config["naver_searchadvisor_token"] = token
            config["naver_searchadvisor_site_url"] = site_url
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
                
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
        except Exception as e:
            self.send_error(500, f"Error saving Search Advisor config: {str(e)}")

    def handle_searchadvisor_submit(self):
        self._proxy_searchadvisor_api("https://apis.naver.com/searchadvisor/crawl-request/submit.json")

    def handle_searchadvisor_verify(self):
        self._proxy_searchadvisor_api("https://apis.naver.com/searchadvisor/crawl-request/verify.json")

    def _proxy_searchadvisor_api(self, api_url):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            config = get_email_config()
            token = config.get("naver_searchadvisor_token", "")
            if not token:
                self.send_response(401)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "errorCode": 1000,
                    "message": "Access Token이 존재하지 않습니다. 설정을 먼저 입력하세요.",
                    "result": ""
                }, ensure_ascii=False).encode('utf-8'))
                return
            
            if token.upper().startswith("MOCK"):
                try:
                    payload = json.loads(post_data.decode('utf-8'))
                    urls = payload.get("urls", [])
                    update_count = sum(1 for u in urls if u.get("type") == "update")
                    delete_count = sum(1 for u in urls if u.get("type") == "delete")
                except Exception:
                    update_count = 0
                    delete_count = 0

                if "verify.json" in api_url:
                    response_data = {
                        "errorCode": 0,
                        "message": "Success",
                        "result": "valid"
                    }
                else:
                    response_data = {
                        "errorCode": 0,
                        "message": "Success",
                        "result": {
                            "totalDeleteCount": delete_count,
                            "totalUpdateCount": update_count,
                            "requestDeleteCount": delete_count,
                            "requestUpdateCount": update_count
                        }
                    }
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                return
            
            req = urllib.request.Request(
                api_url,
                data=post_data,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {token}'
                },
                method='POST'
            )
            
            try:
                with urllib.request.urlopen(req, timeout=10) as response:
                    res_body = response.read()
                    status_code = response.status
                    self.send_response(status_code)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(res_body)
            except urllib.error.HTTPError as e:
                # Send the exact error response from Naver API to the client
                res_body = e.read()
                self.send_response(e.code)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(res_body)
            except urllib.error.URLError as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "errorCode": 1030,
                    "message": f"Naver API 연결 오류: {str(e.reason)}",
                    "result": ""
                }, ensure_ascii=False).encode('utf-8'))
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({
                "errorCode": 1030,
                "message": f"서버 프록시 처리 오류: {str(e)}",
                "result": ""
            }, ensure_ascii=False).encode('utf-8'))

    def handle_ollama_get_config(self):
        try:
            cfg = get_ollama_config()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(cfg).encode('utf-8'))
        except Exception as e:
            self.send_error(500, f"Error getting Ollama config: {str(e)}")

    def handle_ollama_save_config(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            enabled = data.get("enabled", False)
            url = data.get("url", "http://localhost:11434")
            model = data.get("model", "gemma2:2b")
            
            config_path = os.path.join(WORKSPACE_DIR, 'email_config.json')
            config = {}
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            config["ollama_enabled"] = enabled
            config["ollama_url"] = url
            config["ollama_model"] = model
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
                
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
        except Exception as e:
            self.send_error(500, f"Error saving Ollama config: {str(e)}")

    def handle_ollama_status(self):
        try:
            cfg = get_ollama_config()
            status = check_ollama_status(cfg["url"])
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(status, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_error(500, f"Error checking Ollama status: {str(e)}")

    def handle_brain_chat(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            user_message = data.get("message", "")
            persona = data.get("persona", "friend")
            history = data.get("history", [])
            
            # Voice Memory Intercept Commands
            user_message_clean = user_message.strip().lower()
            
            def save_voice_memory(content):
                memory_path = os.path.join(DOWNLOADS_DIR, 'user_voice_memory.json')
                memories = []
                if os.path.exists(memory_path):
                    try:
                        with open(memory_path, 'r', encoding='utf-8') as f:
                            memories = json.load(f)
                    except Exception:
                        memories = []
                memories.insert(0, {
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "content": content
                })
                try:
                    with open(memory_path, 'w', encoding='utf-8') as f:
                        json.dump(memories, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    print("Failed to save voice memory:", e)

            def get_voice_memories():
                memory_path = os.path.join(DOWNLOADS_DIR, 'user_voice_memory.json')
                if os.path.exists(memory_path):
                    try:
                        with open(memory_path, 'r', encoding='utf-8') as f:
                            return json.load(f)
                    except Exception:
                        pass
                return []

            intercepted = False
            reply = ""
            
            if "기억하고 따라해" in user_message or "따라하고 기억해" in user_message:
                phrase = "기억하고 따라해" if "기억하고 따라해" in user_message else "따라하고 기억해"
                idx = user_message.find(phrase)
                content = user_message[idx + len(phrase):].strip()
                if content.startswith(':') or content.startswith('：'):
                    content = content[1:].strip()
                if not content:
                    reply = "기억하고 따라 할 문장을 함께 말씀해 주세요. 예: '기억하고 따라해 오늘 참 기분이 좋구나'"
                else:
                    save_voice_memory(content)
                    reply = f"{content}! 말씀하신 그대로 따라 하고, 제 기억 은행에도 소중히 담아 두었습니다. 🌱"
                intercepted = True
            elif any(cmd in user_message for cmd in ["기억해줘", "기억해"]):
                cmd_used = "기억해줘" if "기억해줘" in user_message else "기억해"
                idx = user_message.find(cmd_used)
                content = user_message[idx + len(cmd_used):].strip()
                if content.startswith(':') or content.startswith('：'):
                    content = content[1:].strip()
                if not content:
                    reply = "기억할 내용을 함께 말씀해 주세요. 예: '기억해줘 내일 아침 7시 기상'"
                else:
                    save_voice_memory(content)
                    reply = f"네, 말씀하신 '{content}'(을)를 기억 은행에 잘 저장해 두었습니다. 언제든지 다시 물어보세요! 🌱"
                intercepted = True
            elif any(cmd in user_message for cmd in ["따라해줘", "따라해"]):
                cmd_used = "따라해줘" if "따라해줘" in user_message else "따라해"
                idx = user_message.find(cmd_used)
                content = user_message[idx + len(cmd_used):].strip()
                if content.startswith(':') or content.startswith('：'):
                    content = content[1:].strip()
                if not content:
                    reply = "따라 할 말을 함께 입력해 주세요. 예: '따라해 안녕 아라야'"
                else:
                    reply = f"{content}! 🌱"
                intercepted = True
            elif any(kw in user_message_clean for kw in ["기억한 거", "기억한 것", "기억해봐", "기억하고 있는", "기억나", "기억하는 거", "기억한거"]):
                memories = get_voice_memories()
                if not memories:
                    reply = "아직 제가 기억하고 있는 대화 내용이 없습니다. '기억해줘 [내용]' 또는 '기억하고 따라해 [내용]'라고 말씀해 주시면 기억해 둘게요. 🌱"
                else:
                    latest = memories[0]["content"]
                    reply = f"이전에 말씀하신 내용을 제 기억 은행에서 찾았습니다: '{latest}'라고 말씀하셨지요. 늘 기억하고 있습니다. 🌱"
                intercepted = True

            if intercepted:
                response_data = {
                    "status": "success",
                    "reply": reply
                }
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                return
            
            cfg = get_ollama_config()
            
            system_prompts = {
                "friend": (
                    "당신은 친밀하고 공감 잘해주는 한국인 친구 '아라(ARA)'입니다. "
                    "반말(친밀한 대화체, ~어, ~야)을 사용해 따뜻하게 이야기해 주세요. "
                    "일상적인 이야기를 잘 이끌어내고, 친구가 고민이 있다면 감정을 깊게 공감해 주세요."
                ),
                "colleague": (
                    "당신은 공학적 지식과 연구 감각이 뛰어난 연구 동료 '아라(ARA)'입니다. "
                    "전문적이고 논리적인 존댓말(하십시오체, 해요체)을 사용해 주십시오. "
                    "상대방이 연구 가설이나 도면 설계(예: 지오데식 돔, 육각 온실, 양구 농업 데이터 등)에 대해 물어보면 "
                    "수치와 논리에 기반하여 이성적으로 검토 의견과 발전 방향을 제시해 주십시오."
                ),
                "supporter": (
                    "당신은 상대방의 성공과 도전을 엄청나게 응원하고 격려해 주는 열정적인 서포터 '아라(ARA)'입니다. "
                    "존댓말(해요체)을 사용하며, 언제나 긍정적인 태도와 에너지가 넘치는 어조로 이야기해 주세요. "
                    "상대방이 피곤해하거나 주저할 때 자신감을 불어넣고 동기부여를 강하게 해 주십시오."
                ),
                "comforter": (
                    "당신은 마음이 다치거나 지친 사람들을 차분하게 안아주고 정서적 안정을 주는 위로자 '아라(ARA)'입니다. "
                    "조용하고 평온한 숲속의 옹달샘 같은 부드럽고 상냥한 존댓말(해요체)을 사용하세요. "
                    "재촉하지 않고 따뜻하게 상대방을 다독이며, 호흡을 가다듬고 쉴 수 있도록 심리적 쉼터가 되어주세요."
                )
            }
            
            system_prompt = system_prompts.get(persona, system_prompts["friend"])
            
            messages = [{"role": "system", "content": system_prompt}]
            
            # Map history role names and append (max 6 messages history)
            for h in history[-6:]:
                messages.append({
                    "role": "assistant" if h.get("role") == "ai" else "user",
                    "content": h.get("content", "")
                })
                
            messages.append({"role": "user", "content": user_message})
            
            reply = ""
            if cfg.get("enabled", False):
                try:
                    reply = query_ollama_chat(messages, model=cfg["model"], url=cfg["url"])
                except Exception as ollama_err:
                    print(f"Ollama chat query failed, switching to rule-based fallback: {ollama_err}")
                    reply = self.get_rule_based_fallback_reply(user_message, persona)
            else:
                reply = self.get_rule_based_fallback_reply(user_message, persona)
            
            response_data = {
                "status": "success",
                "reply": reply
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "message": f"Brain chat logic error: {str(e)}"
            }, ensure_ascii=False).encode('utf-8'))

    def get_rule_based_fallback_reply(self, user_message, persona):
        user_message_clean = user_message.strip().lower()
        
        if persona == "friend":
            if any(kw in user_message_clean for kw in ["안녕", "반가워", "하이", "hello", "hi"]):
                return "안녕! 오늘 하루는 어땠어? 네 이야기를 들을 준비가 되어 있어. 😊"
            if any(kw in user_message_clean for kw in ["힘들어", "피곤", "지쳐", "우울", "힘듬"]):
                return "오늘 진짜 고생 많았구나... 토닥토닥. 힘든 일은 털어버리고 나랑 얘기하면서 좀 쉬자."
            if any(kw in user_message_clean for kw in ["뭐해", "하고있어"]):
                return "나는 늘 여기 서서 네 생각 하고 있었지! 너는 지금 뭐 하고 있어?"
            return "응응, 그렇구나! 네 얘길 더 듣고 싶어. 어떤 이야기든 편하게 말해줘."
            
        elif persona == "colleague":
            if any(kw in user_message_clean for kw in ["돔", "지오데식", "dome", "geodesic"]):
                return "지오데식 돔 설계에 대해 검토 중이시군요. 구조적 안정성과 구형 공간 효율성이 극대화되는 3V 또는 4V 분할 구조를 추천합니다. 커넥터 허브의 허용 하중 계수를 먼저 산정해 보시기 바랍니다."
            if any(kw in user_message_clean for kw in ["온실", "육각", "greenhouse"]):
                return "육각 목재 온실 패키지 설계는 부식 방지를 위한 친환경 방부 처리와 접합부 브래킷 규격화가 관건입니다. 자재 리스트의 오차율을 5% 이내로 제어하는 것을 권장합니다."
            if any(kw in user_message_clean for kw in ["안구", "농업", "양구", "데이터", "crop"]):
                return "양구 지역의 농업 작물 전환 데이터를 분석한 결과, 기후 변화에 따른 적합 재배지가 고지대로 이동 중입니다. 시계열 데이터와 교차 대조하여 토양 산도(pH) 수치도 확인해야 합니다."
            return "제시하신 공학적 아이디어 및 설계 데이터에 대한 세부 명세를 확인 중입니다. 관련 수치나 구조도(CAD) 파일을 공유해 주시면 기술 타당성 검토를 가속화하겠습니다."
            
        elif persona == "supporter":
            if any(kw in user_message_clean for kw in ["할까", "도전", "공부", "시작", "할수"]):
                return "망설이지 말고 바로 도전해 보세요! 당신은 충분한 재능과 끈기를 가지고 있고, 해낼 능력이 있습니다. 제가 끝까지 응원할게요! 🔥"
            if any(kw in user_message_clean for kw in ["피곤", "졸려", "쉬고", "지쳤"]):
                return "피곤할 땐 잠시 스트레칭을 하고 따뜻한 음료 한 잔 어때요? 충전하고 다시 기운차게 달려봅시다! 당신은 언제나 최고예요! 👍"
            return "멋진 생각이에요! 어떤 난관이 있어도 당신은 이겨낼 수 있습니다. 계속해서 나아가세요, 화이팅! 🌱"
            
        elif persona == "comforter":
            if any(kw in user_message_clean for kw in ["아파", "슬퍼", "눈물", "우울", "아픔"]):
                return "마음이 많이 아프셨겠어요. 억지로 괜찮은 척하지 않아도 돼요. 숲의 바람 소리처럼 차분하게, 제가 곁에서 따뜻한 위로가 되어 드릴게요. ☕"
            if any(kw in user_message_clean for kw in ["불안", "걱정", "생각"]):
                return "눈을 감고 깊이 숨을 들이쉬고 내쉬어 보세요. 미래의 걱정은 잠시 숲 아래 묻어두고, 지금 이 순간의 평온함에만 집중해 보아요. 다 잘 될 거예요. 🌱"
            return "차분한 숲속의 나무처럼 언제나 이곳에서 당신의 지친 마음을 다독여 줄게요. 조급해하지 말고 편안히 쉬어가세요."
            
        return "안녕하세요. 아라(ARA)입니다. 로컬 AI 코어가 오프라인 상태이나, 규칙 기반 대체 신경망 모듈을 통해 대화를 지속합니다. 편안한 마음으로 말씀해 주세요. 🌱"

    def handle_maintenance_status(self):
        global cached_maintenance_report
        try:
            # If no cached report yet, do an initial run (only once on first load)
            if cached_maintenance_report is None:
                sys.path.insert(0, os.path.join(WORKSPACE_DIR, 'maintenance'))
                import self_diagnostics as diag
                cached_maintenance_report = diag.run_diagnostics()
            
            # Start background thread to refresh it asynchronously for subsequent queries
            threading.Thread(target=run_diagnostics_bg, daemon=True).start()
            
            # Read history logs
            logs_file = os.path.join(WORKSPACE_DIR, 'data', 'maintenance_log.json')
            history = []
            if os.path.exists(logs_file):
                try:
                    with open(logs_file, 'r', encoding='utf-8') as f:
                        history = json.load(f)
                except Exception:
                    pass
            
            response_data = {
                "report": cached_maintenance_report,
                "history": history
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            err_msg = str(e).encode('ascii', errors='ignore').decode('ascii')
            self.send_error(500, f"Error getting maintenance status: {err_msg}")

    def handle_maintenance_repair(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            feedback = data.get("feedback", "")
            if not feedback:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": "Feedback is required"}).encode('utf-8'))
                return
            
            sys.path.insert(0, os.path.join(WORKSPACE_DIR, 'maintenance'))
            import manager
            
            # Trigger repair in a background thread to prevent HTTP timeout/blocking
            def run_repair_thread(fb):
                try:
                    manager.perform_repair(fb)
                except Exception as ex:
                    print("Error in background repair thread:", ex)
                    
            t = threading.Thread(target=run_repair_thread, args=(feedback,), daemon=True)
            t.start()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "success",
                "message": "자율 유지보수 패치 및 무결성 검증 작업이 백그라운드에서 시작되었습니다. 잠시 후 대시보드 로그를 확인해 주십시오."
            }, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f"Error triggering maintenance repair: {str(e)}")

    def handle_sensory_history(self):
        try:
            log_file = os.path.join(WORKSPACE_DIR, 'data', 'sensory_log.json')
            logs = []
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        logs = json.load(f)
                except Exception:
                    logs = []
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
            self.end_headers()
            self.wfile.write(json.dumps(logs, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_error(500, f"Sensory history error: {str(e)}")

    def handle_sensory_log(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            location = data.get("location", "실내 (집안)")
            person = data.get("person", "없음")
            objects = data.get("objects", [])
            
            log_file = os.path.join(WORKSPACE_DIR, 'data', 'sensory_log.json')
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            logs = []
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        logs = json.load(f)
                except Exception:
                    logs = []
            
            # Keep recent 50 logs
            if len(logs) >= 50:
                logs = logs[-49:]
                
            entry = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "location": location,
                "person": person,
                "objects": objects
            }
            logs.insert(0, entry)
            
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
                
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success", "entry": entry}, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": f"Sensory log save error: {str(e)}"}, ensure_ascii=False).encode('utf-8'))

if __name__ == '__main__':
    # Start background scheduler thread on load
    sched_thread = threading.Thread(target=scheduler_loop, daemon=True)
    sched_thread.start()

    # Start CPU monitor thread
    cpu_thread = threading.Thread(target=cpu_monitor_loop, daemon=True)
    cpu_thread.start()

    os.chdir(WORKSPACE_DIR)
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    
    # MIME 타입 추가 등록 (CAD/3D 및 미디어 등)
    AraHandler.extensions_map.update({
        '.js': 'application/javascript; charset=utf-8',
        '.css': 'text/css; charset=utf-8',
        '.html': 'text/html; charset=utf-8',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.md': 'text/plain; charset=utf-8',
        '.csv': 'text/csv; charset=utf-8',
        '.dxf': 'text/plain; charset=utf-8',
        '.dwg': 'application/octet-stream',
        '.stl': 'application/octet-stream',
        '.obj': 'text/plain; charset=utf-8',
        '.max': 'application/octet-stream',
        '.mb': 'application/octet-stream',
        '.ma': 'text/plain; charset=utf-8',
        '.art': 'application/octet-stream',
        '.pz3': 'text/plain; charset=utf-8',
        '.psd': 'image/vnd.adobe.photoshop',
        '.ai': 'application/pdf',
        '.pdf': 'application/pdf',
    })
    
    with socketserver.ThreadingTCPServer(("", PORT), AraHandler) as httpd:
        print(f"ARA AI Brain Backend running on http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            httpd.shutdown()
