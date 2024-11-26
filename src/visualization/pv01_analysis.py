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
from src.analysis.pv01_analysis import PV01Analysis

# 만기별 색상 매핑 수정
MATURITY_COLORS = {
    "1.0": "#FF9999",  # 연한 빨강
    "2.0": "#66B2FF",  # 연한 파랑
    "2.99": "#99FF99",  # 연한 초록
    "3.0": "#FFCC99",  # 연한 주황
    "5.0": "#FF99FF",  # 연한 보라
    "10.0": "#FFD700",  # 골드
}


class PV01Visualization:
    def __init__(self, analysis=None):
        self.analysis = analysis if analysis else PV01Analysis()
        set_plot_style()

        self.project_root = Path(__file__).parent.parent.parent
        self.output_dir = self.project_root / "docs" / "analysis" / "pv01"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def plot_pv01_by_maturity(self, save=True):
        """만기별 PV01 분포 시각화 (개선된 버전)"""
        pv01_data = self.analysis.calculate_portfolio_pv01()

        fig, ax = plt.subplots(figsize=(15, 8))

        # 만기 그룹별로 정렬
        pv01_data = pv01_data.sort_values("만기")

        # 만기별 색상 매핑
        colors = [
            MATURITY_COLORS.get(str(m), COLOR_PALETTE["primary"])
            for m in pv01_data["만기"]
        ]

        bars = ax.bar(pv01_data["종목명"], pv01_data["PV01"], color=colors)

        # 각 막대 위에 값 표시 (소수점 3자리까지)
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{height:.3f}",
                ha="center",
                va="bottom",
                rotation=0,
                fontsize=10,
            )

        ax.set_title("종목별 PV01 분포", pad=20, fontsize=14, fontweight="bold")
        ax.set_xlabel("종목명", fontsize=12)
        ax.set_ylabel("PV01", fontsize=12)
        ax.grid(True, linestyle="--", alpha=0.3)

        # x축 레이블 회전 및 여백 조정
        plt.xticks(rotation=45, ha="right")

        # 범례 추가
        legend_elements = [
            plt.Rectangle((0, 0), 1, 1, facecolor=color, label=f"{maturity}년")
            for maturity, color in MATURITY_COLORS.items()
        ]
        ax.legend(handles=legend_elements, title="만기", loc="upper right")

        plt.tight_layout()

        if save:
            save_plot(fig, self.output_dir / "pv01_by_maturity.png")
        return fig

    def plot_pv01_maturity_scatter(self, save=True):
        """만기와 PV01의 산점도 시각화 (개선된 버전)"""
        pv01_data = self.analysis.calculate_portfolio_pv01()

        fig, ax = plt.subplots(figsize=(12, 8))

        # 발행액 기준 정규화를 위한 최소/최대값 설정
        min_amount = pv01_data["발행액"].min()
        max_amount = pv01_data["발행액"].max()
        norm_size = (
            (pv01_data["발행액"] - min_amount) / (max_amount - min_amount) * 800
        ) + 200

        scatter = ax.scatter(
            pv01_data["만기"],
            pv01_data["PV01"],
            c=[
                MATURITY_COLORS.get(str(m), COLOR_PALETTE["primary"])
                for m in pv01_data["만기"]
            ],
            s=norm_size,
            alpha=0.6,
            edgecolor="white",
            linewidth=1,
        )

        # 각 점에 종목명 표시 (가독성 개선)
        for idx, row in pv01_data.iterrows():
            ax.annotate(
                row["종목명"],
                (row["만기"], row["PV01"]),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=9,
                bbox=dict(facecolor="white", edgecolor="none", alpha=0.7),
            )

        ax.set_title("만기-PV01 관계 분석", pad=20, fontsize=14, fontweight="bold")
        ax.set_xlabel("만기(년)", fontsize=12)
        ax.set_ylabel("PV01", fontsize=12)
        ax.grid(True, linestyle="--", alpha=0.3)

        # 범례 추가
        legend_elements = [
            plt.scatter([], [], c=color, label=f"{maturity}년", s=100)
            for maturity, color in MATURITY_COLORS.items()
        ]
        ax.legend(handles=legend_elements, title="만기", loc="upper right")

        # 발행액 범례 추가
        size_legend = ax.scatter([], [], c="gray", alpha=0.3, s=500)
        ax.legend([size_legend], ["원의 크기: 발행액"], loc="upper left")

        plt.tight_layout()

        if save:
            save_plot(fig, self.output_dir / "pv01_maturity_scatter.png")
        return fig

    def plot_pv01_per_billion(self, save=True):
        """10억원당 PV01 비교 (개선된 버전)"""
        pv01_data = self.analysis.calculate_portfolio_pv01()

        fig, ax = plt.subplots(figsize=(15, 8))

        # 만기 그룹별로 정렬
        pv01_data = pv01_data.sort_values("만기")

        colors = [
            MATURITY_COLORS.get(str(m), COLOR_PALETTE["primary"])
            for m in pv01_data["만기"]
        ]

        bars = ax.bar(pv01_data["종목명"], pv01_data["PV01_per_billion"], color=colors)

        # 각 막대 위에 값 표시 (소수점 2자리까지)
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{height:.2f}",
                ha="center",
                va="bottom",
                rotation=0,
                fontsize=10,
            )

        ax.set_title("10억원당 PV01", pad=20, fontsize=14, fontweight="bold")
        ax.set_xlabel("종목명", fontsize=12)
        ax.set_ylabel("PV01/10억원", fontsize=12)
        ax.grid(True, linestyle="--", alpha=0.3)

        # x축 레이블 회전
        plt.xticks(rotation=45, ha="right")

        # 범례 추가
        legend_elements = [
            plt.Rectangle((0, 0), 1, 1, facecolor=color, label=f"{maturity}년")
            for maturity, color in MATURITY_COLORS.items()
        ]
        ax.legend(handles=legend_elements, title="만기", loc="upper right")

        plt.tight_layout()

        if save:
            save_plot(fig, self.output_dir / "pv01_per_billion.png")
        return fig

    def plot_maturity_group_summary(self, save=True):
        """만기 그룹별 PV01 요약 (개선된 버전)"""
        pv01_data = self.analysis.calculate_portfolio_pv01()

        # 만기 그룹별 집계
        grouped_data = (
            pv01_data.groupby("만기")
            .agg({"PV01": "sum", "발행액": "sum"})
            .reset_index()
        )

        # 비율 계산
        grouped_data["PV01_ratio"] = (
            grouped_data["PV01"] / grouped_data["PV01"].sum() * 100
        )
        grouped_data["amount_ratio"] = (
            grouped_data["발행액"] / grouped_data["발행액"].sum() * 100
        )

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))

        # 색상 매핑
        colors = [
            MATURITY_COLORS.get(str(m), COLOR_PALETTE["primary"])
            for m in grouped_data["만기"]
        ]

        # PV01 파이 차트
        wedges1, texts1, autotexts1 = ax1.pie(
            grouped_data["PV01_ratio"],
            labels=[f"{m}년" for m in grouped_data["만기"]],
            colors=colors,
            autopct="%1.1f%%",
            startangle=90,
            pctdistance=0.85,
        )

        # 발행액 파이 차트
        wedges2, texts2, autotexts2 = ax2.pie(
            grouped_data["amount_ratio"],
            labels=[f"{m}년" for m in grouped_data["만기"]],
            colors=colors,
            autopct="%1.1f%%",
            startangle=90,
            pctdistance=0.85,
        )

        # 글자 크기 및 스타일 조정
        plt.setp(autotexts1 + autotexts2, size=9, weight="bold")
        plt.setp(texts1 + texts2, size=10)

        ax1.set_title("만기별 PV01 비중", pad=20, fontsize=14, fontweight="bold")
        ax2.set_title("만기별 발행액 비중", pad=20, fontsize=14, fontweight="bold")

        plt.tight_layout()

        if save:
            save_plot(fig, self.output_dir / "maturity_group_summary.png")
        return fig

    def create_full_report(self):
        """모든 PV01 분석 차트 생성"""
        print(f"Saving PV01 analysis charts to: {self.output_dir}")

        self.plot_pv01_by_maturity()
        self.plot_pv01_maturity_scatter()
        self.plot_pv01_per_billion()
        self.plot_maturity_group_summary()

        print("PV01 analysis charts have been generated successfully.")


def main():
    visualizer = PV01Visualization()
    visualizer.create_full_report()


if __name__ == "__main__":
    main()
