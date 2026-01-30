"""logistics_lines 테이블에 AUTOINCREMENT 설정 추가"""
from database import engine
from sqlalchemy import text

def fix_autoincrement():
    """id 컬럼에 SERIAL 타입으로 변경하여 AUTOINCREMENT 추가"""
    with engine.connect() as conn:
        try:
            # 1. 시퀀스 생성
            print("1. 시퀀스 생성 중...")
            conn.execute(text("""
                CREATE SEQUENCE IF NOT EXISTS logistics_lines_id_seq;
            """))
            conn.commit()
            print("  ✅ 시퀀스 생성 완료")
            
            # 2. 기존 데이터의 최대값 확인
            print("\n2. 기존 데이터 확인 중...")
            result = conn.execute(text("""
                SELECT COALESCE(MAX(id), 0) FROM logistics_lines;
            """))
            max_id = result.scalar()
            print(f"  현재 최대 ID: {max_id}")
            
            # 3. 시퀀스 시작값 설정
            print("\n3. 시퀀스 시작값 설정 중...")
            conn.execute(text(f"""
                SELECT setval('logistics_lines_id_seq', {max_id + 1}, false);
            """))
            conn.commit()
            print(f"  ✅ 시퀀스 시작값: {max_id + 1}")
            
            # 4. id 컬럼에 시퀀스 기본값 설정
            print("\n4. id 컬럼 기본값 설정 중...")
            conn.execute(text("""
                ALTER TABLE logistics_lines 
                ALTER COLUMN id 
                SET DEFAULT nextval('logistics_lines_id_seq');
            """))
            conn.commit()
            print("  ✅ id 컬럼 기본값 설정 완료")
            
            # 5. 시퀀스 소유권 설정
            print("\n5. 시퀀스 소유권 설정 중...")
            conn.execute(text("""
                ALTER SEQUENCE logistics_lines_id_seq 
                OWNED BY logistics_lines.id;
            """))
            conn.commit()
            print("  ✅ 시퀀스 소유권 설정 완료")
            
            # 6. 검증
            print("\n6. 설정 검증 중...")
            result = conn.execute(text("""
                SELECT column_default 
                FROM information_schema.columns 
                WHERE table_name = 'logistics_lines' 
                AND column_name = 'id';
            """))
            default_value = result.scalar()
            print(f"  id 컬럼 기본값: {default_value}")
            
            if default_value and 'nextval' in default_value:
                print("\n✅ AUTOINCREMENT 설정이 성공적으로 완료되었습니다!")
            else:
                print("\n⚠️ 기본값 설정 확인이 필요합니다.")
                
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            conn.rollback()

if __name__ == "__main__":
    fix_autoincrement()
