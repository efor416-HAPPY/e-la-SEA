# -*- coding: utf-8 -*-
"""
아라의 동영상 인지망 (Ara's Cognitive Video Network) 리소스 처리 및 전송기
e:/la/sea/data/ 또는 워크스페이스 내의 e:/SEA/data/ 경로의 모든 동영상 파일들을 탐색하고,
내부 메타데이터(해상도, FPS, 프레임 수 등)를 추출하여 아라의 지혜 저장소(accumulated_wisdom.json)에 주입합니다.
"""
import os
import json
import time
import sys
import io
from pathlib import Path

# Force stdout/stderr to use UTF-8 encoding to prevent CP949 encoding crashes on Windows consoles
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

try:
    import cv2  # 영상 프레임 및 메타데이터 추출용 (pip install opencv-python)
except ImportError:
    cv2 = None

class ArasCognitiveVideoNetwork:
    """
    아라의 동영상 인지망 (Ara's Cognitive Video Network) 리소스 처리 및 전송기
    """
    def __init__(self, target_dir="e:/la/sea/data/", max_retries=5, retry_delay=3):
        primary_dir = Path(target_dir)
        workspace_dir = Path(__file__).parent.absolute()
        
        # 기본 경로가 존재하지 않는 경우 워크스페이스 내의 data/ 폴더를 예비 경로로 지정
        if not primary_dir.exists():
            fallback_dir = workspace_dir / "data"
            print(f"⚠️ 기본 경로가 존재하지 않아 예비 경로를 사용합니다: {fallback_dir}")
            self.target_dir = fallback_dir
        else:
            self.target_dir = primary_dir
            
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.supported_formats = ['.mp4', '.avi', '.mkv', '.mov', '.wmv']
        self.wisdom_file_path = workspace_dir / "downloads" / "accumulated_wisdom.json"

    def _connect_synapse(self, data_payload):
        """
        [핵심 연결망] 추출된 비디오 데이터를 실제 아라의 신경망(DB/JSON 지혜 저장소)으로 이식합니다.
        네트워크나 파일 불안정에 대비해 max_retries 만큼 재시도합니다.
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                wisdom = []
                if self.wisdom_file_path.exists():
                    try:
                        with open(self.wisdom_file_path, "r", encoding="utf-8") as f:
                            wisdom = json.load(f)
                    except Exception as e:
                        print(f"⚠️ 지혜 저장소를 읽는 중 오류 발생: {e}")

                file_name = data_payload.get("file_name")
                file_link = f"local-video://{file_name}"
                existing_links = {item.get('link') for item in wisdom if item.get('link')}

                if file_link not in existing_links:
                    now_str = time.strftime('%Y-%m-%d %H:%M:%S')
                    description_text = (
                        f"해상도: {data_payload.get('resolution')} | "
                        f"길이: {data_payload.get('duration')} | "
                        f"FPS: {data_payload.get('fps')} | "
                        f"총 프레임: {data_payload.get('total_frames')}"
                    )
                    
                    wisdom.append({
                        "title": f"동영상: {file_name}",
                        "link": file_link,
                        "description": description_text,
                        "source": "아라의 동영상 인지망 (Video)",
                        "scraped_at": now_str
                    })
                    # 최신 정보가 앞으로 오도록 정렬
                    wisdom.sort(key=lambda x: x.get('scraped_at', ''), reverse=True)
                    
                    self.wisdom_file_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(self.wisdom_file_path, "w", encoding="utf-8") as f:
                        json.dump(wisdom, f, ensure_ascii=False, indent=2)
                
                return True, "시냅스 지식 연동 및 지혜 저장소 이식 완료"

            except Exception as e:
                print(f"   ⚠️ [시냅스 연결 불안정] 시도 {attempt}/{self.max_retries} - 오류: {e}")
                if attempt < self.max_retries:
                    print(f"   ⏳ {self.retry_delay}초 후 우회 경로로 재연결을 시도합니다...")
                    time.sleep(self.retry_delay)
                else:
                    return False, f"시냅스 연결 최종 실패 (신경망 단절: {str(e)})"

    def extract_and_transplant(self, file_path):
        """
        동영상 파일의 형태(메타데이터)를 인지하고 신경망으로 전송합니다.
        """
        print(f"\n👁️ [시각 인지망 활성화] '{file_path.name}' 분석 개시...")
        
        if not cv2:
            return {"status": "error", "file_name": file_path.name, "message": "OpenCV 라이브러리가 설치되지 않았습니다."}

        try:
            # 1. 동영상 파일 열기 (인지 시작)
            video = cv2.VideoCapture(str(file_path))
            if not video.isOpened():
                raise ValueError("동영상 파일을 읽을 수 없습니다. 코덱 문제이거나 파일이 손상되었습니다.")

            # 2. 메타데이터 추출 (형태 파악)
            fps = video.get(cv2.CAP_PROP_FPS)
            frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration_sec = frame_count / fps if fps > 0 else 0
            
            video.release() # 파일 잠금 해제

            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

            # 3. 신경망으로 보낼 데이터 패키징
            cognitive_data = {
                "file_name": file_path.name,
                "file_size": f"{file_size_mb:.2f} MB",
                "resolution": f"{width}x{height}",
                "fps": round(fps, 2),
                "duration": f"{duration_sec:.2f}초",
                "total_frames": frame_count
            }

            # 4. 재시도 로직이 포함된 시냅스 전송 실행
            success, msg = self._connect_synapse(cognitive_data)

            if success:
                return {"status": "success", "data": cognitive_data, "message": msg}
            else:
                return {"status": "error", "file_name": file_path.name, "message": msg}

        except Exception as e:
            return {"status": "error", "file_name": file_path.name, "message": f"인지 처리 중 오류: {str(e)}"}

    def run_pipeline(self):
        """
        지정된 디렉토리의 모든 동영상을 수집하고 인지망 파이프라인을 구동합니다.
        """
        print("==================================================")
        print(f"🎬 [동영상 리소스 스캔] 탐색 경로: {self.target_dir}")
        print("==================================================")
        
        if not self.target_dir.exists():
            try:
                self.target_dir.mkdir(parents=True, exist_ok=True)
                print(f"📁 새 폴더를 생성했습니다: {self.target_dir}")
            except Exception as e:
                print(f"❌ 에러: 폴더를 생성할 수 없습니다: {e}")
                return

        # 지원하는 확장자를 가진 파일만 모두 수집 (대소문자 무시)
        video_files = []
        for ext in self.supported_formats:
            video_files.extend(self.target_dir.glob(f"*{ext}"))
            video_files.extend(self.target_dir.glob(f"*{ext.upper()}"))
            
        video_files = sorted(list(set(video_files)))
        total_count = len(video_files)
        
        print(f"📊 총 {total_count}개의 시각 리소스(동영상)를 발견했습니다.\n")
        
        if total_count == 0:
            print("ℹ️ 처리할 파일이 없습니다. e:/la/sea/data/ 또는 워크스페이스 내의 data/ 폴더에 동영상 파일을 넣어 주세요.")
            return

        success_count = 0
        
        for index, file_path in enumerate(video_files, 1):
            print(f"▶ [{index}/{total_count}] 데이터 주입 중...")
            
            result = self.extract_and_transplant(file_path)
            
            if result["status"] == "success":
                data = result["data"]
                print(f"✅ 이식 완료: {data['file_name']}")
                print(f"   - 해상도: {data['resolution']} | 길이: {data['duration']} | 크기: {data['file_size']}")
                success_count += 1
            else:
                print(f"❌ 이식 실패: {result['file_name']} - {result['message']}")
            
            print("-" * 50)
            
        print(f"\n🏁 [전체 시각 인지망 가동 종료]")
        print(f"📈 총 {total_count}개 중 {success_count}개의 동영상이 아라의 인지망으로 완벽히 연결되었습니다.")

if __name__ == "__main__":
    TARGET_PATH = "e:/la/sea/data/"
    cognitive_network = ArasCognitiveVideoNetwork(target_dir=TARGET_PATH, max_retries=5, retry_delay=3)
    cognitive_network.run_pipeline()
