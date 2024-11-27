import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class MarketEnvironmentAnalysis:
    def __init__(self):
        self.govt_bond_data = pd.read_csv(
            "data/processed/market_data/govt_bond_rates.csv"
        )
        self.spread_data = pd.read_csv(
            "data/processed/spread_data/woori_bond_spreads.csv"
        )
        self.bond_info = pd.read_csv("data/processed/bond_info/woori_bond_info.csv")

        # 날짜 컬럼 datetime 변환
        self.govt_bond_data["일자"] = pd.to_datetime(self.govt_bond_data["일자"])
        self.spread_data["일자"] = pd.to_datetime(self.spread_data["일자"])

    def analyze_yield_curve(self, dates=None):
        """국고채 금리 곡선 분석"""
        if dates is None:
            # 최근 3개 시점 선택
            dates = sorted(self.govt_bond_data["일자"].unique())[-3:]

        yield_curves = {}
        tenors = ["국고채권(1년)", "국고채권(3년)", "국고채권(5년)", "국고채권(10년)"]

        for date in dates:
            daily_data = self.govt_bond_data[self.govt_bond_data["일자"] == date]
            yield_curves[date] = daily_data[tenors].iloc[0]

        return pd.DataFrame(yield_curves).T

    def analyze_credit_spreads(self):
        """신용스프레드 분석"""
        # 만기그룹별 평균 스프레드 계산
        maturity_spreads = self.spread_data.merge(
            self.bond_info[["종목명", "만기그룹"]], on="종목명"
        )

        spread_analysis = (
            maturity_spreads.groupby(["일자", "만기그룹"])["스프레드"]
            .mean()
            .reset_index()
        )

        # 피봇 테이블 생성
        spread_pivot = spread_analysis.pivot(
            index="일자", columns="만기그룹", values="스프레드"
        )

        return spread_pivot

    def analyze_rate_volatility(self, window=20):
        """금리 변동성 분석"""
        # 주요 만기별 금리 변동성 계산
        tenors = ["국고채권(1년)", "국고채권(3년)", "국고채권(5년)", "국고채권(10년)"]

        volatility_df = pd.DataFrame()
        for tenor in tenors:
            # 일간 변화율 계산
            daily_changes = self.govt_bond_data[tenor].pct_change()

            # 이동 표준편차 계산 (연율화)
            volatility = daily_changes.rolling(window=window).std() * np.sqrt(252)
            volatility_df[f"{tenor}_변동성"] = volatility

        volatility_df.index = self.govt_bond_data["일자"]

        return volatility_df

    def get_latest_market_snapshot(self):
        """최신 시장 상황 요약"""
        latest_date = self.govt_bond_data["일자"].max()

        # 최신 국고채 금리
        latest_rates = self.govt_bond_data[
            self.govt_bond_data["일자"] == latest_date
        ].iloc[0]

        # 최신 스프레드
        latest_spreads = (
            self.spread_data[self.spread_data["일자"] == latest_date]
            .groupby("종목명")["스프레드"]
            .mean()
        )

        # 최근 20일 변동성
        latest_vol = self.analyze_rate_volatility().iloc[-1]

        return {
            "latest_date": latest_date,
            "govt_rates": latest_rates,
            "credit_spreads": latest_spreads,
            "volatility": latest_vol,
        }


if __name__ == "__main__":
    analysis = MarketEnvironmentAnalysis()

    # 분석 실행
    yield_curves = analysis.analyze_yield_curve()
    spreads = analysis.analyze_credit_spreads()
    volatility = analysis.analyze_rate_volatility()
    market_snapshot = analysis.get_latest_market_snapshot()

    print("\n=== 시장 환경 분석 결과 ===")
    print(f"\n[분석 기준일] {market_snapshot['latest_date'].strftime('%Y-%m-%d')}")

    print("\n[금리 곡선]")
    print(
        yield_curves.tail(1)[
            ["국고채권(1년)", "국고채권(3년)", "국고채권(5년)", "국고채권(10년)"]
        ].round(3)
    )

    print("\n[신용스프레드 (만기그룹별 평균, bp)]")
    latest_spreads = spreads.tail(1).round(3)
    for col in latest_spreads.columns:
        print(f"만기 {col}: {latest_spreads[col].values[0]*100:.1f}bp")

    print("\n[주요 만기 금리 변동성 (연율화)]")
    latest_vol = volatility.tail(1).round(4) * 100
    for col in latest_vol.columns:
        tenor = col.replace("_변동성", "")
        print(f"{tenor}: {latest_vol[col].values[0]:.2f}%")

    print("\nAnalysis completed")
