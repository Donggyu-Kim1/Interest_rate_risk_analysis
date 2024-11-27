import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from src.utils.plot_config import (
    set_plot_style,
    COLOR_PALETTE,
    MATURITY_COLORS,
    format_percentage,
    save_plot,
)
from src.analysis.scenario.stress_test import HistoricalStressTest


class StressTestVisualization:
    def __init__(self, stress_test=None):
        self.stress_test = stress_test if stress_test else HistoricalStressTest()
        set_plot_style()
        self.results = self.stress_test.run_stress_test()
        self.report = self.stress_test.generate_report(self.results)

        self.output_dir = (
            Path(__file__).parent.parent.parent.parent
            / "docs"
            / "analysis"
            / "stress_test"
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def plot_scenario_impact(self, save=True):
        """시나리오별 손실 영향 시각화"""
        scenario_data = self.report["시나리오별 요약"]

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 12))

        # 손실액 시각화
        scenario_data["손실액"]["sum"].unstack().plot(
            kind="bar",
            ax=ax1,
            color=[COLOR_PALETTE["negative"], COLOR_PALETTE["primary"]],
        )
        ax1.set_title("시나리오별 총 손실액", pad=20)
        ax1.set_ylabel("손실액 (원)")
        ax1.tick_params(axis="x", rotation=45)

        # 손실률 시각화
        scenario_data["손실률(%)"]["mean"].unstack().plot(
            kind="bar",
            ax=ax2,
            color=[COLOR_PALETTE["negative"], COLOR_PALETTE["primary"]],
        )
        ax2.set_title("시나리오별 평균 손실률", pad=20)
        ax2.set_ylabel("손실률 (%)")
        ax2.tick_params(axis="x", rotation=45)

        plt.tight_layout()

        if save:
            save_plot(fig, self.output_dir / "scenario_impact.png")
        return fig

    def plot_maturity_vulnerability(self, save=True):
        """만기별 취약성 분석 시각화"""
        maturity_data = self.report["만기그룹별 취약성"]

        fig, ax = plt.subplots(figsize=(12, 6))

        maturity_data["손실률(%)"]["mean"].unstack().plot(kind="bar", ax=ax, width=0.8)

        ax.set_title("만기그룹별 평균 손실률", pad=20)
        ax.set_xlabel("만기그룹")
        ax.set_ylabel("손실률 (%)")
        ax.tick_params(axis="x", rotation=45)
        ax.grid(True, linestyle="--", alpha=0.7)

        plt.tight_layout()

        if save:
            save_plot(fig, self.output_dir / "maturity_vulnerability.png")
        return fig

    def plot_bond_loss_distribution(self, save=True):
        """개별 채권 손실 분포 시각화"""
        bond_data = self.report["개별 종목 분석"]

        fig, ax = plt.subplots(figsize=(12, 6))

        sns.boxplot(
            data=self.results, x="만기그룹", y="손실률(%)", hue="시나리오", ax=ax
        )

        ax.set_title("만기그룹별 손실률 분포", pad=20)
        ax.set_xlabel("만기그룹")
        ax.set_ylabel("손실률 (%)")
        ax.tick_params(axis="x", rotation=45)

        plt.tight_layout()

        if save:
            save_plot(fig, self.output_dir / "bond_loss_distribution.png")
        return fig

    def create_stress_test_report(self):
        """스트레스 테스트 분석 보고서 생성"""
        print(f"Saving stress test analysis charts to: {self.output_dir}")

        self.plot_scenario_impact()
        self.plot_maturity_vulnerability()
        self.plot_bond_loss_distribution()

        print("Stress test analysis charts have been generated successfully.")


def main():
    visualizer = StressTestVisualization()
    visualizer.create_stress_test_report()


if __name__ == "__main__":
    main()
