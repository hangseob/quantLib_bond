"""
FinancePy + CSV 휴일로 쿠폰(이표) 스케줄 만들기 예시
===================================================

FinancePy의 `Calendar`는 내장 캘린더(UNITED_STATES 등)만 제공하고,
CSV로 커스텀 휴일을 "캘린더에 추가"하는 API는 제공하지 않습니다.

그래서 이 예시는:
- FinancePy의 `Date`를 사용해 쿠폰 날짜(반기)를 생성하고
- CSV(`korea_holidays.csv`)로 읽은 휴일 + 주말을 기준으로
  Following(다음 영업일) 방식으로 날짜를 조정하여
  "커스텀 휴일을 반영한" 쿠폰 스케줄을 만드는 방법을 보여줍니다.

필요 파일:
- korea_holidays.csv  (date,description 컬럼. YYYY-MM-DD)
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from typing import Iterable, List, Set, Tuple

from financepy.utils.date import Date


@dataclass(frozen=True)
class CouponScheduleConfig:
    issue_dt: Date
    maturity_dt: Date
    months: int = 6  # Semi-annual
    include_issue_date: bool = True
    include_maturity_date: bool = True


def load_holidays_csv(filepath: str) -> Set[Tuple[int, int, int]]:
    """CSV(date=YYYY-MM-DD)를 (y,m,d) 튜플 set으로 로드."""
    holidays: Set[Tuple[int, int, int]] = set()
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            y, m, d = map(int, row["date"].split("-"))
            holidays.add((y, m, d))
    return holidays


def is_weekend(dt: Date) -> bool:
    """FinancePy Date.weekday는 0=Mon ... 6=Sun."""
    wd = dt.weekday
    return wd == 5 or wd == 6  # Sat, Sun


def is_holiday(dt: Date, holiday_set: Set[Tuple[int, int, int]]) -> bool:
    return (dt.y, dt.m, dt.d) in holiday_set


def adjust_following(dt: Date, holiday_set: Set[Tuple[int, int, int]]) -> Date:
    """Following: 휴일/주말이면 다음 영업일로 이동."""
    d = dt
    while is_weekend(d) or is_holiday(d, holiday_set):
        d = d.add_days(1)
    return d


def generate_unadjusted_coupon_dates(cfg: CouponScheduleConfig) -> List[Date]:
    """
    Backward 방식으로 Unadjusted 쿠폰 날짜 생성 (maturity -> issue로 역산).
    """
    dates: List[Date] = []
    d = cfg.maturity_dt

    if cfg.include_maturity_date:
        dates.append(d)

    while True:
        d = d.add_months(-cfg.months)
        if d < cfg.issue_dt:
            break
        dates.append(d)

    if cfg.include_issue_date and (len(dates) == 0 or dates[-1] != cfg.issue_dt):
        dates.append(cfg.issue_dt)

    # 현재 maturity->issue로 내려오며 append 했으므로 정렬
    dates_sorted = sorted(dates)
    return dates_sorted


def build_coupon_schedule_following(
    cfg: CouponScheduleConfig, holiday_set: Set[Tuple[int, int, int]]
) -> List[Date]:
    """Unadjusted 스케줄 생성 후 Following으로 조정."""
    unadj = generate_unadjusted_coupon_dates(cfg)
    adj = [adjust_following(d, holiday_set) for d in unadj]
    return adj


def main() -> None:
    holidays = load_holidays_csv("korea_holidays.csv")

    cfg = CouponScheduleConfig(
        issue_dt=Date(1, 1, 2024),
        maturity_dt=Date(1, 1, 2029),
        months=6,
    )

    unadjusted = generate_unadjusted_coupon_dates(cfg)
    adjusted = build_coupon_schedule_following(cfg, holidays)

    print("=" * 70)
    print("FinancePy + CSV 휴일: 쿠폰(이표) 스케줄 생성 예시")
    print("=" * 70)
    print(f"CSV 휴일 개수(주말 제외): {len(holidays)}")
    print(f"Issue: {cfg.issue_dt} / Maturity: {cfg.maturity_dt} / Freq: {12//cfg.months} per year")
    print("")

    print("[Unadjusted coupon dates]")
    for d in unadjusted:
        print(f"  {d}  (weekday={d.weekday})")

    print("")
    print("[Following adjusted coupon dates (weekend + CSV holidays)]")
    for d0, d1 in zip(unadjusted, adjusted):
        moved = "" if d0 == d1 else f"  (moved from {d0})"
        print(f"  {d1}{moved}")


if __name__ == "__main__":
    main()


