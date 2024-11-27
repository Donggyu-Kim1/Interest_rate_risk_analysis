import pandas as pd
import numpy as np
from datetime import datetime
from src.utils.data_loader import (
    load_bond_info,
    load_spread_data,
    load_all_bond_data,
)
from src.analysis.pv01_analysis import PV01Analysis


class WorstScenarioAnalysis:
    def __init__(self):
        self.pv01_analyzer = PV01Analysis()
        self.bond_info = load_bond_info()
        self.bond_spreads = load_spread_data()
        self.market_data = load_all_bond_data()

    def apply_rate_shock(self):
        """Bad 시나리오와 동일한 금리 충격 적용"""
        results = []
        pv01_results = self.pv01_analyzer.calculate_portfolio_pv01()

        for _, bond in self.bond_info.iterrows():
            maturity = float(bond["발행시만기"])

            # Bad 시나리오와 동일한 금리 충격
            if maturity <= 2:
                rate_shock = 0.01  # 100bp
            elif maturity <= 5:
                rate_shock = 0.0075  # 75bp
            else:
                rate_shock = 0.005  # 50bp

            bond_pv01 = pv01_results[pv01_results["종목명"] == bond["종목명"]][
                "PV01"
            ].iloc[0]
            rate_loss = bond_pv01 * (rate_shock * 10000)

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

    def analyze_severe_credit_crisis(self):
        """심각한 신용경색 상황의 스프레드 확대 분석"""
        results = []

        for _, bond in self.bond_info.iterrows():
            maturity = float(bond["발행시만기"])

            # 극단적 신용경색 상황의 스프레드 확대
            if maturity <= 2:
                spread_widening = np.random.uniform(0.006, 0.008)  # 60-80bp
            elif maturity <= 5:
                spread_widening = np.random.uniform(0.010, 0.012)  # 100-120bp
            else:
                spread_widening = np.random.uniform(0.015, 0.018)  # 150-180bp

            current_spread = self.bond_spreads[
                self.bond_spreads["종목명"] == bond["종목명"]
            ]["스프레드"].iloc[-1]

            # 심화된 유동성 프리미엄 (시장 경색 반영)
            base_liquidity_premium = (maturity / 10) * 0.004  # 기본 유동성 프리미엄
            market_stress_factor = 1 + (
                current_spread * 0.1
            )  # 현재 스프레드가 높을수록 스트레스 가중
            liquidity_premium = base_liquidity_premium * market_stress_factor

            total_spread_widening = spread_widening + liquidity_premium

            # 신용리스크로 인한 채권가치 하락 계산
            credit_impact = bond["발행액"] * total_spread_widening

            # 유동성 부족으로 인한 추가 할인율 적용
            illiquidity_discount = 0.05 + (maturity / 20)  # 5%~10% 할인
            total_impact = credit_impact * (1 + illiquidity_discount)

            results.append(
                {
                    "종목명": bond["종목명"],
                    "만기": maturity,
                    "현재스프레드(bp)": current_spread * 10000,
                    "스프레드확대(bp)": spread_widening * 10000,
                    "유동성프리미엄(bp)": liquidity_premium * 10000,
                    "할인율": illiquidity_discount,
                    "신용리스크손실": credit_impact,
                    "총손실": total_impact,
                }
            )

        return pd.DataFrame(results)

    def calculate_crisis_impact(self):
        """신용위기 상황의 복합 효과 분석"""
        rate_impact = self.apply_rate_shock()
        credit_impact = self.analyze_severe_credit_crisis()

        total_results = pd.merge(
            rate_impact,
            credit_impact[
                ["종목명", "신용리스크손실", "유동성프리미엄(bp)", "할인율", "총손실"]
            ],
            on="종목명",
        )

        # 신용위기 상황의 강화된 상호작용 효과 (30% 가정)
        total_results["상호작용효과"] = (
            total_results["금리충격손실"] * total_results["신용리스크손실"] * 0.3
        )

        # 부도위험 가중치 계산 (만기와 현재 스프레드 수준 반영)
        total_results["부도위험가중치"] = total_results.apply(
            lambda x: 1 + (x["만기"] / 5) * (1 + x["할인율"]), axis=1
        )

        # 최종 손실 계산
        total_results["최종위험조정손실"] = (
            total_results["금리충격손실"]
            + total_results["총손실"]
            + total_results["상호작용효과"]
        ) * total_results["부도위험가중치"]

        return total_results

    def analyze_crisis_progression(self, periods=[3, 6, 12]):
        """신용위기 진행 과정 분석"""
        base_results = self.calculate_crisis_impact()
        crisis_results = []

        for period in periods:
            # 신용위기 진행에 따른 비선형적 악화
            intensity_factor = 1 + (period / 12) * 0.6  # 연간 60% 악화

            # 만기별 차별적 악화 반영
            period_result = base_results.copy()
            period_result["기간(월)"] = period
            period_result["위기강도"] = intensity_factor

            # 만기가 길수록 더 큰 악화 가정
            period_result["만기조정위기강도"] = period_result.apply(
                lambda x: intensity_factor * (1 + (x["만기"] / 10) * 0.2), axis=1
            )

            period_result["기간별조정손실"] = (
                period_result["최종위험조정손실"] * period_result["만기조정위기강도"]
            )

            crisis_results.append(period_result)

        return pd.concat(crisis_results, ignore_index=True)


def run_worst_case_analysis():
    analysis = WorstScenarioAnalysis()

    # 1. 금리 충격 영향 (Bad 시나리오와 동일)
    rate_impact = analysis.apply_rate_shock()
    print("\n금리 충격 영향 분석:")
    print(rate_impact)

    # 2. 심각한 신용위기 영향
    credit_impact = analysis.analyze_severe_credit_crisis()
    print("\n신용위기 영향 분석:")
    print(credit_impact)

    # 3. 복합 위기 효과 분석
    total_impact = analysis.calculate_crisis_impact()
    print("\n복합 위기 효과 분석:")
    print(total_impact)

    # 4. 위기 진행 분석
    crisis_analysis = analysis.analyze_crisis_progression()
    print("\n위기 진행 분석:")
    print(crisis_analysis)

    return {
        "rate_impact": rate_impact,
        "credit_impact": credit_impact,
        "total_impact": total_impact,
        "crisis_analysis": crisis_analysis,
    }


if __name__ == "__main__":
    results = run_worst_case_analysis()
