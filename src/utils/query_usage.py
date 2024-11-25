from db_queries import WooriBondDB


def example_queries():
    db = WooriBondDB()

    # 1. 특정 채권의 특정 기간 데이터 조회
    bond_data = db.get_bond_data(
        bond_names=["우리금융지주4-1", "우리금융지주4-2"],
        start_date="2024-01-01",
        end_date="2024-03-31",
        columns=["일자", "종목명", "평균수익률", "평균가격"],
    )
    print("채권 데이터:")
    print(bond_data)

    # 2. 스프레드 범위로 데이터 조회
    spread_data = db.get_spread_data(
        start_date="2024-01-01", min_spread=0.5, max_spread=1.0
    )
    print("\n스프레드 데이터:")
    print(spread_data)

    # 3. 사용자 정의 쿼리 실행
    custom_query = """
    SELECT a.일자, a.종목명, a.평균수익률, b.스프레드
    FROM woori_bond_data a
    JOIN spread_data b
    ON a.일자 = b.일자 AND a.종목명 = b.종목명
    WHERE a.일자 BETWEEN '{start_date}' AND '{end_date}'
    AND a.평균수익률 > {yield_threshold}
    ORDER BY a.일자, a.종목명
    """

    params = {
        "start_date": "2024-01-01",
        "end_date": "2024-03-31",
        "yield_threshold": 3.5,
    }

    result = db.execute_custom_query(custom_query, params)
    print("\n사용자 정의 쿼리 결과:")
    print(result)


if __name__ == "__main__":
    example_queries()
