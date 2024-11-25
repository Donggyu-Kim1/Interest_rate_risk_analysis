from pathlib import Path
import pandas as pd


def get_project_root():
    """프로젝트 루트 경로 반환"""
    return Path(__file__).parent.parent.parent


def load_bond_info():
    """우리금융지주 채권 기본 정보 로드"""
    root_dir = get_project_root()
    file_path = root_dir / "data" / "processed" / "bond_info" / "woori_bond_info.csv"

    df = pd.read_csv(file_path, parse_dates=["발행일", "만기일"])
    return df


def load_govt_rates():
    """국고채 금리 데이터 로드"""
    root_dir = get_project_root()
    file_path = root_dir / "data" / "processed" / "market_data" / "govt_bond_rates.csv"

    df = pd.read_csv(file_path, parse_dates=["일자"])
    return df


def load_spread_data():
    """스프레드 데이터 로드"""
    root_dir = get_project_root()
    file_path = (
        root_dir / "data" / "processed" / "spread_data" / "woori_bond_spreads.csv"
    )

    df = pd.read_csv(file_path, parse_dates=["일자"])
    return df


def get_bond_codes():
    """채권 시리즈 코드 목록 반환"""
    df = load_bond_info()
    # 종목명에서 'O-O' 또는 'O' 패턴 추출
    series_codes = df["종목명"].str.extract(r"우리금융지주(\d+(?:-\d+)?)")
    return series_codes[0].unique().tolist()


def load_individual_bond_data(series_code):
    """개별 채권 시장 데이터 로드"""
    root_dir = get_project_root()
    file_path = (
        root_dir
        / "data"
        / "processed"
        / "market_data"
        / f"woori_bond_data_{series_code}.csv"
    )

    df = pd.read_csv(file_path, parse_dates=["일자"])
    return df


def load_all_bond_data():
    """모든 채권 데이터 로드"""
    series_codes = get_bond_codes()
    all_data = {}

    for code in series_codes:
        all_data[code] = load_individual_bond_data(code)

    return all_data
