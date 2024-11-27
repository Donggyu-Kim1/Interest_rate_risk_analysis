import pandas as pd
from datetime import datetime

# 채권 기본 정보 데이터 생성
bond_data = {
    "종목명": [
        "우리금융지주4-1",
        "우리금융지주5-1",
        "우리금융지주8-1",
        "우리금융지주9",
        "우리금융지주6-2",
        "우리금융지주5-2",
        "우리금융지주8-2",
        "우리금융지주10",
        "우리금융지주6-3",
        "우리금융지주7",
        "우리금융지주4-2",
        "우리금융지주2-2",
    ],
    "표준코드": [
        "KR6316141C68",
        "KR6316141D67",
        "KR6316141E74",
        "KR6316143E72",
        "KR6316143D99",
        "KR6316142D66",
        "KR6316142E73",
        "KR6316144E71",
        "KR6316144D98",
        "KR6316141DB3",
        "KR6316142C67",
        "KR6316142B76",
    ],
    "발행일": [
        "2022-06-08",
        "2023-06-09",
        "2024-07-08",
        "2024-07-09",
        "2023-09-08",
        "2023-06-09",
        "2024-07-08",
        "2024-07-24",
        "2023-09-08",
        "2023-11-22",
        "2022-06-08",
        "2021-07-14",
    ],
    "만기일": [
        "2025-06-05",
        "2025-06-09",
        "2025-07-08",
        "2025-07-09",
        "2025-09-08",
        "2026-06-09",
        "2026-07-08",
        "2026-07-24",
        "2026-09-08",
        "2026-11-20",
        "2027-06-08",
        "2031-07-14",
    ],
    "발행액": [
        30000,
        70000,
        50000,
        100000,
        60000,
        80000,
        50000,
        100000,
        60000,
        80000,
        50000,
        60000,
    ],
    "표면금리": [
        3.785,
        3.997,
        3.396,
        3.383,
        4.189,
        4.041,
        3.325,
        3.315,
        4.249,
        4.165,
        3.896,
        2.193,
    ],
    "이자지급방법": ["이표채"] * 12,
    "이자지급주기": [3] * 12,
}

# DataFrame 생성
df = pd.DataFrame(bond_data)

# 날짜 형식 변환
df["발행일"] = pd.to_datetime(df["발행일"])
df["만기일"] = pd.to_datetime(df["만기일"])


# 발행시 만기 계산 (연단위)
df["발행시만기"] = ((df["만기일"] - df["발행일"]).dt.days / 365.25).round(2)

# 현재 시점 기준 잔존만기 계산
current_date = pd.Timestamp("2024-11-25")  # 현재 날짜
df["잔존만기"] = ((df["만기일"] - current_date).dt.days / 365.25).round(2)

# 만기그룹은 발행시만기 기준으로 표시
df["만기그룹"] = df["발행시만기"].astype(str) + "년"

# 만기 순으로 정렬
df = df.sort_values(["발행시만기"])

# CSV 파일로 저장
df.to_csv("data/raw/bond_info/woori_bond_info.csv", index=False, encoding="utf-8")

print("채권 기본 정보 데이터 생성 완료")
print("\n데이터 샘플:")
print(df.head())
print("\n만기그룹별 통계:")
print(
    df.groupby("만기그룹")
    .agg(
        {
            "종목명": "count",
            "발행액": ["sum", "mean"],
            "표면금리": ["mean", "min", "max"],
            "잔존만기": ["mean", "min", "max"],
        }
    )
    .round(2)
)
