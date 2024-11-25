import pandas as pd
import pymysql
from pathlib import Path
from sqlalchemy import create_engine


def create_connection():
    """SQLAlchemy 엔진 생성"""
    return create_engine(
        "mysql+pymysql://root:3406@localhost/woori_bond_db?charset=utf8"
    )


def check_bond_info(engine):
    """채권 기본 정보 테이블 조회"""
    try:
        query = """
        SELECT * FROM bond_info
        ORDER BY 종목명;
        """
        df = pd.read_sql(query, engine)
        print("\n=== 채권 기본 정보 ===")
        print(f"총 레코드 수: {len(df)}")
        print("\n샘플 데이터:")
        print(df)

        # 중복 검사
        duplicates = df[df.duplicated(subset=["종목명"], keep=False)]
        if not duplicates.empty:
            print("\n중복된 레코드:")
            print(duplicates)

        return df

    except Exception as e:
        print(f"채권 정보 조회 중 오류 발생: {e}")


def check_govt_rates(engine):
    """국고채 금리 테이블 조회"""
    try:
        query = """
        SELECT * FROM govt_bond_rates
        ORDER BY 일자 DESC
        LIMIT 10;
        """
        df = pd.read_sql(query, engine)
        print("\n=== 국고채 금리 데이터 ===")
        print(f"최근 10일 데이터:")
        print(df)

        # 전체 레코드 수 확인
        count_query = "SELECT COUNT(*) as count FROM govt_bond_rates"
        total_count = pd.read_sql(count_query, engine)
        print(f"\n총 레코드 수: {total_count.iloc[0]['count']}")

        # 중복 검사
        dup_query = """
        SELECT 일자, COUNT(*) as count
        FROM govt_bond_rates
        GROUP BY 일자
        HAVING COUNT(*) > 1;
        """
        duplicates = pd.read_sql(dup_query, engine)
        if not duplicates.empty:
            print("\n중복된 날짜:")
            print(duplicates)

        return df

    except Exception as e:
        print(f"국고채 금리 데이터 조회 중 오류 발생: {e}")


def check_woori_bond_data(engine):
    """개별 채권 시장 데이터 테이블 조회"""
    try:
        # 종목별 레코드 수 확인
        count_query = """
        SELECT 종목명, COUNT(*) as 레코드수
        FROM woori_bond_data
        GROUP BY 종목명
        ORDER BY 종목명;
        """
        counts = pd.read_sql(count_query, engine)
        print("\n=== 개별 채권 시장 데이터 ===")
        print("종목별 레코드 수:")
        print(counts)

        # 최근 데이터 샘플 조회
        sample_query = """
        SELECT *
        FROM woori_bond_data
        WHERE 일자 >= (SELECT MAX(일자) - INTERVAL 5 DAY FROM woori_bond_data)
        ORDER BY 일자 DESC, 종목명
        LIMIT 10;
        """
        recent_data = pd.read_sql(sample_query, engine)
        print("\n최근 데이터 샘플:")
        print(recent_data)

        # 중복 검사
        dup_query = """
        SELECT 일자, 종목명, COUNT(*) as count
        FROM woori_bond_data
        GROUP BY 일자, 종목명
        HAVING COUNT(*) > 1;
        """
        duplicates = pd.read_sql(dup_query, engine)
        if not duplicates.empty:
            print("\n중복된 레코드:")
            print(duplicates)

        return counts, recent_data

    except Exception as e:
        print(f"개별 채권 데이터 조회 중 오류 발생: {e}")


def check_spread_data(engine):
    """스프레드 데이터 테이블 조회"""
    try:
        # 종목별 레코드 수 확인
        count_query = """
        SELECT 종목명, COUNT(*) as 레코드수
        FROM spread_data
        GROUP BY 종목명
        ORDER BY 종목명;
        """
        counts = pd.read_sql(count_query, engine)
        print("\n=== 스프레드 데이터 ===")
        print("종목별 레코드 수:")
        print(counts)

        # 최근 데이터 샘플 조회
        sample_query = """
        SELECT *
        FROM spread_data
        WHERE 일자 >= (SELECT MAX(일자) - INTERVAL 5 DAY FROM spread_data)
        ORDER BY 일자 DESC, 종목명
        LIMIT 10;
        """
        recent_data = pd.read_sql(sample_query, engine)
        print("\n최근 데이터 샘플:")
        print(recent_data)

        # 중복 검사
        dup_query = """
        SELECT 일자, 종목명, COUNT(*) as count
        FROM spread_data
        GROUP BY 일자, 종목명
        HAVING COUNT(*) > 1;
        """
        duplicates = pd.read_sql(dup_query, engine)
        if not duplicates.empty:
            print("\n중복된 레코드:")
            print(duplicates)

        return counts, recent_data

    except Exception as e:
        print(f"스프레드 데이터 조회 중 오류 발생: {e}")


def main():
    """메인 실행 함수"""
    try:
        engine = create_connection()

        # 각 테이블 데이터 확인
        check_bond_info(engine)
        check_govt_rates(engine)
        check_woori_bond_data(engine)
        check_spread_data(engine)

    except Exception as e:
        print(f"데이터 확인 중 오류 발생: {e}")


if __name__ == "__main__":
    main()
