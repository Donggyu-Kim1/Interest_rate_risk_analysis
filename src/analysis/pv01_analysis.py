from datetime import datetime
import pandas as pd
from src.utils.data_loader import (
    load_bond_info,
    load_individual_bond_data,
)


class PV01Analysis:
    def __init__(self):
        self.bond_info = load_bond_info()
        self.analysis_date = datetime.now()

    def calculate_cashflows(self, bond):
        # 채권의 모든 미래 현금흐름(이자+원금) 계산
        start_date = bond["발행일"]
        end_date = bond["만기일"]
        payment_freq = bond["이자지급주기"]
        coupon_rate = bond["표면금리"] / 100
        principal = bond["발행액"]

        # 이자지급주기에 따라 payment_dates 생성
        payment_dates = pd.date_range(
            start=start_date, end=end_date, freq=f"{payment_freq}ME"
        )

        cashflows = []

        # 각 지급일의 이자금액 = 발행액 × (표면금리/연간 지급횟수)
        for date in payment_dates:
            cf = principal * (coupon_rate / (12 / payment_freq))
            # 만기일에는 이자 + 원금
            if date == end_date:
                cf += principal

            cashflows.append(
                {
                    "date": date,
                    "amount": cf,
                    "days_to_cf": (date - self.analysis_date).days,
                }
            )

        return pd.DataFrame(cashflows)

    def get_market_rate(self, bond_series):
        """채권 시리즈별 최신 시장금리 불러오기"""
        bond_data = load_individual_bond_data(bond_series)
        latest_data = bond_data[bond_data["일자"] == bond_data["일자"].max()]
        return latest_data["채권평가사 평균수익률_수익률"].iloc[0] / 100

    def calculate_pv01(self, cashflows, market_rate):
        """
        - 각 현금흐름의 현재가치 계산
        - 기본금리와 1bp 상승 금리 각각 계산
        - PV01 = -(충격 후 현재가치 - 기본 현재가치)
        """
        total_pv_base = 0
        total_pv_shock = 0
        shock = 0.0001  # 1bp

        for _, cf in cashflows.iterrows():
            t = cf["days_to_cf"] / 365
            if t > 0:
                pv_base = cf["amount"] / (1 + market_rate) ** t
                pv_shock = cf["amount"] / (1 + market_rate + shock) ** t

                total_pv_base += pv_base
                total_pv_shock += pv_shock

        return -(total_pv_shock - total_pv_base)

    def calculate_portfolio_pv01(self):
        results = []

        for _, bond in self.bond_info.iterrows():
            series_code = bond["종목명"].split("우리금융지주")[1]
            cashflows = self.calculate_cashflows(bond)
            market_rate = self.get_market_rate(series_code)
            pv01 = self.calculate_pv01(cashflows, market_rate)

            results.append(
                {
                    "종목명": bond["종목명"],
                    "만기": bond["발행시만기"],
                    "PV01": pv01,
                    "발행액": bond["발행액"],
                    "PV01_per_billion": pv01 / (bond["발행액"] / 1_000_000),
                }
            )

        return pd.DataFrame(results)


if __name__ == "__main__":
    analysis = PV01Analysis()
    results = analysis.calculate_portfolio_pv01()
    print("\nPV01 Analysis Results:")
    print(results)
