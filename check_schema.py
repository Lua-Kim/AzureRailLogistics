"""데이터베이스 스키마 확인 스크립트"""
from database import engine
from sqlalchemy import text

def check_logistics_lines_schema():
    """logistics_lines 테이블의 스키마 확인"""
    with engine.connect() as conn:
        # 테이블 컬럼 정보 확인
        result = conn.execute(text("""
            SELECT 
                column_name, 
                column_default, 
                is_nullable,
                data_type
            FROM information_schema.columns 
            WHERE table_name = 'logistics_lines' 
            ORDER BY ordinal_position
        """))
        
        print("=== logistics_lines 테이블 스키마 ===")
        for row in result:
            print(f"컬럼: {row[0]}, 기본값: {row[1]}, NULL 허용: {row[2]}, 타입: {row[3]}")
        
        # SEQUENCE 확인
        result = conn.execute(text("""
            SELECT 
                sequence_name,
                data_type,
                start_value,
                increment
            FROM information_schema.sequences
            WHERE sequence_name LIKE '%logistics_lines%'
        """))
        
        print("\n=== logistics_lines 관련 시퀀스 ===")
        sequences = list(result)
        if sequences:
            for row in sequences:
                print(f"시퀀스: {row[0]}, 타입: {row[1]}, 시작값: {row[2]}, 증가: {row[3]}")
        else:
            print("시퀀스가 없습니다! (AUTOINCREMENT 설정 누락)")

if __name__ == "__main__":
    check_logistics_lines_schema()
