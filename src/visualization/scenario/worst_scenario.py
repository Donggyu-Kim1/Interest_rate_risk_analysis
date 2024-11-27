import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import numpy as np
from src.utils.plot_config import (
    set_plot_style,
    COLOR_PALETTE,
    MATURITY_COLORS,
    format_percentage,
    save_plot,
)
from src.analysis.scenario.worst_scenario import WorstScenarioAnalysis


class WorstScenarioVisualization:
    def __init__(self, analysis=None):
        self.analysis = analysis if analysis else WorstScenarioAnalysis()
        set_plot_style()

        # 개별 분석 실행
        self.rate_impact = self.analysis.apply_rate_shock()
        self.credit_impact = self.analysis.analyze_severe_credit_crisis()
        self.total_impact = self.analysis.calculate_crisis_impact()
        self.crisis_analysis = self.analysis.analyze_crisis_progression()

        self.results = {
            "rate_impact": self.rate_impact,
            "credit_impact": self.credit_impact,
            "total_impact": self.total_impact,
            "crisis_analysis": self.crisis_analysis,
        }

        self.output_dir = (
            Path(__file__).parent.parent.parent.parent
            / "docs"
            / "analysis"
            / "scenarios"
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def plot_detailed_components(self, save=True):
        """상세 위기 구성요소 영향 시각화"""
        impact_data = self.total_impact.copy()
        impact_data_main = impact_data[:-1]
        impact_data_last = impact_data.iloc[-1:]

        # 주요 손실 구성요소
        components = [
            "금리충격손실",
            "신용리스크손실",
            "상호작용효과",
            "최종위험조정손실",
        ]

        fig = plt.figure(figsize=(15, 12))
        gs = fig.add_gridspec(3, 1, height_ratios=[2, 1, 2])

        # 상단 그래프: 1-10번 채권
        ax1 = fig.add_subplot(gs[0])
        impact_data_main[components].abs().plot(kind="bar", ax=ax1, width=0.8)
        ax1.set_title("채권별 위기 요소 손실 규모", pad=20, fontsize=12)
        ax1.set_xlabel("")
        ax1.set_ylabel("손실액(백만원)")
        ax1.set_xticklabels(impact_data_main["종목명"], rotation=45, ha="right")
        ax1.legend(title="손실 요인")
        ax1.grid(True, alpha=0.3)

        # 중단 그래프: 11번 채권
        ax2 = fig.add_subplot(gs[1])
        impact_data_last[components].abs().plot(kind="bar", ax=ax2, width=0.8)
        ax2.set_xlabel("")
        ax2.set_ylabel("손실액(백만원)")
        ax2.set_xticklabels(impact_data_last["종목명"], rotation=45, ha="right")
        ax2.grid(True, alpha=0.3)
        ax2.legend().remove()  # 범례 제거

        # 하단 그래프: 만기별 분포
        ax3 = fig.add_subplot(gs[2])
        sns.boxplot(data=impact_data, x="만기", y="최종위험조정손실", ax=ax3)
        ax3.set_title("만기별 최종 위험조정손실 분포", pad=20, fontsize=12)
        ax3.set_xlabel("만기(년)")
        ax3.set_ylabel("손실액(백만원)")
        ax3.grid(True, alpha=0.3)

        plt.tight_layout()

        if save:
            save_plot(fig, self.output_dir / "worst_detailed_components.png")
        return fig

    def plot_risk_evolution(self, save=True):
        """위험 진화 과정 상세 분석"""
        crisis_data = self.crisis_analysis

        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))

        # 1. 위기 강도 변화
        for maturity in crisis_data["만기"].unique():
            mask = crisis_data["만기"] == maturity
            ax1.plot(
                crisis_data[mask]["기간(월)"],
                crisis_data[mask]["만기조정위기강도"],
                marker="o",
                label=f"{maturity}년",
            )

        ax1.set_title("만기별 위기 강도 진화", pad=20)
        ax1.set_xlabel("경과 기간(월)")
        ax1.set_ylabel("위기 강도")
        ax1.legend(title="만기")
        ax1.grid(True, alpha=0.3)

        # 2. 누적 손실 추이
        period_losses = crisis_data.pivot_table(
            values="기간별조정손실", index="기간(월)", columns="만기", aggfunc="sum"
        )
        period_losses.plot(kind="bar", ax=ax2, width=0.8)

        ax2.set_title("기간별 누적 손실 추이", pad=20)
        ax2.set_xlabel("경과 기간(월)")
        ax2.set_ylabel("손실액(백만원)")
        ax2.legend(title="만기(년)")
        ax2.grid(True, alpha=0.3)

        # 3. 만기별 부도위험 가중치
        sns.boxplot(data=crisis_data, x="만기", y="부도위험가중치", ax=ax3)

        ax3.set_title("만기별 부도위험 가중치 분포", pad=20)
        ax3.set_xlabel("만기(년)")
        ax3.set_ylabel("부도위험 가중치")
        ax3.grid(True, alpha=0.3)

        # 4. 스프레드 영향
        spread_data = self.credit_impact.sort_values("만기")
        ax4.bar(
            range(len(spread_data)),
            spread_data["스프레드확대(bp)"],
            label="스프레드 확대",
        )
        ax4.bar(
            range(len(spread_data)),
            spread_data["유동성프리미엄(bp)"],
            bottom=spread_data["스프레드확대(bp)"],
            label="유동성 프리미엄",
        )

        ax4.set_title("채권별 스프레드 구성요소", pad=20)
        ax4.set_xlabel("채권")
        ax4.set_ylabel("베이시스 포인트(bp)")
        ax4.set_xticks(range(len(spread_data)))
        ax4.set_xticklabels(spread_data["종목명"], rotation=45)
        ax4.legend()
        ax4.grid(True, alpha=0.3)

        plt.tight_layout()

        if save:
            save_plot(fig, self.output_dir / "worst_risk_evolution.png")
        return fig

    def create_worst_case_report(self):
        """최악의 시나리오 분석 보고서 생성"""
        print(f"Saving worst case scenario analysis charts to: {self.output_dir}")

        self.plot_detailed_components()
        self.plot_risk_evolution()

        print(
            "Enhanced worst case scenario analysis charts have been generated successfully."
        )


def main():
    visualizer = WorstScenarioVisualization()
    visualizer.create_worst_case_report()


if __name__ == "__main__":
    main()
