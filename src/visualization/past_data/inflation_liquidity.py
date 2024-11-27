import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
from src.utils.plot_config import (
    set_plot_style,
    COLOR_PALETTE,
    format_percentage,
    save_plot,
)
from src.analysis.past_data.inflation_liquidity import InflationPeriodAnalysis

# 만기별 색상 매핑
TENOR_COLORS = {
    "1년": "#FF9999",  # 연한 빨강
    "3년": "#66B2FF",  # 연한 파랑
    "5년": "#99FF99",  # 연한 초록
    "10년": "#FFCC99",  # 연한 주황
}


class InflationVisualization:
    def __init__(self, analysis=None):
        self.analysis = analysis if analysis else InflationPeriodAnalysis()
        set_plot_style()

        self.project_root = Path(__file__).parent.parent.parent.parent
        self.output_dir = self.project_root / "docs" / "analysis" / "inflation_period"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def plot_rate_trends(self, save=True):
        """인플레이션 기간 금리 추이 시각화"""
        rates_data = self.analysis.get_inflation_period_rates()

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))

        # 금리 수준 추이
        for tenor, color in TENOR_COLORS.items():
            col_name = f"국고채권{tenor}"
            ax1.plot(
                rates_data["일자"],
                rates_data[col_name],
                label=f"{tenor}",
                color=color,
                linewidth=2,
            )

        ax1.set_title("국고채 금리 추이", pad=20, fontsize=14, fontweight="bold")
        ax1.set_xlabel("일자", fontsize=12)
        ax1.set_ylabel("금리(%)", fontsize=12)
        ax1.grid(True, linestyle="--", alpha=0.3)
        ax1.legend(title="만기", title_fontsize=10, fontsize=9, loc="upper right")

        # 일간 변동폭 추이
        for tenor, color in TENOR_COLORS.items():
            col_name = f"daily_change_{tenor[0]}y"
            if tenor == "10년":
                col_name = "daily_change_10y"
            ax2.plot(
                rates_data["일자"],
                rates_data[col_name],
                label=f"{tenor}",
                color=color,
                linewidth=2,
            )

        ax2.set_title("일간 금리 변동폭", pad=20, fontsize=14, fontweight="bold")
        ax2.set_xlabel("일자", fontsize=12)
        ax2.set_ylabel("변동폭(%p)", fontsize=12)
        ax2.grid(True, linestyle="--", alpha=0.3)
        ax2.legend(title="만기", title_fontsize=10, fontsize=9, loc="upper right")

        # x축 날짜 포맷 설정
        plt.gcf().autofmt_xdate()

        plt.tight_layout()

        if save:
            save_plot(fig, self.output_dir / "inflation_rate_trends.png")
        return fig

    def plot_peak_rates_period(self, save=True):
        """최고 금리 기간 분석 시각화"""
        peak_rates = self.analysis.find_peak_rates_period()

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))

        # 실제 금리 추이
        for tenor, color in TENOR_COLORS.items():
            col_name = f"국고채권{tenor}"
            ax1.plot(
                peak_rates["일자"],
                peak_rates[col_name],
                label=f"{tenor}",
                color=color,
                linewidth=2,
            )

        ax1.set_title("실제 금리 추이", pad=20, fontsize=14, fontweight="bold")
        ax1.set_xlabel("일자", fontsize=12)
        ax1.set_ylabel("금리(%)", fontsize=12)
        ax1.grid(True, linestyle="--", alpha=0.3)
        ax1.legend(title="만기", title_fontsize=10, fontsize=9)

        # 이동평균 추이
        for tenor, color in TENOR_COLORS.items():
            ma_col = f"MA_{tenor[0]}Y"
            if tenor == "10년":
                ma_col = "MA_10Y"
            ax2.plot(
                peak_rates["일자"],
                peak_rates[ma_col],
                label=f"{tenor} 이동평균",
                color=color,
                linewidth=2,
            )

        ax2.set_title("30일 이동평균 추이", pad=20, fontsize=14, fontweight="bold")
        ax2.set_xlabel("일자", fontsize=12)
        ax2.set_ylabel("금리(%)", fontsize=12)
        ax2.grid(True, linestyle="--", alpha=0.3)
        ax2.legend(title="만기", title_fontsize=10, fontsize=9)

        plt.gcf().autofmt_xdate()

        plt.tight_layout()

        if save:
            save_plot(fig, self.output_dir / "peak_rate_period.png")
        return fig

    def plot_rate_rises(self, save=True):
        """금리 상승 분석 시각화"""
        rate_rises = self.analysis.analyze_rate_rise()

        fig, ax = plt.subplots(figsize=(15, 8))

        # 만기별 상승폭 산점도
        for tenor, color in TENOR_COLORS.items():
            rise_col = f"rise_{tenor[0]}y"
            if tenor == "10년":
                rise_col = "rise_10y"
            scatter = ax.scatter(
                rate_rises["일자"],
                rate_rises[rise_col],
                label=f"{tenor}",
                color=color,
                alpha=0.6,
                s=100,
            )

        ax.axhline(y=0, color="gray", linestyle="--", alpha=0.5)

        ax.set_title("금리 상승 분석", pad=20, fontsize=14, fontweight="bold")
        ax.set_xlabel("일자", fontsize=12)
        ax.set_ylabel("금리 변화(%p)", fontsize=12)
        ax.grid(True, linestyle="--", alpha=0.3)

        plt.gcf().autofmt_xdate()

        ax.legend(title="만기", title_fontsize=10, fontsize=9, loc="upper right")

        plt.tight_layout()

        if save:
            save_plot(fig, self.output_dir / "rate_rises.png")
        return fig

    def plot_summary_stats(self, save=True):
        """주요 통계 시각화"""
        rates_data = self.analysis.get_inflation_period_rates()

        # 기초 통계량 계산
        stats_data = {
            "만기": ["1년", "3년", "5년", "10년"],
            "최저금리": [
                rates_data["국고채권1년"].min(),
                rates_data["국고채권3년"].min(),
                rates_data["국고채권5년"].min(),
                rates_data["국고채권10년"].min(),
            ],
            "최고금리": [
                rates_data["국고채권1년"].max(),
                rates_data["국고채권3년"].max(),
                rates_data["국고채권5년"].max(),
                rates_data["국고채권10년"].max(),
            ],
            "변동폭": [
                rates_data["국고채권1년"].max() - rates_data["국고채권1년"].min(),
                rates_data["국고채권3년"].max() - rates_data["국고채권3년"].min(),
                rates_data["국고채권5년"].max() - rates_data["국고채권5년"].min(),
                rates_data["국고채권10년"].max() - rates_data["국고채권10년"].min(),
            ],
        }

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))

        # 최고/최저 금리 비교
        x = np.arange(len(stats_data["만기"]))
        width = 0.35

        ax1.bar(
            x - width / 2,
            stats_data["최저금리"],
            width,
            label="최저금리",
            color="lightblue",
            alpha=0.7,
        )
        ax1.bar(
            x + width / 2,
            stats_data["최고금리"],
            width,
            label="최고금리",
            color="lightcoral",
            alpha=0.7,
        )

        ax1.set_title("만기별 최고/최저 금리", pad=20, fontsize=14, fontweight="bold")
        ax1.set_xticks(x)
        ax1.set_xticklabels(stats_data["만기"])
        ax1.set_ylabel("금리(%)", fontsize=12)
        ax1.legend()
        ax1.grid(True, linestyle="--", alpha=0.3)

        # 변동폭 비교
        bars = ax2.bar(
            stats_data["만기"],
            stats_data["변동폭"],
            color=[TENOR_COLORS[m] for m in stats_data["만기"]],
        )

        ax2.set_title("만기별 금리 변동폭", pad=20, fontsize=14, fontweight="bold")
        ax2.set_ylabel("변동폭(%p)", fontsize=12)
        ax2.grid(True, linestyle="--", alpha=0.3)

        # 막대 위에 값 표시
        for bar in bars:
            height = bar.get_height()
            ax2.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{height:.2f}%p",
                ha="center",
                va="bottom",
            )

        plt.tight_layout()

        if save:
            save_plot(fig, self.output_dir / "summary_stats.png")
        return fig

    def create_full_report(self):
        """모든 인플레이션 기간 분석 차트 생성"""
        print(f"Saving Inflation period analysis charts to: {self.output_dir}")

        self.plot_rate_trends()
        self.plot_peak_rates_period()
        self.plot_rate_rises()
        self.plot_summary_stats()

        print("Inflation period analysis charts have been generated successfully.")


def main():
    visualizer = InflationVisualization()
    visualizer.create_full_report()


if __name__ == "__main__":
    main()
