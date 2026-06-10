# src/database/db_initializer.py
import os
import sqlite3

def initialize_database(db_path="C:/la/sea/data/ara_system.db", schema_path="C:/la/sea/src/database/schema.sql"):
    print(f"[DB Initializer] 데이터베이스 초기화 진행 중: {db_path}")
    
    # Ensure the parent directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Connect and apply schema
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
            
        cursor.executescript(schema_sql)
        conn.commit()
        print("[DB Initializer] 스키마 적용 완료 (AgentRegistry, MemoryContext 테이블 생성 완료).")
        
        # Seed initial/mock data for demonstration
        cursor.execute("INSERT OR REPLACE INTO AgentRegistry (agent_name, auth_token, status) VALUES (?, ?, ?)", 
                       ("VisionAgent", "ara_token_secure_vision_2026", "IDLE"))
        cursor.execute("INSERT OR REPLACE INTO AgentRegistry (agent_name, auth_token, status) VALUES (?, ?, ?)", 
                       ("MainRouter", "ara_token_secure_router_2026", "RUNNING"))
                       
        cursor.execute("INSERT OR REPLACE INTO MemoryContext (summary_text, importance_score) VALUES (?, ?)",
                       ("이전 대화 컨텍스트 요약: CNC 가공 라인 3번의 G코드 동작 피드백 및 Vision 인지 모델 매뉴얼 대조 완료.", 0.85))
                       
        conn.commit()
        print("[DB Initializer] 초기 테스트 데이터 시딩 완료.")
        
        # Verify seeding
        cursor.execute("SELECT * FROM AgentRegistry")
        print("--- AgentRegistry 현황 ---")
        for row in cursor.fetchall():
            print(f"Agent: {row[0]}, Token: {row[1]}, Status: {row[2]}, Last Heartbeat: {row[3]}")
            
        cursor.execute("SELECT * FROM MemoryContext")
        print("--- MemoryContext 현황 ---")
        for row in cursor.fetchall():
            print(f"ID: {row[0]}, Summary: {row[1]}, Score: {row[2]}, Timestamp: {row[3]}")
            
        conn.close()
        print("[DB Initializer] 데이터베이스 작업 성공적으로 완료.")
        return True
    except Exception as e:
        print(f"[DB Initializer 오류]: {e}")
        return False

if __name__ == "__main__":
    initialize_database()
