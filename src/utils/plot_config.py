import matplotlib.pyplot as plt
import seaborn as sns


def set_plot_style():
    """기본 plot 스타일 설정"""
    sns.set_style("whitegrid")  # seaborn의 스타일 직접 설정
    sns.set_palette("husl")

    # 폰트 설정
    plt.rcParams["font.family"] = "NanumGothic"  # 한글 폰트
    plt.rcParams["axes.unicode_minus"] = False  # 마이너스 기호 깨짐 방지

    # 그래프 크기 설정
    plt.rcParams["figure.figsize"] = [10, 6]

    # 그리드 설정
    plt.rcParams["grid.linestyle"] = "--"
    plt.rcParams["grid.alpha"] = 0.5


# 색상 팔레트 정의
COLOR_PALETTE = {
    "primary": "#1f77b4",  # 기본 색상
    "secondary": "#ff7f0e",  # 보조 색상
    "accent": "#2ca02c",  # 강조 색상
    "negative": "#d62728",  # 음수/하락
    "positive": "#2ca02c",  # 양수/상승
    "neutral": "#7f7f7f",  # 중립
}

# 만기 그룹별 색상 정의
MATURITY_COLORS = {
    "1년": "#1f77b4",
    "2년": "#ff7f0e",
    "3년": "#2ca02c",
    "5년": "#d62728",
    "10년": "#9467bd",
}


def format_thousands(x, pos):
    """천단위 구분자 포맷팅"""
    return "{:,.0f}".format(x)


def format_percentage(x, pos):
    """퍼센트 포맷팅"""
    return "{:.2f}%".format(x)


# 그래프 저장 설정
FIGURE_DPI = 300
FIGURE_BBOX_INCHES = "tight"


def save_plot(fig, filename):
    """그래프 저장 함수"""
    fig.savefig(filename, dpi=FIGURE_DPI, bbox_inches=FIGURE_BBOX_INCHES)
    plt.close(fig)
