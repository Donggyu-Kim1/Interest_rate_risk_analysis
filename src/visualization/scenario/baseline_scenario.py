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
from src.analysis.scenario.baseline_scenario import BaselineScenarioAnalysis


class BaselineScenarioVisualization:
    def __init__(self, analysis=None):
        self.analysis = analysis if analysis else BaselineScenarioAnalysis()
        set_plot_style()

        self.project_root = Path(__file__).parent.parent.parent.parent
        self.output_dir = self.project_root / "docs" / "analysis" / "scenarios"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def visualize_rate_change_logic(self, save=True):
        """baseline_scenario 설정"""
        fig, ax = plt.subplots(figsize=(12, 8))

        # 만기 구간 설정
        maturities = np.linspace(0, 10, 100)
        rates = []

        # 금리 변화 로직 적용
        for m in maturities:
            if m <= 2:
                rate = -25  # -25bp
            elif m <= 5:
                rate = -20  # -20bp
            else:
                rate = -15  # -15bp
            rate -= 7  # 신용스프레드 축소 효과 (-7bp)
            rates.append(rate)

        # 금리 변화 그래프
        ax.plot(maturities, rates, "b-", linewidth=2)

        # 구간 표시
        ax.axvspan(0, 2, alpha=0.2, color="red", label="2년 이하: -25bp")
        ax.axvspan(2, 5, alpha=0.2, color="green", label="2~5년: -20bp")
        ax.axvspan(5, 10, alpha=0.2, color="blue", label="5년 초과: -15bp")

        # 신용스프레드 효과 표시
        ax.axhline(
            y=-7, color="gray", linestyle="--", label="신용스프레드 축소 효과: -7bp"
        )

        # 그래프 설정
        ax.set_title("만기별 금리 인하 시나리오 설정", pad=20, fontsize=14)
        ax.set_xlabel("만기(년)", fontsize=12)
        ax.set_ylabel("금리 변동(bp)", fontsize=12)
        ax.grid(True, linestyle="--", alpha=0.7)
        ax.legend()

        # 주요 포인트 표시
        key_points = [(2, -32), (5, -27), (7, -22)]
        for x, y in key_points:
            ax.plot(x, y, "ro")
            ax.annotate(
                f"({x}년, {y}bp)",
                xy=(x, y),
                xytext=(10, 10),
                textcoords="offset points",
            )

        plt.tight_layout()

        if save:
            save_plot(fig, self.output_dir / "baseline_rate_scenario.png")
        return fig

    def plot_rate_changes(self, save=True):
        """금리 변동 시각화"""
        rate_changes = self.analysis.calculate_rate_changes()

        fig, ax = plt.subplots(figsize=(12, 7))

        # 만기별로 정렬
        rate_changes = rate_changes.sort_values("만기")

        bars = ax.bar(rate_changes["만기"], rate_changes["금리변동(bp)"])

        # Bar 색상 설정
        for bar, maturity in zip(bars, rate_changes["만기"]):
            bar.set_color(
                MATURITY_COLORS.get(f"{maturity}년", COLOR_PALETTE["primary"])
            )

        ax.set_title("만기별 금리 변동폭", pad=20, fontsize=14)
        ax.set_xlabel("만기(년)", fontsize=12)
        ax.set_ylabel("금리 변동(bp)", fontsize=12)
        ax.grid(True, linestyle="--", alpha=0.7)

        # Bar 위에 값 표시
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{height:.1f}bp",
                ha="center",
                va="bottom",
            )

        plt.tight_layout()

        if save:
            save_plot(fig, self.output_dir / "baseline_rate_changes.png")
        return fig

    def plot_price_impact(self, save=True):
        """가격 변화 영향 시각화"""
        price_changes = self.analysis.calculate_price_changes()

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 14))

        # 상단 그래프: 절대적 가격 변화
        price_changes = price_changes.sort_values("만기")
        bars1 = ax1.bar(price_changes["종목명"], price_changes["가격변화"])

        ax1.set_title("채권별 가격 변화", pad=20, fontsize=14)
        ax1.set_xlabel("종목명", fontsize=12)
        ax1.set_ylabel("가격 변화(원)", fontsize=12)
        ax1.tick_params(axis="x", rotation=45)
        ax1.grid(True, linestyle="--", alpha=0.7)

        # 하단 그래프: 수익률 변화
        bars2 = ax2.bar(price_changes["종목명"], price_changes["수익률(%)"])

        ax2.set_title("채권별 수익률 변화", pad=20, fontsize=14)
        ax2.set_xlabel("종목명", fontsize=12)
        ax2.set_ylabel("수익률(%)", fontsize=12)
        ax2.tick_params(axis="x", rotation=45)
        ax2.grid(True, linestyle="--", alpha=0.7)

        # Bar 색상 설정
        for bar1, bar2, maturity in zip(bars1, bars2, price_changes["만기"]):
            color = MATURITY_COLORS.get(f"{maturity}년", COLOR_PALETTE["primary"])
            bar1.set_color(color)
            bar2.set_color(color)

        plt.tight_layout()

        if save:
            save_plot(fig, self.output_dir / "baseline_price_impact.png")
        return fig

    def plot_maturity_analysis(self, save=True):
        """만기별 분석 시각화"""
        results = self.analysis.analyze_portfolio_impact()
        maturity_analysis = results["maturity_analysis"]

        fig, ax = plt.subplots(figsize=(12, 7))

        x = range(len(maturity_analysis.index))
        width = 0.3

        # 발행액 막대 그래프
        ax1 = ax
        bars1 = ax1.bar(
            [i - width / 2 for i in x],
            maturity_analysis["발행액"],
            width,
            label="발행액",
            color=COLOR_PALETTE["primary"],
        )
        ax1.set_ylabel("발행액(백만원)", color=COLOR_PALETTE["primary"])

        # 수익률 선 그래프
        ax2 = ax1.twinx()
        line = ax2.plot(
            x,
            maturity_analysis["수익률(%)"],
            "o-",
            label="평균 수익률",
            color=COLOR_PALETTE["secondary"],
        )
        ax2.set_ylabel("수익률(%)", color=COLOR_PALETTE["secondary"])

        # 그래프 설정
        ax1.set_title("만기별 분석", pad=20, fontsize=14)
        ax1.set_xticks(x)
        ax1.set_xticklabels(maturity_analysis.index)
        ax1.grid(True, linestyle="--", alpha=0.7)

        # 범례 통합
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2, loc="upper right")

        plt.tight_layout()

        if save:
            save_plot(fig, self.output_dir / "baseline_maturity_analysis.png")
        return fig

    def create_full_report(self):
        """모든 기준 시나리오 차트 생성"""
        print(f"Saving baseline scenario charts to: {self.output_dir}")

        self.visualize_rate_change_logic()
        self.plot_rate_changes()
        self.plot_price_impact()
        self.plot_maturity_analysis()

        print("Baseline scenario charts have been generated successfully.")


def main():
    visualizer = BaselineScenarioVisualization()
    visualizer.create_full_report()


if __name__ == "__main__":
    main()
