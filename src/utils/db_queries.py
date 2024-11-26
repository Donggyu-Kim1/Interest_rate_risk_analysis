from sqlalchemy import create_engine
import pandas as pd
from typing import Optional, Union, Dict, List, Any
from datetime import datetime
from config.config_db import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_CHARSET


class WooriBondDB:
    def __init__(self):
        self.engine = create_engine(
            f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?charset={DB_CHARSET}"
        )

    def execute_query(self, query: str) -> pd.DataFrame:
        """
        SQL 쿼리를 실행하고 결과를 DataFrame으로 반환

        Args:
            query: 실행할 SQL 쿼리문

        Returns:
            pd.DataFrame: 쿼리 결과
        """
        try:
            return pd.read_sql(query, self.engine)
        except Exception as e:
            print(f"쿼리 실행 중 오류 발생: {e}")
            print(f"실행된 쿼리: {query}")
            raise

    def get_bond_data(
        self,
        bond_names: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        columns: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        채권 데이터 조회

        Args:
            bond_names: 조회할 종목명 리스트
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
            columns: 조회할 컬럼 리스트

        Returns:
            pd.DataFrame: 조회된 채권 데이터
        """
        try:
            # 기본 쿼리 구성
            select_cols = "*" if not columns else ", ".join(columns)
            query = f"""
                SELECT {select_cols}
                FROM woori_bond_data
                WHERE 1=1
            """

            # 조건 추가
            if bond_names:
                bonds_str = "', '".join(bond_names)
                query += f" AND 종목명 IN ('{bonds_str}')"
            if start_date:
                query += f" AND 일자 >= '{start_date}'"
            if end_date:
                query += f" AND 일자 <= '{end_date}'"

            query += " ORDER BY 일자, 종목명"

            return self.execute_query(query)

        except Exception as e:
            print(f"채권 데이터 조회 중 오류 발생: {e}")
            raise

    def get_spread_data(
        self,
        bond_names: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        min_spread: Optional[float] = None,
        max_spread: Optional[float] = None,
    ) -> pd.DataFrame:
        """
        스프레드 데이터 조회

        Args:
            bond_names: 조회할 종목명 리스트
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
            min_spread: 최소 스프레드
            max_spread: 최대 스프레드

        Returns:
            pd.DataFrame: 조회된 스프레드 데이터
        """
        try:
            query = """
                SELECT *
                FROM spread_data
                WHERE 1=1
            """

            if bond_names:
                bonds_str = "', '".join(bond_names)
                query += f" AND 종목명 IN ('{bonds_str}')"
            if start_date:
                query += f" AND 일자 >= '{start_date}'"
            if end_date:
                query += f" AND 일자 <= '{end_date}'"
            if min_spread is not None:
                query += f" AND 스프레드 >= {min_spread}"
            if max_spread is not None:
                query += f" AND 스프레드 <= {max_spread}"

            query += " ORDER BY 일자, 종목명"

            return self.execute_query(query)

        except Exception as e:
            print(f"스프레드 데이터 조회 중 오류 발생: {e}")
            raise

    def execute_custom_query(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        사용자 정의 쿼리 실행

        Args:
            query: SQL 쿼리문
            params: 쿼리 파라미터

        Returns:
            pd.DataFrame: 쿼리 결과
        """
        try:
            if params:
                query = query.format(**params)
            return self.execute_query(query)

        except Exception as e:
            print(f"사용자 정의 쿼리 실행 중 오류 발생: {e}")
            raise
