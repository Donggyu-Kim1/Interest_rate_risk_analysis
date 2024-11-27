import pandas as pd
import numpy as np
import pymysql
from pathlib import Path
import re
from config.config_db import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_CHARSET


def create_connection():
    """데이터베이스 연결 생성"""
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        db=DB_NAME,
        charset=DB_CHARSET,
    )


def create_tables(conn):
    """테이블 생성"""
    cursor = conn.cursor()

    # 채권 기본 정보 테이블
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS bond_info (
            종목명 VARCHAR(20) PRIMARY KEY,
            표준코드 VARCHAR(12),
            발행일 DATE,
            만기일 DATE,
            발행액 INT,
            표면금리 FLOAT,
            이자지급방법 VARCHAR(10),
            이자지급주기 INT,
            발행시만기 FLOAT,
            잔존만기 FLOAT,
            만기그룹 VARCHAR(10)
        )
    """
    )

    # 국고채 금리 테이블
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS govt_bond_rates (
            일자 DATE,
            국고채권1년 FLOAT,
            국고채권3년 FLOAT,
            국고채권5년 FLOAT,
            국고채권10년 FLOAT,
            통안증권91일 FLOAT,
            통안증권1년 FLOAT,
            통안증권2년 FLOAT,
            PRIMARY KEY (일자)
        )
    """
    )

    # 개별 채권 시장 데이터 테이블
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS woori_bond_data (
            일자 DATE,
            종목명 VARCHAR(20),
            평균수익률 FLOAT,
            수익률대비 FLOAT,
            평균가격 FLOAT,
            가격대비 FLOAT,
            PRIMARY KEY (일자, 종목명)
        )
    """
    )

    # 스프레드 데이터 테이블
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS spread_data (
            일자 DATE,
            종목명 VARCHAR(20),
            회사채수익률 FLOAT,
            국고채수익률 FLOAT,
            스프레드 FLOAT,
            PRIMARY KEY (일자, 종목명)
        )
    """
    )

    conn.commit()


def insert_bond_info(conn, file_path):
    """채권 기본 정보 삽입"""
    try:
        df = pd.read_csv(file_path, parse_dates=["발행일", "만기일"])
        cursor = conn.cursor()

        for _, row in df.iterrows():
            sql = """INSERT INTO bond_info VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    표준코드=VALUES(표준코드), 발행일=VALUES(발행일), 만기일=VALUES(만기일),
                    발행액=VALUES(발행액), 표면금리=VALUES(표면금리), 이자지급방법=VALUES(이자지급방법),
                    이자지급주기=VALUES(이자지급주기), 발행시만기=VALUES(발행시만기),
                    잔존만기=VALUES(잔존만기), 만기그룹=VALUES(만기그룹)"""
            cursor.execute(sql, tuple(row))

        conn.commit()
        print("Bond info insertion completed successfully!")
    except Exception as e:
        print(f"Error inserting bond info: {e}")
        conn.rollback()


def insert_govt_rates(conn, file_path):
    """국고채 금리 데이터 삽입"""
    try:
        df = pd.read_csv(file_path, parse_dates=["일자"])
        cursor = conn.cursor()

        for _, row in df.iterrows():
            sql = """INSERT INTO govt_bond_rates VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    국고채권1년=VALUES(국고채권1년), 국고채권3년=VALUES(국고채권3년),
                    국고채권5년=VALUES(국고채권5년), 국고채권10년=VALUES(국고채권10년),
                    통안증권91일=VALUES(통안증권91일), 통안증권1년=VALUES(통안증권1년),
                    통안증권2년=VALUES(통안증권2년)"""
            cursor.execute(sql, tuple(row))

        conn.commit()
        print("Government bond rates insertion completed successfully!")

    except Exception as e:
        print(f"Error inserting government rates: {e}")
        conn.rollback()


