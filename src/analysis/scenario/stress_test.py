import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple
from datetime import datetime
from src.utils.data_loader import load_bond_info, load_individual_bond_data
from src.analysis.pv01_analysis import PV01Analysis


@dataclass
class HistoricalScenario:
    name: str
    period: Tuple[str, str]
    rate_changes: Dict[str, Dict[str, float]]
    description: str


class HistoricalStressTest:
    def __init__(self):
        """
        PV01Analysis 클래스를 활용하여 더 정확한 PV01 계산 구현
        """
        self.bond_data = load_bond_info()
        self.pv01_analyzer = PV01Analysis()
        self.scenarios = self._define_historical_scenarios()
        self.pv01_results = self.pv01_analyzer.calculate_portfolio_pv01()

    def _define_historical_scenarios(self) -> Dict[str, HistoricalScenario]:
        """역사적 스트레스 시나리오 정의"""
        return {
            "covid_crisis": HistoricalScenario(
                name="코로나 위기",
                period=("2020-02-28", "2020-08-27"),
                rate_changes={
                    "급락기": {  # 2020년 2월 28일 기준
                        1.0: -0.041,  # 1년물
                        2.0: -0.065,  # 2년물
                        2.99: -0.090,  # 3년물
                        3.0: -0.090,  # 3년물
                        5.0: -0.110,  # 5년물
                        10.0: -0.110,  # 10년물
                    },
                    "최저점": {  # 2020년 8월 27일 기준
                        1.0: 0.680,  # 1년물
                        2.0: 0.766,  # 2년물
                        2.99: 0.852,  # 3년물
                        3.0: 0.852,  # 3년물
                        5.0: 1.102,  # 5년물
                        10.0: 1.102,  # 10년물
                    },
                },
                description="코로나19 팬데믹으로 인한 금리 급락 시기",
            ),
            "inflation_shock": HistoricalScenario(
                name="인플레이션 충격 및 유동성(레고렌드) 위기",
                period=("2022-09-26", "2022-11-08"),
                rate_changes={
                    "급등기": {  # 2022년 9월 26일 기준
                        1.0: 0.262,  # 1년물
                        2.0: 0.305,  # 2년물
                        2.99: 0.349,  # 3년물
                        3.0: 0.349,  # 3년물
                        5.0: 0.370,  # 5년물
                        10.0: 0.370,  # 10년물
                    },
                    "최고점": {  # 2022년 11월 8일 기준
                        1.0: 4.256,  # 1년물
                        2.0: 4.206,  # 2년물
                        2.99: 4.156,  # 3년물
                        3.0: 4.156,  # 3년물
                        5.0: 4.178,  # 5년물
                        10.0: 4.178,  # 10년물
                    },
                },
                description="2022년 하반기 인플레이션 대응 급격한 금리 인상기",
            ),
        }

    def get_current_market_data(self, bond_series: str) -> float:
        """개별 채권의 현재 시장 수익률 조회"""
        bond_data = load_individual_bond_data(bond_series)
        latest_data = bond_data[bond_data["일자"] == bond_data["일자"].max()]
        return latest_data["채권평가사 평균수익률_수익률"].iloc[0]

    def run_stress_test(self) -> pd.DataFrame:
        """스트레스 테스트 실행"""
        results = []

        for scenario_id, scenario in self.scenarios.items():
            for phase, rate_changes in scenario.rate_changes.items():
                for _, bond in self.bond_data.iterrows():
                    maturity_group = float(bond["만기그룹"].replace("년", ""))

                    if maturity_group in rate_changes:
                        rate_change = rate_changes[maturity_group]
                        series_code = bond["종목명"].split("우리금융지주")[1]

                        # PV01 가져오기
                        bond_pv01 = self.pv01_results[
                            self.pv01_results["종목명"] == bond["종목명"]
                        ]["PV01"].iloc[0]

                        # 현재 시장 수익률 가져오기
                        bond_data = load_individual_bond_data(series_code)
                        latest_yield = bond_data.iloc[0]["채권평가사 평균수익률_수익률"]

                        # 손실액 계산 (금리 상승 시 손실이 발생하므로 음수 부호 사용)
                        loss = -bond_pv01 * abs(rate_change) * 10000  # bp 단위로 변환

                        results.append(
                            {
                                "시나리오": scenario.name,
                                "국면": phase,
                                "기준일자": (
                                    scenario.period[0]
                                    if phase.endswith("기")
                                    else scenario.period[1]
                                ),
                                "종목명": bond["종목명"],
                                "만기그룹": bond["만기그룹"],
                                "발행액": bond["발행액"],
                                "금리변동(bp)": rate_change * 100,
                                "PV01": bond_pv01,
                                "손실액": loss,
                                "손실률(%)": (loss / bond["발행액"]) * 100,
                                "채권수익률": latest_yield,
                            }
                        )

        return pd.DataFrame(results)

    def analyze_results(
        self, results: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """스트레스 테스트 결과 분석"""
        # 시나리오별 총계 분석
        scenario_summary = (
            results.groupby(["시나리오", "국면"])
            .agg(
                {
                    "손실액": ["sum", "min", "max"],
                    "손실률(%)": ["mean", "min", "max"],
                    "금리변동(bp)": "mean",
                    "채권수익률": "mean",
                }
            )
            .round(2)
        )

        # 만기그룹별 취약성 분석
        maturity_analysis = (
            results.groupby(["만기그룹", "시나리오"])
            .agg(
                {
                    "손실액": ["sum", "mean"],
                    "손실률(%)": "mean",
                    "PV01": "sum",
                    "채권수익률": "mean",
                }
            )
            .round(2)
        )

        # 개별 종목 분석
        bond_analysis = (
            results.groupby(["종목명"])
            .agg(
                {
                    "손실액": ["mean", "min", "max"],
                    "손실률(%)": ["mean", "min", "max"],
                    "PV01": "first",
                    "채권수익률": "first",
                }
            )
            .round(2)
        )

        return scenario_summary, maturity_analysis, bond_analysis

    def generate_report(self, results: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """스트레스 테스트 보고서 생성"""
        scenario_summary, maturity_analysis, bond_analysis = self.analyze_results(
            results
        )

        report = {
            "상세 결과": results,
            "시나리오별 요약": scenario_summary,
            "만기그룹별 취약성": maturity_analysis,
            "개별 종목 분석": bond_analysis,
        }

        return report


def main():
    # 스트레스 테스트 실행
    stress_test = HistoricalStressTest()
    results = stress_test.run_stress_test()
    report = stress_test.generate_report(results)

    # 결과 출력
    for title, df in report.items():
        print(f"\n[{title}]")
        print(df)


if __name__ == "__main__":
    main()
