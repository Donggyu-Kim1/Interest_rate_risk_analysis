from src.utils.db_queries import WooriBondDB


class CovidBondAnalysis:
    def __init__(self):
        self.db = WooriBondDB()

    def get_covid_period_rates(self, start_date="2020-01-01", end_date="2021-12-31"):
        """코로나 시기의 국고채 금리 데이터 조회"""
        params = {"start_date": start_date, "end_date": end_date}

        query = """
        SELECT 일자, 국고채권1년, 국고채권3년, 국고채권5년, 국고채권10년
        FROM govt_bond_rates
        WHERE 일자 >= '{start_date}'
        AND 일자 <= '{end_date}'
        ORDER BY 일자
        """

        return self.db.execute_custom_query(query, params)

    def find_lowest_rates_period(self, window_size=30):
        """이동평균을 사용하여 금리가 가장 낮았던 기간 찾기"""
        params = {
            "window": window_size,
            "start_date": "2020-01-01",
            "end_date": "2021-12-31",
        }

        query = """
        SELECT 일자, 
               AVG(국고채권1년) OVER (ORDER BY 일자 ROWS BETWEEN {window} PRECEDING AND CURRENT ROW) as MA_1Y,
               AVG(국고채권3년) OVER (ORDER BY 일자 ROWS BETWEEN {window} PRECEDING AND CURRENT ROW) as MA_3Y,
               AVG(국고채권5년) OVER (ORDER BY 일자 ROWS BETWEEN {window} PRECEDING AND CURRENT ROW) as MA_5Y,
               국고채권1년, 국고채권3년, 국고채권5년
        FROM govt_bond_rates
        WHERE 일자 >= '{start_date}'
        AND 일자 <= '{end_date}'
        ORDER BY 일자
        """

        return self.db.execute_custom_query(query, params)

    def analyze_rate_drop(self):
        """금리 하락 분석"""
        params = {
            "start_date": "2020-01-01",
            "end_date": "2021-12-31",
            "drop_threshold": -0.1,
        }

        query = """
        WITH rate_changes AS (
            SELECT 
                일자,
                국고채권1년,
                국고채권3년,
                국고채권5년,
                LAG(국고채권1년) OVER (ORDER BY 일자) as prev_1y,
                LAG(국고채권3년) OVER (ORDER BY 일자) as prev_3y,
                LAG(국고채권5년) OVER (ORDER BY 일자) as prev_5y
            FROM govt_bond_rates
            WHERE 일자 >= '{start_date}'
            AND 일자 <= '{end_date}'
        )
        SELECT 
            일자,
            ROUND(국고채권1년 - prev_1y, 3) as drop_1y,
            ROUND(국고채권3년 - prev_3y, 3) as drop_3y,
            ROUND(국고채권5년 - prev_5y, 3) as drop_5y
        FROM rate_changes
        WHERE (국고채권1년 - prev_1y < {drop_threshold})
           OR (국고채권3년 - prev_3y < {drop_threshold})
           OR (국고채권5년 - prev_5y < {drop_threshold})
        ORDER BY 일자
        """

        return self.db.execute_custom_query(query, params)


def main():
    try:
        analyzer = CovidBondAnalysis()

        # 1. 전체 기간 데이터 조회
        print("2020-2021년 국고채 금리 데이터 조회 중...")
        covid_rates = analyzer.get_covid_period_rates()
        if not covid_rates.empty:
            print("\n기간별 국고채 금리:")
            print(covid_rates.head())
        else:
            print("해당 기간의 데이터가 없습니다.")

        # 2. 금리가 가장 낮았던 기간 찾기
        print("\n금리 최저점 기간 분석 중...")
        lowest_rates = analyzer.find_lowest_rates_period()
        if not lowest_rates.empty:
            min_rate_row = lowest_rates.loc[lowest_rates["MA_3Y"].idxmin()]
            print(f"3년물 기준 최저 금리 기록일: {min_rate_row['일자']}")
            print(f"해당 시점 3년물 금리: {min_rate_row['국고채권3년']:.3f}%")
            print(f"30일 이동평균: {min_rate_row['MA_3Y']:.3f}%")
        else:
            print("해당 기간의 데이터가 없습니다.")

        # 3. 급격한 금리 하락 기간 분석
        print("\n주요 금리 하락 시점 분석 중...")
        rate_drops = analyzer.analyze_rate_drop()
        if not rate_drops.empty:
            print("\n10bp 이상 하락한 날짜 및 하락폭:")
            print(rate_drops)

            # 최대 하락 시점 찾기
            max_drop_1y = rate_drops.loc[rate_drops["drop_1y"].idxmin()]
            max_drop_3y = rate_drops.loc[rate_drops["drop_3y"].idxmin()]
            print(f"\n최대 하락 시점:")
            print(f"1년물: {max_drop_1y['일자']} ({max_drop_1y['drop_1y']}%p)")
            print(f"3년물: {max_drop_3y['일자']} ({max_drop_3y['drop_3y']}%p)")
        else:
            print("큰 폭의 금리 하락이 없었습니다.")

    except Exception as e:
        print(f"분석 중 오류 발생: {str(e)}")
        import traceback

        print(traceback.format_exc())


if __name__ == "__main__":
    main()
