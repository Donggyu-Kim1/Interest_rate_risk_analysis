from datetime import datetime
import pandas as pd
import numpy as np
from src.analysis.pv01_analysis import PV01Analysis


class BaselineScenarioAnalysis:
    def __init__(self):
        self.pv01_analyzer = PV01Analysis()
        self.portfolio_pv01 = self.pv01_analyzer.calculate_portfolio_pv01()
        self.bond_info = self.pv01_analyzer.bond_info

    def calculate_rate_changes(self):
        """만기별 금리 인하 폭 설정"""
        rate_changes = []

        for _, bond in self.bond_info.iterrows():
            maturity = bond["발행시만기"]

            # 만기별 금리인하 폭 차등 적용
            if maturity <= 2:
                rate_change = -0.0025  # -25bp
            elif maturity <= 5:
                rate_change = -0.0020  # -20bp
            else:
                rate_change = -0.0015  # -15bp

            # 신용스프레드 축소 효과 추가 (-7bp)
            total_change = rate_change - 0.0007

            rate_changes.append(
                {
                    "종목명": bond["종목명"],
                    "만기": maturity,
                    "금리변동": total_change,
                    "금리변동(bp)": total_change * 10000,
                }
            )

        return pd.DataFrame(rate_changes)

    def calculate_price_changes(self):
        """금리 변동에 따른 가격 변화 계산"""
        rate_changes = self.calculate_rate_changes()
        results = []

        for _, row in self.portfolio_pv01.iterrows():
            bond_rate_change = rate_changes[rate_changes["종목명"] == row["종목명"]][
                "금리변동"
            ].iloc[0]

            # 1차 효과 (PV01)
            price_change_linear = -row["PV01"] * (bond_rate_change * 10000)

            # 컨벡서티 효과 (근사치: PV01 효과의 약 2~3% 추가)
            convexity_effect = price_change_linear * 0.025

            total_price_change = price_change_linear + convexity_effect
            price_change_ratio = (total_price_change / row["발행액"]) * 100

            results.append(
                {
                    "종목명": row["종목명"],
                    "만기": row["만기"],
                    "발행액": row["발행액"],
                    "PV01": row["PV01"],
                    "가격변화": total_price_change,
                    "수익률(%)": price_change_ratio,
                    "금리변동(bp)": bond_rate_change * 10000,
                }
            )

        return pd.DataFrame(results)

    def analyze_portfolio_impact(self):
        """포트폴리오 전체 영향 분석"""
        price_changes = self.calculate_price_changes()

        # 만기 그룹별 분석
        maturity_analysis = (
            price_changes.groupby("만기")
            .agg({"발행액": "sum", "가격변화": "sum", "수익률(%)": "mean"})
            .round(2)
        )

        # 전체 포트폴리오 영향
        total_impact = {
            "총 발행액": price_changes["발행액"].sum(),
            "총 가격변화": price_changes["가격변화"].sum(),
            "평균 수익률(%)": price_changes["수익률(%)"].mean(),
            "최대 수익률(%)": price_changes["수익률(%)"].max(),
            "최소 수익률(%)": price_changes["수익률(%)"].min(),
        }

        return {
            "detail": price_changes,
            "maturity_analysis": maturity_analysis,
            "total_impact": total_impact,
        }


def run_baseline_analysis():
    analyzer = BaselineScenarioAnalysis()
    results = analyzer.analyze_portfolio_impact()

    print("\n=== Baseline 시나리오 분석 결과 ===")
    print("\n1. 개별 채권 분석:")
    print(results["detail"].round(2))

    print("\n2. 만기별 분석:")
    print(results["maturity_analysis"])

    print("\n3. 포트폴리오 전체 영향:")
    for key, value in results["total_impact"].items():
        print(f"{key}: {value:,.2f}")

    return results


if __name__ == "__main__":
    results = run_baseline_analysis()
