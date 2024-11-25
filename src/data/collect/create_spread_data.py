import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path


def load_data():
    """데이터 파일들을 로드하는 함수"""
    # 기본 경로 설정
    processed_dir = Path("data/processed")

    # 우리금융지주 채권 기본 정보 로드
    woori_bonds = pd.read_csv(
        processed_dir / "bond_info/woori_bond_info.csv",
        parse_dates=["발행일", "만기일"],
    )

    # 국고채 금리 데이터 로드
    govt_rates = pd.read_csv(
        processed_dir / "market_data/govt_bond_rates.csv", parse_dates=["일자"]
    )

    return woori_bonds, govt_rates


def find_matching_govt_rate(row, govt_rates):
    """각 회사채의 발행시만기에 맞는 국고채 금리를 찾는 함수"""
    maturity = row["발행시만기"]

    if maturity <= 1:
        return govt_rates["국고채권(1년)"]
    elif maturity <= 3:
        return govt_rates["국고채권(3년)"]
    elif maturity <= 5:
        return govt_rates["국고채권(5년)"]
    else:
        return govt_rates["국고채권(10년)"]


def calculate_spreads():
    """스프레드 계산 및 데이터셋 생성"""
    # 데이터 로드
    woori_bonds, govt_rates = load_data()

    # 결과를 저장할 리스트
    spread_data_list = []

    # 각 채권별로 스프레드 계산
    for _, bond in woori_bonds.iterrows():
        # 채권 코드로 해당 채권의 시장 데이터 파일 경로 생성
        bond_market_data_path = f"data/processed/market_data/woori_bond_data_{bond['종목명'].split('우리금융지주')[1]}.csv"

        try:
            # 해당 채권의 시장 데이터 로드
            bond_market_data = pd.read_csv(bond_market_data_path, parse_dates=["일자"])

            # 정부채 데이터와 날짜 기준으로 병합
            merged_data = pd.merge(bond_market_data, govt_rates, on="일자", how="inner")

            # 해당 만기에 맞는 국고채 금리 선택
            govt_rate = find_matching_govt_rate(bond, merged_data)

            # 스프레드 계산
            merged_data["스프레드"] = (
                merged_data["채권평가사 평균수익률_수익률"] - govt_rate
            )

            # 결과 데이터 구성
            result_data = pd.DataFrame(
                {
                    "일자": merged_data["일자"],
                    "종목명": bond["종목명"],
                    "발행시만기": bond["발행시만기"],
                    "잔존만기": bond["잔존만기"],
                    "회사채수익률": merged_data["채권평가사 평균수익률_수익률"],
                    "국고채수익률": govt_rate,
                    "스프레드": merged_data["스프레드"],
                }
            )

            spread_data_list.append(result_data)

        except FileNotFoundError:
            print(f"Warning: Market data not found for {bond['종목명']}")
            continue

    # 전체 데이터 합치기
    final_spread_data = pd.concat(spread_data_list, ignore_index=True)

    # 결과 저장
    output_dir = Path("data/processed/spread_data")
    output_dir.mkdir(parents=True, exist_ok=True)

    final_spread_data.to_csv(
        output_dir / "woori_bond_spreads.csv", index=False, encoding="utf-8"
    )

    return final_spread_data


def main():
    """메인 실행 함수"""
    try:
        spread_data = calculate_spreads()
        print("스프레드 데이터 생성 완료")
        print("\n기본 통계:")
        print(
            spread_data.groupby("종목명")["스프레드"]
            .agg(["mean", "min", "max", "std"])
            .round(3)
        )

    except Exception as e:
        print(f"Error occurred: {str(e)}")


if __name__ == "__main__":
    main()
