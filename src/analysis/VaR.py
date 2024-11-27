import numpy as np
import pandas as pd
from scipy import stats
from dataclasses import dataclass
from typing import Dict, Tuple, List, NamedTuple
from src.utils.db_queries import WooriBondDB


@dataclass
class VaRAnalysisResult:
    """확장된 VaR 분석 결과 클래스"""

    position_size: float
    current_value: float
    var_95: float
    var_99: float
    remaining_maturity: float
    expected_shortfall_95: float
    expected_shortfall_99: float
    var_95_pct: float
    var_99_pct: float
    es_95_pct: float
    es_99_pct: float
    simulated_returns: np.ndarray  # 시뮬레이션 결과 저장
    normality_test: Tuple[float, float]  # (통계량, p-value)
    distribution_params: Dict  # 분포 파라미터


class MonteCarloVaRAnalysis:
    def __init__(self):
        self.db = WooriBondDB()

    def get_portfolio_data(self) -> Tuple[pd.DataFrame, np.ndarray]:
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
        WHERE w.일자 >= DATE_SUB(CURRENT_DATE, INTERVAL 1 YEAR)
        ORDER BY w.일자, w.종목명
        """
        data = self.db.execute_custom_query(query)

        # 피벗 테이블로 변환하여 모든 채권의 수익률을 동일한 날짜에 맞춤
        data["trade_date"] = pd.to_datetime(data["trade_date"])
        pivot_prices = data.pivot(
            index="trade_date", columns="bond_name", values="price"
        )

        # 수익률 계산 및 결측치 처리
        returns = pivot_prices.pct_change().fillna(0)

        # 넘파이 배열로 변환
        returns_matrix = returns.values.T

        return data, returns_matrix

    def fit_distribution(self, returns: np.ndarray) -> Tuple[Dict, Tuple[float, float]]:
        """수익률 분포 적합 및 정규성 검정"""
        # 정규성 검정
        normality_test = stats.normaltest(returns)

        # 분포 파라미터 추정
        if normality_test[1] < 0.05:  # 정규성 기각
            df, loc, scale = stats.t.fit(returns)
            params = {"distribution": "t", "df": df, "loc": loc, "scale": scale}
        else:
            mu, std = stats.norm.fit(returns)
            params = {"distribution": "normal", "mu": mu, "std": std}

        return params, normality_test

    def calculate_individual_var(
        self,
        returns: np.ndarray,
        position_size: float,
        current_price: float,
        remaining_maturity: float,
        n_simulations: int = 10000,
        horizon_days: int = 10,
    ) -> VaRAnalysisResult:
        """개별 채권 VaR 분석"""
        # 분포 적합 및 검정
        dist_params, normality_test = self.fit_distribution(returns)

        mean_return = np.mean(returns)
        std_return = np.std(returns)

        # t-분포 사용 (정규성 검정 실패를 고려)
        df = 5  # 자유도
        simulated_returns = stats.t.rvs(
            df=df,
            loc=mean_return * horizon_days,
            scale=std_return * np.sqrt(horizon_days),
            size=n_simulations,
        )

        # 포트폴리오 가치 계산
        current_value = current_price * position_size
        simulated_values = current_price * (1 + simulated_returns) * position_size

        # VaR & ES 계산 (절대값으로 변환)
        var_95 = abs(current_value - np.percentile(simulated_values, 5))
        var_99 = abs(current_value - np.percentile(simulated_values, 1))

        cutoff_95 = np.percentile(simulated_values, 5)
        cutoff_99 = np.percentile(simulated_values, 1)
        es_95 = abs(
            current_value - np.mean(simulated_values[simulated_values <= cutoff_95])
        )
        es_99 = abs(
            current_value - np.mean(simulated_values[simulated_values <= cutoff_99])
        )

        return VaRAnalysisResult(
            position_size=position_size,
            current_value=current_value,
            var_95=var_95,
            var_99=var_99,
            remaining_maturity=remaining_maturity,
            expected_shortfall_95=es_95,
            expected_shortfall_99=es_99,
            var_95_pct=(var_95 / current_value) * 100,
            var_99_pct=(var_99 / current_value) * 100,
            es_95_pct=(es_95 / current_value) * 100,
            es_99_pct=(es_99 / current_value) * 100,
            simulated_returns=simulated_returns,
            normality_test=normality_test,
            distribution_params=dist_params,
        )

    def calculate_portfolio_var(
        self,
        returns_matrix: np.ndarray,
        positions: np.ndarray,
        n_simulations: int = 10000,
        horizon_days: int = 10,
    ) -> Tuple[float, float, np.ndarray]:
        """포트폴리오 VaR 계산 (상관관계 고려)"""
        # 결측치 제거
        returns_matrix = np.nan_to_num(returns_matrix, 0)

        # 최소 관측치 확인
        if returns_matrix.shape[1] < 2:
            raise ValueError("Insufficient observations for covariance calculation")

        # 공분산 행렬 계산 및 안정화
        cov_matrix = np.cov(returns_matrix) + np.eye(returns_matrix.shape[0]) * 1e-6

        try:
            chol_matrix = np.linalg.cholesky(cov_matrix)
        except np.linalg.LinAlgError:
            # 대각 행렬로 대체
            chol_matrix = np.diag(np.sqrt(np.diag(cov_matrix)))

        # 시뮬레이션
        n_assets = len(positions)
        random_numbers = np.random.standard_normal((n_assets, n_simulations))
        correlated_returns = np.dot(chol_matrix, random_numbers)

        # 포트폴리오 수익률 계산
        weights = positions / np.sum(positions)
        portfolio_returns = np.dot(weights, correlated_returns)

        # 유효한 값만 사용하여 VaR/ES 계산
        valid_returns = portfolio_returns[~np.isnan(portfolio_returns)]
        if len(valid_returns) == 0:
            return 0.0, 0.0, np.zeros(n_simulations)

        portfolio_value = np.sum(positions)
        var_95 = abs(np.percentile(valid_returns, 5)) * portfolio_value
        es_95 = (
            abs(
                np.mean(valid_returns[valid_returns <= np.percentile(valid_returns, 5)])
            )
            * portfolio_value
        )

        return var_95, es_95, portfolio_returns

    def analyze_portfolio(
        self, n_simulations: int = 10000, horizon_days: int = 10
    ) -> Dict:
        """전체 포트폴리오 분석 실행"""
        # 데이터 조회
        data, returns_matrix = self.get_portfolio_data()

        # 개별 채권 분석
        individual_results = {}
        positions = []

        for bond_name in data["bond_name"].unique():
            bond_data = data[data["bond_name"] == bond_name].iloc[-1]
            returns = (
                data[data["bond_name"] == bond_name]["price"]
                .pct_change()
                .dropna()
                .values
            )

            result = self.calculate_individual_var(
                returns=returns,
                position_size=bond_data["issue_amount"],
                current_price=bond_data["price"],
                remaining_maturity=bond_data["remaining_maturity"],
                n_simulations=n_simulations,
                horizon_days=horizon_days,
            )

            individual_results[bond_name] = result
            positions.append(bond_data["issue_amount"])

        # 포트폴리오 VaR 계산
        positions = np.array(positions)
        portfolio_var, portfolio_es, portfolio_returns = self.calculate_portfolio_var(
            returns_matrix=returns_matrix,
            positions=positions,
            n_simulations=n_simulations,
            horizon_days=horizon_days,
        )

        return {
            "individual_results": individual_results,
            "portfolio_var": portfolio_var,
            "portfolio_es": portfolio_es,
            "portfolio_returns": portfolio_returns,
            "returns_matrix": returns_matrix,
            "positions": positions,
            "bond_names": list(individual_results.keys()),
        }


def main():
    analyzer = MonteCarloVaRAnalysis()
    results = analyzer.analyze_portfolio()

    # 결과 출력
    print("\n=== 개별 채권 VaR 분석 결과 ===")
    for bond_name, result in results["individual_results"].items():
        print(f"\n{bond_name}:")
        print(f"VaR (95%): {result.var_95_pct:.2f}%")
        print(f"ES (95%): {result.es_95_pct:.2f}%")
        print(f"정규성 검정 p-value: {result.normality_test[1]:.4f}")

    print("\n=== 포트폴리오 VaR 분석 결과 ===")
    portfolio_value = np.sum(results["positions"])
    print(f"Portfolio VaR (95%): {(results['portfolio_var']/portfolio_value)*100:.2f}%")
    print(f"Portfolio ES (95%): {(results['portfolio_es']/portfolio_value)*100:.2f}%")


if __name__ == "__main__":
    main()
