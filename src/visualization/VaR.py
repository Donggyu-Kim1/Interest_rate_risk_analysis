import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy import stats
from pathlib import Path
from src.utils.plot_config import (
    set_plot_style,
    COLOR_PALETTE,
    MATURITY_COLORS,
    format_percentage,
    save_plot,
)
from src.analysis.VaR import MonteCarloVaRAnalysis


class VaRVisualization:
    def __init__(self, analysis=None):
        self.analysis = analysis if analysis else MonteCarloVaRAnalysis()
        set_plot_style()

        # 프로젝트 루트 디렉토리 설정
        self.project_root = Path(__file__).parent.parent.parent
        self.output_dir = self.project_root / "docs" / "analysis" / "var"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def plot_risk_profile(self, summary, save=True):
        """채권별 리스크 프로파일 시각화"""
        fig, ax = plt.subplots(figsize=(12, 8))

        # 데이터 준비
        bonds = summary["Bond"].values
        var_95 = np.abs(summary["VaR_95"].values)  # 절대값 처리
        es_95 = np.abs(summary["ES_95"].values)  # 절대값 처리
        position_sizes = summary["Position Size"].values

        # 손실률 계산 (포지션 크기 대비 비율)
        var_loss_ratio = (var_95 / position_sizes) * 100
        es_loss_ratio = (es_95 / position_sizes) * 100

        # 정렬을 위한 인덱스 (VaR 기준)
        sort_idx = np.argsort(var_loss_ratio)[::-1]  # 내림차순 정렬

        x = np.arange(len(bonds))
        width = 0.8

        # VaR을 기본 막대로 표시
        bars1 = ax.bar(
            x,
            var_loss_ratio[sort_idx],
            width,
            label="VaR 95%",
            color="skyblue",
            alpha=0.7,
        )

        # ES를 별도의 막대로 표시
        bars2 = ax.bar(
            x, es_loss_ratio[sort_idx], width, label="ES 95%", color="salmon", alpha=0.4
        )

        # 평균선 추가
        ax.axhline(
            y=np.mean(var_loss_ratio),
            color="blue",
            linestyle="--",
            alpha=0.5,
            label="평균 VaR",
        )
        ax.axhline(
            y=np.mean(es_loss_ratio),
            color="red",
            linestyle="--",
            alpha=0.5,
            label="평균 ES",
        )

        # 그래프 꾸미기
        ax.set_title(
            "채권별 VaR & ES 분석\n(포지션 대비 예상 최대손실률)", pad=20, fontsize=14
        )
        ax.set_xlabel("채권 (VaR 기준 정렬)", fontsize=12)
        ax.set_ylabel("포지션 대비 손실률 (%)", fontsize=12)

        # x축 레이블 설정
        ax.set_xticks(x)
        ax.set_xticklabels([bonds[i] for i in sort_idx], rotation=45, ha="right")

        # 범례 설정
        ax.legend(loc="upper right")

        # 그리드 추가
        ax.grid(True, axis="y", linestyle="--", alpha=0.3)

        # 데이터 레이블 추가
        def autolabel(bars):
            for bar in bars:
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height,
                    f"{height:.1f}%",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                )

        autolabel(bars1)

        plt.tight_layout()

        if save:
            save_plot(fig, self.output_dir / "risk_profile.png")
        return fig

    def plot_return_distribution(
        self, bond_data, simulated_returns, var_95, es_95, save=True
    ):
        """수익률 분포도 시각화 (VaR, ES 표시)"""
        fig, ax = plt.subplots(figsize=(12, 7))

        # 히스토그램 생성
        n, bins, patches = ax.hist(
            simulated_returns,
            bins=50,
            density=True,
            color="skyblue",
            alpha=0.7,
            label="수익률 분포",
        )

        # VaR과 ES 위치 표시
        var_line = ax.axvline(
            var_95, color="red", linestyle="--", label=f"VaR 95%: {var_95:.2f}%"
        )
        es_line = ax.axvline(
            es_95, color="darkred", linestyle="-.", label=f"ES 95%: {es_95:.2f}%"
        )

        # VaR을 초과하는 영역 강조 - 안전하게 수정
        try:
            var_idx = np.where(bins >= var_95)[0]
            if len(var_idx) > 0:
                var_idx = var_idx[0]
                for patch in patches[var_idx:]:
                    patch.set_facecolor("salmon")
                    patch.set_alpha(0.5)
        except Exception as e:
            print(
                f"Warning: Could not highlight VaR region for {bond_data['종목명']}: {str(e)}"
            )

        # 커널 밀도 추정 곡선 추가
        kde = stats.gaussian_kde(simulated_returns)
        x_range = np.linspace(min(simulated_returns), max(simulated_returns), 200)
        ax.plot(x_range, kde(x_range), "k-", lw=2, label="KDE", alpha=0.5)

        # ES 영역 표시 - 안전하게 수정
        tail_returns = simulated_returns[simulated_returns <= var_95]
        if len(tail_returns) > 0:
            x_range_tail = x_range[x_range <= var_95]
            if len(x_range_tail) > 0:
                ax.fill_between(
                    x_range_tail,
                    kde(x_range_tail),
                    color="red",
                    alpha=0.2,
                    label="ES 영역",
                )

        # 그래프 꾸미기
        ax.set_title(
            f"수익률 분포 및 리스크 지표\n{bond_data['종목명']}", pad=20, fontsize=14
        )
        ax.set_xlabel("수익률 (%)", fontsize=12)
        ax.set_ylabel("빈도", fontsize=12)
        ax.grid(True, linestyle="--", alpha=0.3)
        ax.legend(loc="upper left")

        # 주요 통계량 텍스트 추가
        stats_text = (
            f"평균 수익률: {np.mean(simulated_returns):.2f}%\n"
            f"표준편차: {np.std(simulated_returns):.2f}%\n"
            f"왜도: {stats.skew(simulated_returns):.2f}\n"
            f"첨도: {stats.kurtosis(simulated_returns):.2f}"
        )

        ax.text(
            0.95,
            0.95,
            stats_text,
            transform=ax.transAxes,
            verticalalignment="top",
            horizontalalignment="right",
            bbox=dict(facecolor="white", alpha=0.8),
        )

        # x축 범위 설정
        margin = (max(simulated_returns) - min(simulated_returns)) * 0.1
        ax.set_xlim(min(simulated_returns) - margin, max(simulated_returns) + margin)

        plt.tight_layout()

        if save:
            save_plot(
                fig, self.output_dir / f"return_distribution_{bond_data['종목명']}.png"
            )

        return fig

    def plot_multi_distributions(self, summary, simulations_data, save=True):
        """여러 채권의 수익률 분포 비교"""
        n_bonds = len(summary)
        fig, axes = plt.subplots(
            int(np.ceil(n_bonds / 2)),
            2,
            figsize=(15, 4 * int(np.ceil(n_bonds / 2))),
            constrained_layout=True,
        )
        axes = axes.flatten()

        for idx, (bond_name, sim_data) in enumerate(simulations_data.items()):
            ax = axes[idx]

            # 해당 채권의 VaR, ES 값 찾기
            bond_summary = summary[summary["Bond"] == bond_name].iloc[0]
            var_95 = bond_summary["VaR_95_pct"]
            es_95 = bond_summary["ES_95_pct"]

            # 히스토그램 그리기
            n, bins, patches = ax.hist(
                sim_data, bins=30, density=True, color="skyblue", alpha=0.7
            )

            # VaR, ES 표시
            ax.axvline(
                var_95, color="red", linestyle="--", label=f"VaR 95%: {var_95:.2f}%"
            )
            ax.axvline(
                es_95, color="darkred", linestyle="-.", label=f"ES 95%: {es_95:.2f}%"
            )

            # VaR 초과 영역 강조 - 안전하게 수정
            try:
                var_idx = np.where(bins >= var_95)[0]
                if len(var_idx) > 0:
                    var_idx = var_idx[0]
                    for patch in patches[var_idx:]:
                        patch.set_facecolor("salmon")
                        patch.set_alpha(0.5)
            except Exception as e:
                print(
                    f"Warning: Could not highlight VaR region for {bond_name}: {str(e)}"
                )

            # 커널 밀도 추정 곡선 추가
            kde = stats.gaussian_kde(sim_data)
            x_range = np.linspace(min(sim_data), max(sim_data), 200)
            ax.plot(x_range, kde(x_range), "k-", lw=2, label="KDE", alpha=0.5)

            # 그래프 꾸미기
            ax.set_title(f"{bond_name}", fontsize=10)
            ax.grid(True, linestyle="--", alpha=0.3)
            ax.legend(fontsize=8)

            # 핵심 통계량 표시
            stats_text = f"μ={np.mean(sim_data):.2f}%\nσ={np.std(sim_data):.2f}%"
            ax.text(
                0.95,
                0.95,
                stats_text,
                transform=ax.transAxes,
                verticalalignment="top",
                horizontalalignment="right",
                fontsize=8,
                bbox=dict(facecolor="white", alpha=0.8),
            )

            # x축 범위 설정
            margin = (max(sim_data) - min(sim_data)) * 0.1
            ax.set_xlim(min(sim_data) - margin, max(sim_data) + margin)

        # 사용하지 않는 서브플롯 제거
        for idx in range(len(simulations_data), len(axes)):
            fig.delaxes(axes[idx])

        fig.suptitle("채권별 수익률 분포 비교", fontsize=14, y=1.02)

        if save:
            save_plot(fig, self.output_dir / "multi_distributions.png")
        return fig

    def create_full_report(self):
        """모든 VaR 분석 차트 생성"""
        print(f"Saving VaR analysis charts to: {self.output_dir}")

        # VaR 분석 실행
        summary, maturity_groups = self.analysis.analyze_portfolio()

        # 시뮬레이션 결과 가져오기
        simulated_data = {}
        for _, bond_row in summary.iterrows():
            bond_name = bond_row["Bond"]
            # MonteCarloVaRAnalysis에서 해당 채권의 시뮬레이션 데이터 가져오기
            bond_data = {"종목명": bond_name}
            simulated_returns = self.analysis.run_simulation(bond_name)
            var_95 = bond_row["VaR_95_pct"]
            es_95 = bond_row["ES_95_pct"]

            # 개별 채권 분포도 생성
            self.plot_return_distribution(bond_data, simulated_returns, var_95, es_95)
            simulated_data[bond_name] = simulated_returns

        # 전체 차트 생성
        self.plot_risk_profile(summary)
        self.plot_multi_distributions(summary, simulated_data)

        print("VaR analysis charts have been generated successfully.")


def main():
    visualizer = VaRVisualization()
    visualizer.create_full_report()


if __name__ == "__main__":
    main()
