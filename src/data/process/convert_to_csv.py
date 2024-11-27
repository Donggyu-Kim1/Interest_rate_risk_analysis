import pandas as pd
import os

# 입력/출력 경로 설정
raw_data_path = "data/raw/market_data"
processed_data_path = "data/processed/market_data"

# 디렉토리가 없으면 생성
if not os.path.exists(processed_data_path):
    os.makedirs(processed_data_path)


# 국고채/통안채 데이터 처리
def process_govt_bond_rates():
    # Excel 파일 읽기
    df = pd.read_excel(f"{raw_data_path}/govt_bond_rates.xls")
    # CSV로 저장
    df.to_csv(
        f"{processed_data_path}/govt_bond_rates.csv", index=False, encoding="utf-8"
    )


# 회사채 유통수익률 데이터 처리
def process_woori_bond_yields():
    for file in os.listdir(f"{raw_data_path}/woori_bond_yields"):
        if file.endswith(".txt"):
            # txt 파일 읽기
            df = pd.read_csv(
                f"{raw_data_path}/woori_bond_yields/{file}", delimiter=","
            )  # 구분자는 실제 파일에 맞게 조정

            # 파일명에서 확장자 제거
            output_filename = os.path.splitext(file)[0] + ".csv"

            # CSV로 저장
            df.to_csv(
                f"{processed_data_path}/{output_filename}",
                index=False,
                encoding="utf-8",
            )


if __name__ == "__main__":
    process_govt_bond_rates()
    process_woori_bond_yields()
