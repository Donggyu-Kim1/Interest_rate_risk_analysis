from src.utils.db_queries import WooriBondDB


class InflationPeriodAnalysis:
    def __init__(self):
        self.db = WooriBondDB()

    def get_inflation_period_rates(
        self, start_date="2022-01-01", end_date="2023-12-31"
    ):
        """인플레이션 기간 금리 데이터 조회"""
        params = {"start_date": start_date, "end_date": end_date}

        query = """
        WITH daily_changes AS (
            SELECT 
                일자,
                국고채권1년,
                국고채권3년,
                국고채권5년,
                국고채권10년,
                LAG(국고채권1년) OVER (ORDER BY 일자) as prev_1y,
                LAG(국고채권3년) OVER (ORDER BY 일자) as prev_3y,
                LAG(국고채권5년) OVER (ORDER BY 일자) as prev_5y,
                LAG(국고채권10년) OVER (ORDER BY 일자) as prev_10y
            FROM govt_bond_rates
            WHERE 일자 >= '{start_date}' AND 일자 <= '{end_date}'
        )
        SELECT 
            일자,
            국고채권1년,
            국고채권3년,
            국고채권5년,
            국고채권10년,
            ROUND(국고채권1년 - prev_1y, 3) as daily_change_1y,
            ROUND(국고채권3년 - prev_3y, 3) as daily_change_3y,
            ROUND(국고채권5년 - prev_5y, 3) as daily_change_5y,
            ROUND(국고채권10년 - prev_10y, 3) as daily_change_10y
        FROM daily_changes
        ORDER BY 일자
        """

        return self.db.execute_custom_query(query, params)

    def find_peak_rates_period(self, window_size=30):
        """이동평균을 사용하여 금리가 가장 높았던 기간 찾기"""
        params = {
            "window": window_size,
            "start_date": "2022-01-01",
            "end_date": "2023-12-31",
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

    def analyze_rate_rise(self):
        """금리 상승 분석"""
        params = {
            "start_date": "2022-01-01",
            "end_date": "2023-12-31",
            "rise_threshold": 0.1,
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
            ROUND(국고채권1년 - prev_1y, 3) as rise_1y,
            ROUND(국고채권3년 - prev_3y, 3) as rise_3y,
            ROUND(국고채권5년 - prev_5y, 3) as rise_5y
        FROM rate_changes
        WHERE (국고채권1년 - prev_1y > {rise_threshold})
           OR (국고채권3년 - prev_3y > {rise_threshold})
           OR (국고채권5년 - prev_5y > {rise_threshold})
        ORDER BY 일자
        """

        return self.db.execute_custom_query(query, params)


def main():
    try:
        analyzer = InflationPeriodAnalysis()

        # 1. 전체 기간 데이터 조회
        print("2022-2023년 국고채 금리 데이터 조회 중...")
        inflation_rates = analyzer.get_inflation_period_rates()
        if not inflation_rates.empty:
            print("\n기간별 국고채 금리:")
            print(inflation_rates.head())
        else:
            print("해당 기간의 데이터가 없습니다.")

        # 2. 금리가 가장 높았던 기간 찾기
        print("\n금리 최고점 기간 분석 중...")
        peak_rates = analyzer.find_peak_rates_period()
        if not peak_rates.empty:
            max_rate_row = peak_rates.loc[peak_rates["MA_3Y"].idxmax()]
            print(f"3년물 기준 최고 금리 기록일: {max_rate_row['일자']}")
            print(f"해당 시점 3년물 금리: {max_rate_row['국고채권3년']:.3f}%")
            print(f"30일 이동평균: {max_rate_row['MA_3Y']:.3f}%")
        else:
            print("해당 기간의 데이터가 없습니다.")

        # 3. 급격한 금리 상승 기간 분석
        print("\n주요 금리 상승 시점 분석 중...")
        rate_rises = analyzer.analyze_rate_rise()
        if not rate_rises.empty:
            print("\n10bp 이상 상승한 날짜 및 상승폭:")
            print(rate_rises)

            # 최대 상승 시점 찾기
            max_rise_1y = rate_rises.loc[rate_rises["rise_1y"].idxmax()]
            max_rise_3y = rate_rises.loc[rate_rises["rise_3y"].idxmax()]
            print(f"\n최대 상승 시점:")
            print(f"1년물: {max_rise_1y['일자']} ({max_rise_1y['rise_1y']}%p)")
            print(f"3년물: {max_rise_3y['일자']} ({max_rise_3y['rise_3y']}%p)")
        else:
            print("큰 폭의 금리 상승이 없었습니다.")

    except Exception as e:
        print(f"분석 중 오류 발생: {str(e)}")
        import traceback

        print(traceback.format_exc())


if __name__ == "__main__":
    main()
