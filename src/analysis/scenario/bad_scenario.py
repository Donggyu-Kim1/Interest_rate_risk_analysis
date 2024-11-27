import pandas as pd
import numpy as np
from datetime import datetime
from src.utils.data_loader import (
    load_bond_info,
    load_spread_data,
    load_all_bond_data,
)
from src.analysis.pv01_analysis import PV01Analysis


class BadScenarioAnalysis:
    def __init__(self):
        self.pv01_analyzer = PV01Analysis()
        self.bond_info = load_bond_info()
        self.bond_spreads = load_spread_data()
        self.market_data = load_all_bond_data()

    def apply_rate_shock(self):
        """만기별 금리 충격 시나리오 적용"""
        results = []

        # PV01 계산
        pv01_results = self.pv01_analyzer.calculate_portfolio_pv01()

        for _, bond in self.bond_info.iterrows():
            maturity = float(bond["발행시만기"])

            # 만기별 금리 충격 크기 설정
            if maturity <= 2:
                rate_shock = 0.01  # 100bp
            elif maturity <= 5:
                rate_shock = 0.0075  # 75bp
            else:
                rate_shock = 0.005  # 50bp

            # 해당 채권의 PV01 데이터 찾기
            bond_pv01 = pv01_results[pv01_results["종목명"] == bond["종목명"]][
                "PV01"
            ].iloc[0]

            # 금리 충격으로 인한 손실 계산
            rate_loss = bond_pv01 * (rate_shock * 10000)  # bp 단위로 변환

            results.append(
                {
                    "종목명": bond["종목명"],
                    "만기": maturity,
                    "금리충격(bp)": rate_shock * 10000,
                    "PV01": bond_pv01,
                    "금리충격손실": rate_loss,
                }
            )

        return pd.DataFrame(results)

    def analyze_spread_widening(self):
        results = []
        pv01_results = self.pv01_analyzer.calculate_portfolio_pv01()

        for _, bond in self.bond_info.iterrows():
            maturity = float(bond["발행시만기"])

            # 스프레드 확대 폭 설정
            if maturity <= 2:
                spread_widening = np.random.uniform(20, 30)
            elif maturity <= 5:
                spread_widening = np.random.uniform(30, 40)
            else:
                spread_widening = np.random.uniform(40, 50)

            current_spread = (
                self.bond_spreads[self.bond_spreads["종목명"] == bond["종목명"]][
                    "스프레드"
                ].iloc[-1]
                * 100
            )

            # PV01 기반 손실 계산
            bond_pv01 = pv01_results[pv01_results["종목명"] == bond["종목명"]][
                "PV01"
            ].iloc[0]
            spread_loss = bond_pv01 * spread_widening

            results.append(
                {
                    "종목명": bond["종목명"],
                    "만기": maturity,
                    "현재스프레드(bp)": current_spread,
                    "스프레드확대(bp)": spread_widening,
                    "스프레드손실": spread_loss,
                }
            )

        return pd.DataFrame(results)

    def calculate_total_impact(self):
        """금리충격과 스프레드 확대의 복합 효과 분석"""
        rate_impact = self.apply_rate_shock()
        spread_impact = self.analyze_spread_widening()

        total_results = pd.merge(
            rate_impact, spread_impact[["종목명", "스프레드손실"]], on="종목명"
        )

        # 상호작용 효과 추정 (3% 가정)
        total_results["상호작용효과"] = (
            total_results["금리충격손실"] * total_results["스프레드손실"] * 0.03
        )

        # 총 손실 계산
        total_results["총손실"] = (
            total_results["금리충격손실"]
            + total_results["스프레드손실"]
            + total_results["상호작용효과"]
        )

        return total_results

    def analyze_time_progression(self, periods=[3, 6, 12]):
        """시간 경과에 따른 스트레스 강도 변화 분석"""
        base_results = self.calculate_total_impact()
        time_results = []

        for period in periods:
            # 기간별 스트레스 강도 조정 계수
            intensity_factor = 1 + (period / 12) * 0.2  # 연간 20% 강도 증가 가정

            period_result = base_results.copy()
            period_result["기간(월)"] = period
            period_result["스트레스강도"] = intensity_factor
            period_result["기간별총손실"] = period_result["총손실"] * intensity_factor

            time_results.append(period_result)

        return pd.concat(time_results, ignore_index=True)


def run_analysis():
    analysis = BadScenarioAnalysis()

    # 1. 금리 충격 영향
    rate_impact = analysis.apply_rate_shock()
    print("\n금리 충격 영향 분석:")
    print(rate_impact)

    # 2. 스프레드 확대 영향
    spread_impact = analysis.analyze_spread_widening()
    print("\n스프레드 확대 영향 분석:")
    print(spread_impact)

    # 3. 복합 효과 분석
    total_impact = analysis.calculate_total_impact()
    print("\n복합 효과 분석:")
    print(total_impact)

    # 4. 시계열 전개 분석
    time_analysis = analysis.analyze_time_progression()
    print("\n시계열 전개 분석:")
    print(time_analysis)

    return {
        "rate_impact": rate_impact,
        "spread_impact": spread_impact,
        "total_impact": total_impact,
        "time_analysis": time_analysis,
    }


if __name__ == "__main__":
    results = run_analysis()