def insert_woori_bond_data(conn, data_dir):
    """개별 채권 시장 데이터 삽입"""
    cursor = conn.cursor()

    # 채권 정보 파일에서 종목명 리스트 가져오기
    bond_info_df = pd.read_csv(data_dir / "bond_info/woori_bond_info.csv")
    bond_dict = {}

    # 파일명과 종목명 매핑 생성
    for _, row in bond_info_df.iterrows():
        # 종목명에서 숫자 부분 추출 (예: '우리금융지주4-1' -> '4-1')
        bond_number = re.search(r"\d+(?:-\d+)?", row["종목명"]).group()
        bond_dict[bond_number] = row["종목명"]

    # 모든 채권 데이터 파일 처리
    for file_path in data_dir.glob("market_data/woori_bond_data_*.csv"):
        try:
            # 파일명에서 채권 번호 추출
            bond_number = re.search(r"data_(\d+(?:-\d+)?)", file_path.stem).group(1)
            bond_name = bond_dict.get(bond_number)

            if bond_name is None:
                print(f"Warning: No matching bond name found for file {file_path.name}")
                continue

            # 데이터 읽기 및 전처리
            df = pd.read_csv(file_path, parse_dates=["일자"])

            # NaN 값을 None으로 변환, MySQL은 NaN 사용 불가
            df = df.replace({np.nan: None})

            # 이름 재정의
            df = df.rename(
                columns={
                    "채권평가사 평균수익률_수익률": "평균수익률",
                    "채권평가사 평균수익률_대비": "수익률대비",
                    "채권평가사 평균가격_가격": "평균가격",
                    "채권평가사 평균가격_대비": "가격대비",
                }
            )

            # 종목명 컬럼 추가
            df["종목명"] = bond_name

            # 데이터 삽입
            for _, row in df.iterrows():
                sql = """INSERT INTO woori_bond_data 
                        (일자, 종목명, 평균수익률, 수익률대비, 평균가격, 가격대비)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                        평균수익률=VALUES(평균수익률),
                        수익률대비=VALUES(수익률대비),
                        평균가격=VALUES(평균가격),
                        가격대비=VALUES(가격대비)"""
                values = (
                    row["일자"],
                    row["종목명"],
                    row["평균수익률"],
                    row["수익률대비"],
                    row["평균가격"],
                    row["가격대비"],
                )
                cursor.execute(sql, values)

            print(f"Processed {file_path.name} for {bond_name}")

        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")
            conn.rollback()

    conn.commit()
    print("Bond info insertion completed successfully!")


def insert_spread_data(conn, file_path):
    """스프레드 데이터 삽입"""
    try:
        # 스프레드 데이터 읽기
        df = pd.read_csv(file_path, parse_dates=["일자"])

        # 필요한 컬럼만 선택
        spread_data = df[["일자", "종목명", "회사채수익률", "국고채수익률", "스프레드"]]

        cursor = conn.cursor()

        # 데이터 삽입
        for _, row in spread_data.iterrows():
            sql = """INSERT INTO spread_data 
                    (일자, 종목명, 회사채수익률, 국고채수익률, 스프레드)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    회사채수익률=VALUES(회사채수익률),
                    국고채수익률=VALUES(국고채수익률),
                    스프레드=VALUES(스프레드)"""

            values = (
                row["일자"],
                row["종목명"],
                row["회사채수익률"],
                row["국고채수익률"],
                row["스프레드"],
            )

            cursor.execute(sql, values)

        conn.commit()
        print(f"Spread data insertion completed successfully!")

    except Exception as e:
        print(f"Error inserting spread data: {e}")
        conn.rollback()


def main():
    """메인 실행 함수"""
    # 데이터베이스 연결
    conn = create_connection()

    try:
        # 테이블 생성
        create_tables(conn)

        # 데이터 파일 경로 설정
        data_dir = Path("data/processed")

        # 각 데이터 파일 삽입
        insert_bond_info(conn, data_dir / "bond_info/woori_bond_info.csv")
        insert_govt_rates(conn, data_dir / "market_data/govt_bond_rates.csv")
        insert_woori_bond_data(conn, data_dir)
        insert_spread_data(conn, data_dir / "spread_data/woori_bond_spreads.csv")

        print("Data insertion completed successfully!")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
