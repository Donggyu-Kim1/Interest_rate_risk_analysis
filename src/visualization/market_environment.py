import os
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
from src.analysis.market_environment import MarketEnvironmentAnalysis


class MarketEnvironmentVisualization:
    def __init__(self, analysis=None):
        self.analysis = analysis if analysis else MarketEnvironmentAnalysis()
        set_plot_style()

        # 프로젝트 루트 디렉토리 설정
        self.project_root = Path(__file__).parent.parent.parent
        self.output_dir = self.project_root / "docs" / "analysis" / "market_environment"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def plot_yield_curves(self, save=True):
        """금리 곡선 시각화"""
        yield_curves = self.analysis.analyze_yield_curve()
        tenors = ["1년", "3년", "5년", "10년"]

        fig, ax = plt.subplots(figsize=(12, 7))

        for date in yield_curves.index:
            data = yield_curves.loc[date]
            ax.plot(
                tenors,
                data,
                marker="o",
                label=date.strftime("%Y-%m-%d"),
                linewidth=2,
                markersize=8,
            )

        ax.set_title("국고채 금리 곡선 추이", pad=20, fontsize=14)
        ax.set_xlabel("만기", fontsize=12)
        ax.set_ylabel("금리 (%)", fontsize=12)
        ax.grid(True, linestyle="--", alpha=0.7)
        ax.legend(title="기준일", title_fontsize=10)

        # 그래프 여백 조정
        plt.tight_layout()

        if save:
            save_plot(fig, self.output_dir / "yield_curves.png")
        return fig

    def plot_credit_spreads(self, save=True):
        """신용스프레드 추이 시각화"""
        spread_data = self.analysis.analyze_credit_spreads()

        fig, ax = plt.subplots(figsize=(12, 7))

        # 만기별 색상 매핑 정의
        maturity_color_map = {
            "1.0년": "#1f77b4",  # 파랑
            "2.0년": "#ff7f0e",  # 주황
            "2.99년": "#2ca02c",  # 초록
            "3.0년": "#d62728",  # 빨강
            "5.0년": "#9467bd",  # 보라
            "10.0년": "#8c564b",  # 갈색
        }

        for maturity in spread_data.columns:
            color = maturity_color_map.get(maturity, COLOR_PALETTE["primary"])
            line = ax.plot(
                spread_data.index,
                spread_data[maturity] * 100,  # Convert to basis points
                label=f"{maturity}",
                linewidth=2,
            )

            # 색상이 매핑되지 않은 만기가 있다면 콘솔에 출력
            if maturity not in maturity_color_map:
                print(f"Warning: No color defined for maturity {maturity}")

        ax.set_title("만기별 신용스프레드 추이", pad=20, fontsize=14)
        ax.set_xlabel("일자", fontsize=12)
        ax.set_ylabel("스프레드 (bp)", fontsize=12)
        ax.grid(True, linestyle="--", alpha=0.7)
        ax.legend(
            title="만기", title_fontsize=10, bbox_to_anchor=(1.05, 1), loc="upper left"
        )

        # Format y-axis to show basis points
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{x:.0f}"))

        # 그래프 여백 조정
        plt.tight_layout()

        if save:
            save_plot(fig, self.output_dir / "credit_spreads.png")
        return fig

    def plot_rate_volatility(self, save=True):
        """금리 변동성 시각화"""
        volatility_data = self.analysis.analyze_rate_volatility()

        fig, ax = plt.subplots(figsize=(12, 7))

        for column in volatility_data.columns:
            tenor = column.replace("_변동성", "")
            color = MATURITY_COLORS.get(
                tenor.replace("국고채권(", "").replace(")", ""),
                COLOR_PALETTE["primary"],
            )
            ax.plot(
                volatility_data.index,
                volatility_data[column] * 100,
                label=tenor,
                linewidth=2,
                color=color,
            )

        ax.set_title("만기별 금리 변동성 추이", pad=20, fontsize=14)
        ax.set_xlabel("일자", fontsize=12)
        ax.set_ylabel("연율화 변동성 (%)", fontsize=12)
        ax.grid(True, linestyle="--", alpha=0.7)
        ax.legend(title="만기", title_fontsize=10)

        # 그래프 여백 조정
        plt.tight_layout()

        if save:
            save_plot(fig, self.output_dir / "rate_volatility.png")
        return fig

    def create_full_report(self):
        """모든 시장 분석 차트 생성"""
        print(f"Saving market analysis charts to: {self.output_dir}")

        self.plot_yield_curves()
        self.plot_credit_spreads()
        self.plot_rate_volatility()

        print("Market analysis charts have been generated successfully.")


def main():
    visualizer = MarketEnvironmentVisualization()
    visualizer.create_full_report()


if __name__ == "__main__":
    main()
