# -*- coding: utf-8 -*-
"""
Naver Search Advisor Crawl Request API Library (Python)
This module provides both a simple function and a class-based client with retry logic.
"""
import requests
import json
import time

def request_naver_crawl(access_token, target_url):
    """
    Simple function to send a crawl request to Naver Search Advisor API.
    - access_token: Bearer Access Token from Naver Search Advisor settings
    - target_url: Target URL to crawl
    """
    api_url = 'https://apis.naver.com/searchadvisor/crawl-request/submit.json'
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    
    payload = {
        "urls": [
            {
                "url": target_url,
                "type": "update"  # crawl request: update, delete request: delete
            }
        ]
    }
    
    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(payload), timeout=10)
        
        if response.status_code == 200:
            print("✅ 수집 요청 성공:", response.json())
            return True
        else:
            print(f"❌ API 에러 발생 (상태 코드: {response.status_code})")
            print("에러 상세 내용:", response.text)
            return False
            
    except Exception as e:
        print("❌ 네트워크 또는 코드 실행 에러:", e)
        return False


class NaverSearchAdvisor:
    """
    Custom Class Library for Naver Search Advisor API with automatic retries and delay.
    """
    def __init__(self, access_token, max_retries=3, delay_seconds=2):
        self.access_token = access_token
        self.max_retries = max_retries
        self.delay = delay_seconds
        self.api_url = 'https://apis.naver.com/searchadvisor/crawl-request/submit.json'
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        }

    def request_crawl(self, target_url, request_type="update"):
        """
        Sends crawl request and retries on failure up to max_retries.
        - target_url: Target URL to register
        - request_type: "update" (crawl), "delete" (deindex)
        """
        payload = {
            "urls": [
                {
                    "url": target_url,
                    "type": request_type
                }
            ]
        }
        
        print(f"🚀 '{target_url}'에 대한 {request_type} 요청을 시작합니다.")
        
        for attempt in range(1, self.max_retries + 1):
            try:
                print(f"▶ [시도 {attempt}/{self.max_retries}] API 연결 중...")
                response = requests.post(self.api_url, headers=self.headers, data=json.dumps(payload), timeout=10)
                
                if response.status_code == 200:
                    print("✅ 요청 성공! 네이버가 URL을 정상적으로 접수했습니다.")
                    print("응답 데이터:", response.json())
                    return True
                else:
                    print(f"⚠️ API 응답 에러 (상태 코드: {response.status_code})")
                    print("에러 상세:", response.text)
            
            except requests.exceptions.RequestException as e:
                print(f"❌ 네트워크 오류 또는 연결 실패: {e}")
            
            if attempt < self.max_retries:
                print(f"⏳ {self.delay}초 대기 후 다시 연결을 시도합니다...\n")
                time.sleep(self.delay)
        
        print("🚨 최대 재시도 횟수를 초과했습니다. 나중에 다시 시도해 주세요.")
        return False


# ==========================================
# 💡 라이브러리 사용 예시 (주관적 작동 테스트)
# ==========================================
if __name__ == "__main__":
    # 서치어드바이저 도구 설정에서 발급받은 실제 토큰으로 변경하세요.
    ACCESS_TOKEN = "여기에_발급받은_액세스_토큰을_입력하세요" 

    # 수집을 요청할 웹사이트의 실제 페이지 URL로 변경하세요.
    TARGET_URL = "https://www.your-site.com/new-post" 

    print("--- 1. Simple Function Test ---")
    request_naver_crawl(ACCESS_TOKEN, TARGET_URL)

    print("\n--- 2. Custom Library Class Test ---")
    advisor_bot = NaverSearchAdvisor(access_token=ACCESS_TOKEN, max_retries=5, delay_seconds=3)
    advisor_bot.request_crawl(TARGET_URL)
