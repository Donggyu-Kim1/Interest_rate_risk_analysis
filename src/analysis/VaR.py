from src.utils.db_queries import WooriBondDB
from dataclasses import dataclass
from typing import Dict, Tuple
import pandas as pd
import numpy as np
from scipy import stats


@dataclass
class VaRResult:
    """VaR 분석 결과를 저장하는 데이터 클래스"""

    position_size: float
    current_value: float
    var_95: float
    var_99: float
    remaining_maturity: float
    expected_shortfall_95: float
    expected_shortfall_99: float
    var_95_pct: float  # 포지션 대비 VaR 비율
    var_99_pct: float
    es_95_pct: float  # 포지션 대비 ES 비율
    es_99_pct: float


class MonteCarloVaRAnalysis:
    def __init__(self):
        self.db = WooriBondDB()

    def get_bond_market_data(self):
        """채권 시장 데이터 조회"""
        query = """
        SELECT 
            w.일자 as trade_date,
            w.종목명 as bond_name,
            w.평균가격 as price,
            w.평균수익률 as yield,
            b.발행액 as issue_amount,
            b.잔존만기 as remaining_maturity
        FROM woori_bond_data w
        JOIN bond_info b ON w.종목명 = b.종목명
        ORDER BY w.일자, w.종목명
        """
        return self.db.execute_custom_query(query)

    def get_bond_returns(self, data: pd.DataFrame) -> pd.DataFrame:
        """채권별 일별 수익률 계산"""
        df = data.copy()
        df["daily_return"] = df.groupby("bond_name")["price"].pct_change()
        return df.dropna()

    def calculate_var_metrics(
        self,
        bond_data: pd.DataFrame,
        n_simulations: int = 10000,
        horizon_days: int = 10,
    ) -> VaRResult:
        """
        채권별 VaR 및 Expected Shortfall 계산

        Args:
            bond_data: 단일 채권의 시계열 데이터
            n_simulations: 시뮬레이션 횟수
            horizon_days: 예측 기간 (일)

        Returns:
            VaRResult: VaR 분석 결과
        """
        # 기초 통계량 계산
        mean_return = bond_data["daily_return"].mean()
        std_return = bond_data["daily_return"].std()
        current_price = bond_data["price"].iloc[-1]
        position_size = bond_data["issue_amount"].iloc[-1]
        current_value = current_price * position_size

        # 정규성 검정 및 분포 선택
        _, p_value = stats.normaltest(bond_data["daily_return"])

        if p_value < 0.05:
            # 정규성 기각시 t-분포 사용
            degrees_of_freedom = 5
            simulated_returns = stats.t.rvs(
                df=degrees_of_freedom,
                loc=mean_return * horizon_days,
                scale=std_return * np.sqrt(horizon_days),
                size=n_simulations,
            )
        else:
            # 정규성 채택시 정규분포 사용
            simulated_returns = np.random.normal(
                mean_return * horizon_days,
                std_return * np.sqrt(horizon_days),
                n_simulations,
            )

        # 포트폴리오 가치 시뮬레이션
        simulated_prices = current_price * (1 + simulated_returns)
        portfolio_values = simulated_prices * position_size

        # VaR 계산
        var_95 = current_price * position_size - np.percentile(portfolio_values, 5)
        var_99 = current_price * position_size - np.percentile(portfolio_values, 1)

        # Expected Shortfall 계산
        cutoff_95 = np.percentile(portfolio_values, 5)
        cutoff_99 = np.percentile(portfolio_values, 1)
        es_95 = -np.mean(portfolio_values[portfolio_values <= cutoff_95])
        es_99 = -np.mean(portfolio_values[portfolio_values <= cutoff_99])

        # 비율 계산
        var_95_pct = (var_95 / current_value) * 100
        var_99_pct = (var_99 / current_value) * 100
        es_95_pct = (abs(es_95) / current_value) * 100
        es_99_pct = (abs(es_99) / current_value) * 100

        return VaRResult(
            position_size=position_size,
            current_value=current_value,
            var_95=var_95,
            var_99=var_99,
            remaining_maturity=bond_data["remaining_maturity"].iloc[-1],
            expected_shortfall_95=es_95,
            expected_shortfall_99=es_99,
            var_95_pct=var_95_pct,
            var_99_pct=var_99_pct,
            es_95_pct=es_95_pct,
            es_99_pct=es_99_pct,
        )

    def analyze_portfolio(
        self, n_simulations: int = 10000, horizon_days: int = 10
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        전체 포트폴리오 VaR 분석 수행

        Args:
            n_simulations: 시뮬레이션 횟수
            horizon_days: 예측 기간 (일)

        Returns:
            Tuple[pd.DataFrame, pd.DataFrame]: (개별 채권 분석 결과, 만기별 그룹 분석 결과)
        """
        # 데이터 조회 및 전처리
        data = self.get_bond_market_data()
        data = self.get_bond_returns(data)

        # 채권별 VaR 분석
        results = {}
        for bond_name in data["bond_name"].unique():
            bond_data = data[data["bond_name"] == bond_name]
            results[bond_name] = self.calculate_var_metrics(
                bond_data, n_simulations, horizon_days
            )

        # 분석 결과 DataFrame 생성
        summary = pd.DataFrame(
            [
                {
                    "Bond": bond,
                    "Position Size": result.position_size,
                    "Current Value": result.current_value,
                    "VaR_95": result.var_95,
                    "VaR_99": result.var_99,
                    "ES_95": result.expected_shortfall_95,
                    "ES_99": result.expected_shortfall_99,
                    "VaR_95_pct": result.var_95_pct,
                    "VaR_99_pct": result.var_99_pct,
                    "ES_95_pct": result.es_95_pct,
                    "ES_99_pct": result.es_99_pct,
                    "Remaining Maturity": result.remaining_maturity,
                }
                for bond, result in results.items()
            ]
        )

        # 만기별 그룹화 (observed=True 추가)
        maturity_groups = summary.groupby(
            pd.cut(
                summary["Remaining Maturity"],
                bins=[0, 1, 3, 5, 10],
                labels=["0-1Y", "1-3Y", "3-5Y", "5-10Y"],
            ),
            observed=True,
        ).agg(
            {
                "Position Size": "sum",
                "Current Value": "sum",
                "VaR_95": "sum",
                "VaR_99": "sum",
                "ES_95": "sum",
                "ES_99": "sum",
            }
        )

        # 만기별 그룹에 대한 비율 계산 추가
        for group in maturity_groups.index:
            current_value = maturity_groups.loc[group, "Current Value"]
            maturity_groups.loc[group, "VaR_95_pct"] = (
                maturity_groups.loc[group, "VaR_95"] / current_value
            ) * 100
            maturity_groups.loc[group, "VaR_99_pct"] = (
                maturity_groups.loc[group, "VaR_99"] / current_value
            ) * 100
            maturity_groups.loc[group, "ES_95_pct"] = (
                abs(maturity_groups.loc[group, "ES_95"]) / current_value
            ) * 100
            maturity_groups.loc[group, "ES_99_pct"] = (
                abs(maturity_groups.loc[group, "ES_99"]) / current_value
            ) * 100

        return summary, maturity_groups


def main():
    """메인 실행 함수"""
    try:
        analyzer = MonteCarloVaRAnalysis()
        summary, maturity_groups = analyzer.analyze_portfolio(
            n_simulations=10000, horizon_days=10
        )

        pd.set_option("display.float_format", lambda x: "{:.2f}".format(x))

        print("\n=== 개별 채권 VaR 분석 결과 ===")
        print(
            summary[
                [
                    "Bond",
                    "Current Value",
                    "VaR_95",
                    "VaR_95_pct",
                    "VaR_99",
                    "VaR_99_pct",
                    "ES_95_pct",
                    "ES_99_pct",
                    "Remaining Maturity",
                ]
            ].to_string()
        )

        print("\n=== 만기별 그룹 VaR 분석 결과 ===")
        print(
            maturity_groups[
                [
                    "Current Value",
                    "VaR_95",
                    "VaR_95_pct",
                    "VaR_99",
                    "VaR_99_pct",
                    "ES_95_pct",
                    "ES_99_pct",
                ]
            ].to_string()
        )

    except Exception as e:
        print(f"분석 중 오류 발생: {e}")


if __name__ == "__main__":
    main()
