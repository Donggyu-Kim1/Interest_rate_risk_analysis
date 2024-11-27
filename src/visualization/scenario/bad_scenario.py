import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
from src.utils.plot_config import (
    set_plot_style,
    COLOR_PALETTE,
    MATURITY_COLORS,
    format_percentage,
    save_plot,
)
from src.analysis.scenario.bad_scenario import BadScenarioAnalysis


class BadScenarioVisualization:
    def __init__(self, analysis=None):
        self.analysis = analysis if analysis else BadScenarioAnalysis()
        set_plot_style()

        self.project_root = Path(__file__).parent.parent.parent.parent
        self.output_dir = self.project_root / "docs" / "analysis" / "scenarios"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def visualize_rate_shock_scenario(self, save=True):
        """금리 충격 시나리오 설정 시각화"""
        fig, ax = plt.subplots(figsize=(12, 8))

        maturities = np.linspace(0, 10, 100)
        shocks = []

        for m in maturities:
            if m <= 2:
                shock = 100  # 100bp
            elif m <= 5:
                shock = 75  # 75bp
            else:
                shock = 50  # 50bp
            shocks.append(shock)

        ax.plot(maturities, shocks, "r-", linewidth=2)

        ax.axvspan(0, 2, alpha=0.2, color="red", label="2년 이하: 100bp")
        ax.axvspan(2, 5, alpha=0.2, color="yellow", label="2~5년: 75bp")
        ax.axvspan(5, 10, alpha=0.2, color="green", label="5년 초과: 50bp")

        ax.set_title("만기별 금리 충격 시나리오", pad=20, fontsize=14)
        ax.set_xlabel("만기(년)", fontsize=12)
        ax.set_ylabel("금리 충격(bp)", fontsize=12)
        ax.grid(True, linestyle="--", alpha=0.7)
        ax.legend()

        plt.tight_layout()

        if save:
            save_plot(fig, self.output_dir / "bad_rate_shock_scenario.png")
        return fig

    def plot_rate_impact(self, save=True):
        """금리 충격 영향 분석 시각화"""
        rate_impact = self.analysis.apply_rate_shock()

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 14))

        # 금리 충격 크기
        rate_impact = rate_impact.sort_values("만기")
        bars1 = ax1.bar(rate_impact["종목명"], rate_impact["금리충격(bp)"])

        ax1.set_title("채권별 금리 충격", pad=20, fontsize=14)
        ax1.set_xlabel("종목명", fontsize=12)
        ax1.set_ylabel("금리 충격(bp)", fontsize=12)
        ax1.tick_params(axis="x", rotation=45)
        ax1.grid(True, linestyle="--", alpha=0.7)

        # 손실 영향
        bars2 = ax2.bar(rate_impact["종목명"], rate_impact["금리충격손실"])

        ax2.set_title("채권별 금리충격 손실", pad=20, fontsize=14)
        ax2.set_xlabel("종목명", fontsize=12)
        ax2.set_ylabel("손실액(백만원)", fontsize=12)
        ax2.tick_params(axis="x", rotation=45)
        ax2.grid(True, linestyle="--", alpha=0.7)

        plt.tight_layout()

        if save:
            save_plot(fig, self.output_dir / "bad_rate_impact.png")
        return fig

    def plot_spread_impact(self, save=True):
        """스프레드 확대 영향 시각화"""
        spread_impact = self.analysis.analyze_spread_widening()

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 14))

        spread_impact = spread_impact.sort_values("만기")

        # 현재 vs 확대 스프레드
        width = 0.35
        x = np.arange(len(spread_impact))

        ax1.bar(
            x - width / 2,
            spread_impact["현재스프레드(bp)"],
            width,
            label="현재",
            color="blue",
        )
        ax1.bar(
            x + width / 2,
            spread_impact["스프레드확대(bp)"],
            width,
            label="확대",
            color="red",
        )

        ax1.set_title("채권별 스프레드 변화", pad=20, fontsize=14)
        ax1.set_xticks(x)
        ax1.set_xticklabels(spread_impact["종목명"], rotation=45)
        ax1.set_ylabel("스프레드(bp)", fontsize=12)
        ax1.legend()
        ax1.grid(True, linestyle="--", alpha=0.7)

        # 손실 영향
        ax2.bar(spread_impact["종목명"], spread_impact["스프레드손실"])
        ax2.set_title("스프레드 확대로 인한 손실", pad=20, fontsize=14)
        ax2.set_xlabel("종목명", fontsize=12)
        ax2.set_ylabel("손실액(백만원)", fontsize=12)
        ax2.tick_params(axis="x", rotation=45)
        ax2.grid(True, linestyle="--", alpha=0.7)

        plt.tight_layout()

        if save:
            save_plot(fig, self.output_dir / "bad_spread_impact.png")
        return fig

    def plot_time_analysis(self, save=True):
        """시간 경과에 따른 영향 시각화"""
        time_analysis = self.analysis.analyze_time_progression()

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 14))

        periods = time_analysis["기간(월)"].unique()

        # 기간별 스트레스 강도
        for period in periods:
            period_data = time_analysis[time_analysis["기간(월)"] == period]
            ax1.plot(
                period_data["만기"],
                period_data["스트레스강도"],
                marker="o",
                label=f"{period}개월",
            )

        ax1.set_title("기간별 스트레스 강도 변화", pad=20, fontsize=14)
        ax1.set_xlabel("만기(년)", fontsize=12)
        ax1.set_ylabel("스트레스 강도", fontsize=12)
        ax1.grid(True, linestyle="--", alpha=0.7)
        ax1.legend()

        # 기간별 손실 추이
        for period in periods:
            period_data = time_analysis[time_analysis["기간(월)"] == period]
            ax2.plot(
                period_data["만기"],
                period_data["기간별총손실"],
                marker="o",
                label=f"{period}개월",
            )

        ax2.set_title("기간별 총 손실 추이", pad=20, fontsize=14)
        ax2.set_xlabel("만기(년)", fontsize=12)
        ax2.set_ylabel("총 손실액(백만원)", fontsize=12)
        ax2.grid(True, linestyle="--", alpha=0.7)
        ax2.legend()

        plt.tight_layout()

        if save:
            save_plot(fig, self.output_dir / "bad_time_analysis.png")
        return fig

    def create_full_report(self):
        """모든 Bad 시나리오 차트 생성"""
        print(f"Saving bad scenario charts to: {self.output_dir}")

        self.visualize_rate_shock_scenario()
        self.plot_rate_impact()
        self.plot_spread_impact()
        self.plot_time_analysis()

        print("Bad scenario charts have been generated successfully.")


def main():
    visualizer = BadScenarioVisualization()
    visualizer.create_full_report()


if __name__ == "__main__":
    main()
