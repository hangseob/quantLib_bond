"""
FinancePy 내장 미국 휴일 캘린더로 Quarterly(분기) 쿠폰 스케줄 만들기 예시
===========================================================================

이 파일은 FinancePy의 내장 캘린더 `CalendarTypes.UNITED_STATES` 를 사용해
분기(QUARTERLY) 쿠폰 지급일을 생성하고, 영업일 조정(Following)을 반영한
쿠폰 스케줄을 출력합니다.

핵심 포인트
- `Bond(..., freq_type=FrequencyTypes.QUARTERLY, cal_type=CalendarTypes.UNITED_STATES, bd_type=BusDayAdjustTypes.FOLLOWING)`
- 생성된 쿠폰 날짜 리스트는 `bond.cpn_dts` 로 확인
"""

from financepy.products.bonds.bond import Bond
from financepy.utils import BusDayAdjustTypes
from financepy.utils.calendar import Calendar, CalendarTypes
from financepy.utils.date import Date
from financepy.utils.day_count import DayCountTypes
from financepy.utils.frequency import FrequencyTypes


def main() -> None:
    # 예시 채권 파라미터
    issue_dt = Date(15, 1, 2024)
    maturity_dt = Date(15, 1, 2026)  # 2년 만기
    coupon = 0.05  # 5% (연)

    # 미국 휴일 캘린더
    cal_type = CalendarTypes.UNITED_STATES
    calendar = Calendar(cal_type)

    # 분기 쿠폰 + Following 영업일 조정
    bond = Bond(
        issue_dt=issue_dt,
        maturity_dt=maturity_dt,
        coupon=coupon,
        freq_type=FrequencyTypes.QUARTERLY,
        dc_type=DayCountTypes.ACT_ACT_ICMA,
        cal_type=cal_type,
        bd_type=BusDayAdjustTypes.FOLLOWING,
    )

    print("=" * 70)
    print("FinancePy: UNITED_STATES 휴일 반영 Quarterly 쿠폰 스케줄")
    print("=" * 70)
    print(f"Issue: {issue_dt} / Maturity: {maturity_dt}")
    print(f"Coupon: {coupon * 100:.2f}% / Frequency: QUARTERLY")
    print(f"Calendar: {cal_type.name} / BusDayAdjust: FOLLOWING")
    print("")

    print("[Coupon dates (adjusted)]")
    for dt in bond.cpn_dts:
        is_hol = calendar.is_holiday(dt)
        tag = "HOLIDAY" if is_hol else "BUSINESS"
        print(f"  {str(dt):>11}  {tag}")

    # 참고: FinancePy 내부 캘린더 기준 휴일 리스트(연도별) 일부 출력
    print("")
    print("[Holiday samples (by year)]")
    for y in range(issue_dt.y, maturity_dt.y + 1):
        year_holidays = calendar.get_holiday_list(y)
        print(f"  {y}: {len(year_holidays)} holidays")
        for dt in year_holidays[:10]:
            print(f"    {dt}")
        if len(year_holidays) > 10:
            print("    ...")


if __name__ == "__main__":
    main()


