# src/agents/vision_agent.py
import asyncio
import socket
import json
import os
import sys

class VisionAgent:
    def __init__(self, socket_path="/tmp/ara_system.sock"):
        self.socket_path = socket_path
        self.reader = None
        self.writer = None
        self.model_loaded = False
        self.net = None # ONNX Runtime/OpenCV 인터페이스 홀더

    async def connect_core(self):
        """C++ 라우터 코어와 UDS 연결 확립"""
        while True:
            try:
                if os.name == 'nt':
                    # Windows 환경의 경우, asyncio.open_unix_connection()이 미지원되므로
                    # AF_UNIX 소켓 객체를 직접 생성하여 연결한 뒤 stream을 바인딩하거나
                    # TCP 시뮬레이션 포트(5000)로 폴백합니다.
                    print("[VisionAgent] Windows 환경 감지 - UDS / TCP 호환 모드 실행")
                    try:
                        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                        self.sock.connect(self.socket_path)
                        self.reader, self.writer = await asyncio.open_connection(sock=self.sock)
                    except Exception as e:
                        # TCP fallback for testing under standard Windows environments
                        print(f"[VisionAgent] UDS 소켓 연결 불가({e}). 로컬 TCP 시뮬레이터(127.0.0.1:5000) 연결 시도...")
                        self.reader, self.writer = await asyncio.open_connection("127.0.0.1", 5000)
                else:
                    self.reader, self.writer = await asyncio.open_unix_connection(self.socket_path)
                
                print("[VisionAgent] 코어 라우터 연결 성공.")
                # 에이전트 등록 패킷 전송
                reg_packet = {"sender": "VisionAgent", "action": "REGISTER"}
                self.writer.write(json.dumps(reg_packet).encode())
                await self.writer.drain()
                break
            except Exception as e:
                print(f"[VisionAgent] 연결 재시도 중... ({e})")
                await asyncio.sleep(2)

    def load_lightweight_model(self):
        """VRAM을 쓰지 않고 CPU/내장그래픽 전용으로 ONNX 초경량 모델 로드"""
        if not self.model_loaded:
            print("[VisionAgent] 이벤트 트리거 발생: 초경량 ONNX Vision 모델 로드 (CPU 연산 배치)")
            try:
                import onnxruntime as ort
                # 64GB RAM 시스템 메모리를 적극 활용하기 위해 CPUExecutionProvider 설정
                # VRAM 사용량은 0MB로 유지되며, CPU 멀티스레딩 최적화 옵션 지정
                opts = ort.SessionOptions()
                opts.intra_op_num_threads = 4
                opts.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
                self.net = ort.InferenceSession("models/vision/yolov8n.onnx", sess_options=opts, providers=['CPUExecutionProvider'])
                print("[VisionAgent] ONNX Runtime: YOLOv8n 모델 로드 완료 (CPUExecutionProvider)")
            except ImportError:
                print("[VisionAgent] onnxruntime 패키지가 없어 시뮬레이션 모델(CPU 연산)로 대체 로드합니다.")
                self.net = "MOCK_CPU_ONNX_SESSION"
            self.model_loaded = True

    def unload_model(self):
        """분석 태스크 종료 후 메모리 즉시 해제"""
        if self.model_loaded:
            self.net = None
            self.model_loaded = False
            print("[VisionAgent] 분석 완료: Vision 모델 메모리 반환 완료.")

    async def listen_commands(self):
        while True:
            try:
                data = await self.reader.read(4096)
                if not data:
                    print("[VisionAgent] 라우터로부터 연결 끊김.")
                    break
                
                cmd = json.loads(data.decode())
                print(f"[VisionAgent 명령 수신]: {cmd}")
                
                if cmd.get("action") == "TRIGGER_DETECTION":
                    self.load_lightweight_model()
                    
                    # 시뮬레이션 분석 수행 (추론 연산 시간 시뮬레이션)
                    print("[VisionAgent] 객체 감지 추론 연산 중 (CPU 스레드 점유)...")
                    await asyncio.sleep(1) 
                    
                    # 분석 결과 생성 및 전송
                    result_packet = {
                        "sender": "VisionAgent",
                        "target": cmd.get("sender", "Core"),
                        "action": "DETECTION_RESULT",
                        "status": "SUCCESS",
                        "payload": {
                            "detected_objects": ["CNC_Tool", "Workpiece_Aligned"],
                            "confidence": 0.94
                        }
                    }
                    self.writer.write(json.dumps(result_packet).encode())
                    await self.writer.drain()
                    print("[VisionAgent] 추론 결과 전송 완료.")
                    
                    # 모델 언로드 정책 실행 (VRAM/RAM 즉각 해제)
                    self.unload_model()
            except Exception as e:
                print(f"[VisionAgent 오류]: {e}")
                break

async def main():
    # Windows의 경우 ProactorEventLoop의 소켓 호환성 경고 회피를 위해 selector 이벤트 루프 사용 검토 가능
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    # 소켓 경로를 환경 설정에 맞게 지정
    socket_path = os.environ.get("ARA_SOCKET_PATH", "/tmp/ara_system.sock")
    agent = VisionAgent(socket_path=socket_path)
    await agent.connect_core()
    await agent.listen_commands()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[VisionAgent] 에이전트가 키보드 인터럽트에 의해 종료되었습니다.")
