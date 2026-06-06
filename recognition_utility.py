# -*- coding: utf-8 -*-
import os
import sys
import json
import time
import cv2

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(WORKSPACE_DIR, 'data', 'sensory_log.json')

def ensure_log_dir():
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

def write_sensory_log(location, person_detected, objects_detected):
    ensure_log_dir()
    logs = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except Exception:
            logs = []
            
    # Keep only recent 50 logs
    if len(logs) >= 50:
        logs = logs[-49:]
        
    entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "location": location,
        "person": "감지됨 (사용자)" if person_detected else "없음",
        "objects": objects_detected
    }
    
    # Prepend the newest entry
    logs.insert(0, entry)
    
    try:
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Failed to write sensory log: {e}")

def main():
    print("[기동] ARA 로컬 시각 인식 엔진 구동 중...")
    
    # Load frontal face Haar Cascade classifier
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(cascade_path)
    if face_cascade.empty():
        print("[오류] Haar Cascade XML 로드 실패.")
        sys.exit(1)
        
    # Open camera capture stream
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[오류] 카메라 장치를 열 수 없습니다.")
        sys.exit(1)
        
    print("[정보] 얼굴 인식 창을 기동합니다. 종료하려면 'q' 키를 누르십시오.")
    
    last_log_time = 0
    
    # Background substraction for simple motion activity estimation
    prev_gray = None
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("[경고] 카메라 프레임을 읽을 수 없습니다.")
            time.sleep(0.1)
            continue
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.2, 
            minNeighbors=5, 
            minSize=(30, 30)
        )
        
        # Draw rectangles on detected faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (61, 102, 78), 2) # forest green
            cv2.putText(frame, "Human", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (61, 102, 78), 2)
            
        person_detected = len(faces) > 0
        
        # Estimate Environment (Indoors vs Outdoors) based on luminosity and motion variation
        # Calculate average luminosity
        avg_luminosity = gray.mean()
        
        # Calculate motion/activity levels
        motion_score = 0.0
        if prev_gray is not None:
            frame_diff = cv2.absdiff(gray, prev_gray)
            motion_score = frame_diff.mean()
        prev_gray = gray
        
        # Simple heuristic:
        # High avg luminosity (typically sun/sky outdoors is > 190) combined with motion variability suggests outdoors
        if avg_luminosity > 185 or (motion_score > 35.0 and avg_luminosity > 160):
            location = "실외 (집밖)"
        else:
            location = "실내 (집안)"
            
        objects_detected = ["face"] if person_detected else []
        
        # Write to log periodically (every 3 seconds to avoid disk thrashing)
        curr_time = time.time()
        if curr_time - last_log_time >= 3.0:
            write_sensory_log(location, person_detected, objects_detected)
            last_log_time = curr_time
            
        # Draw overlay info on frame window
        cv2.putText(frame, f"Location: {location}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Faces Detected: {len(faces)}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, "ARA Vision - Press 'q' to Quit", (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Show window local feed
        cv2.imshow("ARA Vision Core Engine", frame)
        
        # Exit on 'q' key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()
    print("[종료] ARA 로컬 시각 인식 엔진 종료.")

if __name__ == "__main__":
    main()
