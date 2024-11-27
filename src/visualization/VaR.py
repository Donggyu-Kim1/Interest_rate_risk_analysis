import matplotlib.pyplot as plt
import pandas as pd
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
        self.output_dir = (
            Path(__file__).parent.parent.parent / "docs" / "analysis" / "var"
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def plot_distribution_fit(self, returns, bond_name, save=True):
        """수익률의 분포 적합성 검정 및 시각화"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # 정규성 검정
        stat, p_value = stats.normaltest(returns)

        # 히스토그램과 이론적 분포 비교
        sns.histplot(returns, stat="density", kde=True, ax=ax1)
        x = np.linspace(returns.min(), returns.max(), 100)

        # 정규분포 적합
        mu, std = stats.norm.fit(returns)
        pdf_norm = stats.norm.pdf(x, mu, std)
        ax1.plot(x, pdf_norm, "r-", label="Normal")

        # t분포 적합
        df, loc, scale = stats.t.fit(returns)
        pdf_t = stats.t.pdf(x, df, loc, scale)
        ax1.plot(x, pdf_t, "g--", label="Student t")

        ax1.set_title(f"Distribution Fit Test\np-value: {p_value:.4f}")
        ax1.legend()

        # Q-Q plot
        stats.probplot(returns, dist="norm", plot=ax2)
        ax2.set_title("Normal Q-Q Plot")

        plt.tight_layout()
        if save:
            save_plot(fig, self.output_dir / f"dist_fit_{bond_name}.png")
        return fig

    def plot_portfolio_var(
        self, returns_matrix, weights, var_portfolio, es_portfolio, save=True
    ):
        fig, ax = plt.subplots(figsize=(12, 7))

        portfolio_returns = np.dot(returns_matrix.T, weights)

        sns.histplot(portfolio_returns, stat="density", kde=True, ax=ax, bins=50)

        ax.axvline(
            -var_portfolio,
            color="red",
            linestyle="--",
            label=f"Portfolio VaR (95%): {var_portfolio/100:.2f}억원",
        )
        ax.axvline(
            -es_portfolio,
            color="darkred",
            linestyle="-.",
            label=f"Portfolio ES (95%): {es_portfolio/100:.2f}억원",
        )

        # x축 범위 조정
        xlim = max(abs(portfolio_returns.min()), abs(portfolio_returns.max()))
        ax.set_xlim(-xlim, xlim)

        ax.set_title("위험 측정을 통한 포트폴리오 수익률 분포")
        ax.legend()

        if save:
            save_plot(fig, self.output_dir / "portfolio_var.png")
        return fig

    def plot_correlation_heatmap(self, returns_matrix, bond_names, save=True):
        fig, ax = plt.subplots(figsize=(15, 12))  # 크기 증가

        # 전치 후 상관관계 계산
        corr_matrix = pd.DataFrame(returns_matrix.T).corr()

        # 라벨 간소화 (예: '우리금융지주' 제외하고 시리즈 번호만)
        short_labels = [name.replace("우리금융지주", "") for name in bond_names]

        sns.heatmap(
            corr_matrix,
            annot=True,
            fmt=".2f",
            square=True,
            cmap="RdBu_r",
            vmin=-1,
            vmax=1,
            xticklabels=short_labels,
            yticklabels=short_labels,
            ax=ax,
        )

        plt.xticks(rotation=45)
        plt.yticks(rotation=0)

        ax.set_title("Return Correlation Matrix")

        plt.tight_layout()
        if save:
            save_plot(fig, self.output_dir / "correlation_heatmap.png")
        return fig

    def create_comprehensive_report(self, data_dict):
        """종합 리스크 분석 보고서 생성"""
        for bond_name, returns in data_dict["individual_returns"].items():
            self.plot_distribution_fit(returns, bond_name)

        self.plot_portfolio_var(
            data_dict["returns_matrix"],
            data_dict["weights"],
            data_dict["portfolio_var"],
            data_dict["portfolio_es"],
        )

        self.plot_correlation_heatmap(
            data_dict["returns_matrix"], data_dict["bond_names"]
        )


def main():
    analyzer = MonteCarloVaRAnalysis()
    results = analyzer.analyze_portfolio()

    visualizer = VaRVisualization()

    # 시각화에 필요한 데이터 구조 생성
    data_dict = {
        "individual_returns": {
            bond: result.simulated_returns
            for bond, result in results["individual_results"].items()
        },
        "returns_matrix": results["returns_matrix"],
        "weights": results["positions"] / np.sum(results["positions"]),
        "portfolio_var": results["portfolio_var"],
        "portfolio_es": results["portfolio_es"],
        "bond_names": results["bond_names"],
    }

    visualizer.create_comprehensive_report(data_dict)


if __name__ == "__main__":
    main()
