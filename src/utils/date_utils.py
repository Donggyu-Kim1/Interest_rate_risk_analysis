import pandas as pd
from datetime import datetime, timedelta
import numpy as np


def calculate_days_between(start_date, end_date):
    """두 날짜 사이의 일수를 계산"""
    return (end_date - start_date).days


def calculate_years_between(start_date, end_date):
    """두 날짜 사이의 연수를 계산 (소수점 2자리까지)"""
    days = calculate_days_between(start_date, end_date)
    return round(days / 365.25, 2)


def get_remaining_maturity(maturity_date, base_date=None):
    """특정 기준일 기준 잔존만기 계산"""
    if base_date is None:
        base_date = pd.Timestamp.now()
    return calculate_years_between(base_date, maturity_date)


def get_payment_dates(start_date, maturity_date, payment_freq=3):
    """이자지급일 배열 생성

    Parameters:
    -----------
    start_date : datetime
        발행일
    maturity_date : datetime
        만기일
    payment_freq : int
        이자지급 주기 (월 단위, 기본값 3개월)

    Returns:
    --------
    list : 이자지급일 리스트
    """
    payment_dates = []
    current_date = start_date

    while current_date < maturity_date:
        current_date += pd.DateOffset(months=payment_freq)
        if current_date < maturity_date:
            payment_dates.append(current_date)

    payment_dates.append(maturity_date)
    return payment_dates


def get_last_business_day(year, month):
    """해당 월의 마지막 영업일 반환"""
    last_day = pd.Timestamp(year=year, month=month, day=1) + pd.offsets.MonthEnd(1)
    while last_day.weekday() > 4:  # 주말인 경우
        last_day -= pd.Timedelta(days=1)
    return last_day


def create_date_range(start_date, end_date, freq="B"):
    """영업일 기준 날짜 범위 생성

    Parameters:
    -----------
    start_date : datetime
        시작일
    end_date : datetime
        종료일
    freq : str
        주기 ('B': 영업일, 'M': 월말, 'Q': 분기말)

    Returns:
    --------
    DatetimeIndex : 날짜 범위
    """
    return pd.date_range(start=start_date, end=end_date, freq=freq)


def is_business_day(date):
    """영업일 여부 확인"""
    return bool(len(pd.bdate_range(date, date)))


def get_next_business_day(date):
    """다음 영업일 반환"""
    next_day = date + pd.Timedelta(days=1)
    while not is_business_day(next_day):
        next_day += pd.Timedelta(days=1)
    return next_day


def quarter_end_dates(start_date, end_date):
    """분기말 날짜 리스트 반환"""
    return pd.date_range(start=start_date, end=end_date, freq="Q")


def format_date(date, format="%Y-%m-%d"):
    """날짜를 지정된 형식의 문자열로 변환"""
    return date.strftime(format)


def parse_date(date_str, format="%Y-%m-%d"):
    """문자열을 datetime 객체로 변환"""
    return datetime.strptime(date_str, format)
