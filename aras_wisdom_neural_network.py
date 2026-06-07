# -*- coding: utf-8 -*-
"""
아라의 지혜의 신경망 (Ara's Wisdom Neural Network) 리소스 처리기
e:/la/sea/pdf/ 또는 워크스페이스 내의 e:/SEA/pdf/ 경로의 모든 PDF 파일들을 안전하게 탐색하고,
내용을 추출하여 아라의 지혜 저장소(accumulated_wisdom.json)에 자동으로 주입합니다.
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
    import pypdf  # PDF 텍스트 추출용 라이브러리
except ImportError:
    pypdf = None

class ArasWisdomNeuralNetwork:
    """
    아라의 지혜의 신경망 (Ara's Wisdom Neural Network) 리소스 처리기
    """
    def __init__(self, target_dir="e:/la/sea/pdf/"):
        # 대상 디렉토리를 Path 객체로 설정
        primary_dir = Path(target_dir)
        workspace_dir = Path(__file__).parent.absolute()
        
        # E:/la/sea/pdf/ 경로가 존재하지 않는 경우 워크스페이스 내의 pdf/ 폴더를 예비 경로로 지정
        if not primary_dir.exists():
            fallback_dir = workspace_dir / "pdf"
            print(f"⚠️ 기본 경로가 존재하지 않아 예비 경로를 사용합니다: {fallback_dir}")
            self.target_dir = fallback_dir
        else:
            self.target_dir = primary_dir

        self.wisdom_file_path = workspace_dir / "downloads" / "accumulated_wisdom.json"

    def save_to_wisdom_store(self, file_name, text_preview):
        """
        추출된 PDF 텍스트 요약을 아라의 실제 지혜 저장소(accumulated_wisdom.json)에 저장하여
        웹 대시보드에 노출될 수 있도록 연동합니다.
        """
        wisdom = []
        if self.wisdom_file_path.exists():
            try:
                with open(self.wisdom_file_path, "r", encoding="utf-8") as f:
                    wisdom = json.load(f)
            except Exception as e:
                print(f"⚠️ 지혜 저장소 파일을 읽는 중 오류 발생: {e}")

        # 중복 링크 체크 (파일명 기반으로 가상 링크 형성)
        file_link = f"local-pdf://{file_name}"
        existing_links = {item.get('link') for item in wisdom if item.get('link')}

        if file_link not in existing_links:
            now_str = time.strftime('%Y-%m-%d %H:%M:%S')
            wisdom.append({
                "title": f"PDF: {file_name}",
                "link": file_link,
                "description": text_preview,
                "source": "아라의 지혜의 신경망 (PDF)",
                "scraped_at": now_str
            })
            # 최신 정보가 앞으로 오도록 정렬
            wisdom.sort(key=lambda x: x.get('scraped_at', ''), reverse=True)
            
            try:
                self.wisdom_file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.wisdom_file_path, "w", encoding="utf-8") as f:
                    json.dump(wisdom, f, ensure_ascii=False, indent=2)
                print(f"💾 [저장 완료] '{file_name}' 지혜 저장소에 누적 등록되었습니다.")
                return True
            except Exception as e:
                print(f"❌ 지혜 저장소 파일 저장 오류: {e}")
        else:
            print(f"ℹ️ [건너뜀] '{file_name}'은 이미 지혜 저장소에 등록되어 있습니다.")
        return False

    def extract_and_analyze(self, file_path):
        """
        각 PDF 파일을 읽고 분석하여 신경망 리소스로 변환합니다.
        """
        print(f"🧠 [지혜의 신경망] -> '{file_path.name}' 리소스 분석 개시...")
        
        try:
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            extracted_text = ""
            
            # pypdf 라이브러리가 있을 경우 텍스트를 추출
            if pypdf:
                with open(file_path, "rb") as f:
                    reader = pypdf.PdfReader(f)
                    # 앞쪽 3페이지만 샘플링
                    for page in reader.pages[:3]:
                        text = page.extract_text()
                        if text:
                            extracted_text += text + "\n"
            else:
                extracted_text = "[pypdf 미설치] 파일 메타데이터 정보만 추출되었습니다."

            # 비어있는 텍스트 방지
            preview = extracted_text[:100].replace("\n", " ").strip()
            if not preview or preview == "[pypdf 미설치]":
                preview = f"PDF Document metadata extracted successfully. Size: {file_size_mb:.2f} MB"
            else:
                preview = preview + "..."

            # 아라의 실제 지혜 저장소 DB/JSON 파일과 동기화
            self.save_to_wisdom_store(file_path.name, preview)
            
            return {
                "status": "success",
                "file_name": file_path.name,
                "file_size": f"{file_size_mb:.2f} MB",
                "text_preview": preview,
                "message": "신경망 지식 리소스 등록 완료"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "file_name": file_path.name,
                "message": f"파일 처리 중 오류 발생: {str(e)}"
            }

    def run_pipeline(self):
        """
        지정된 디렉토리의 모든 PDF를 수집하고 파이프라인을 구동합니다.
        """
        print("==================================================")
        print(f"📂 [디렉토리 스캔] 탐색 경로: {self.target_dir}")
        print("==================================================")
        
        # 폴더가 존재하지 않는 경우 자동으로 폴더를 생성
        if not self.target_dir.exists():
            try:
                self.target_dir.mkdir(parents=True, exist_ok=True)
                print(f"📁 새 폴더를 생성했습니다: {self.target_dir}")
            except Exception as e:
                print(f"❌ 에러: 폴더를 생성할 수 없습니다: {e}")
                return

        # 대소문자 구분 없이 .pdf 및 .PDF 파일 모두 수집
        pdf_files = list(self.target_dir.glob("*.pdf")) + list(self.target_dir.glob("*.PDF"))
        pdf_files = sorted(list(set(pdf_files)))
        
        total_count = len(pdf_files)
        print(f"📊 총 {total_count}개의 지식 리소스(PDF)를 발견했습니다.\n")
        
        if total_count == 0:
            print("ℹ️ 처리할 파일이 없습니다. E:/la/sea/pdf/ 또는 워크스페이스 내의 pdf/ 폴더 안에 PDF 파일을 추가해 주세요.")
            return

        success_count = 0
        
        for index, file_path in enumerate(pdf_files, 1):
            print(f"🔄 [{index}/{total_count}] 가동 중...")
            result = self.extract_and_analyze(file_path)
            
            if result["status"] == "success":
                print(f"✅ 리소스 등록 성공!")
                print(f"   파일명: {result['file_name']} ({result['file_size']})")
                print(f"   데이터 요약: {result['text_preview']}")
                success_count += 1
            else:
                print(f"❌ 리소스 등록 실패: {result['file_name']}")
                print(f"   사유: {result['message']}")
                
            print("-" * 50)
            
        print(f"\n🏁 [전체 공정 가동 종료]")
        print(f"📈 총 {total_count}개 중 {success_count}개의 지식이 '아라의 지혜의 신경망'에 성공적으로 통합되었습니다.")

if __name__ == "__main__":
    TARGET_PATH = "e:/la/sea/pdf/"
    wisdom_chain = ArasWisdomNeuralNetwork(target_dir=TARGET_PATH)
    wisdom_chain.run_pipeline()
