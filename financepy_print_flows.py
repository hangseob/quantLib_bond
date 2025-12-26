"""
FinancePy Bond cashflow printing example
=======================================

요청 사양:
- Issue:    2024-12-26
- Maturity: 2025-12-26
- Coupon:   4% (annual)
- Frequency: Quarterly
- DayCount: Act/360
- Holidays: 사용 안함 (CalendarTypes.NONE)

이 스크립트는 FinancePy `Bond` 객체를 생성하고,
쿠폰 일정(cpn_dts)과 flow_amounts, 그리고 원금 포함 최종 상환 플로우를 출력합니다.
"""

from financepy.utils.date import Date
from financepy.utils.frequency import FrequencyTypes
from financepy.utils.day_count import DayCountTypes
from financepy.utils.calendar import CalendarTypes, BusDayAdjustTypes
from financepy.products.bonds.bond import Bond


def main():
    issue_dt = Date(26, 12, 2024)
    maturity_dt = Date(26, 1, 2026)

    coupon_rate = 0.04
    face = 100.0

    bond = Bond(
        issue_dt=issue_dt,
        maturity_dt=maturity_dt,
        coupon=coupon_rate,
        freq_type=FrequencyTypes.QUARTERLY,
        dc_type=DayCountTypes.ACT_360,
        cal_type=CalendarTypes.NONE,  # 휴일/주말 모두 무시(모든 날이 영업일)
        bd_type=BusDayAdjustTypes.NONE,  # 날짜 조정 없음(언어 그대로 schedule)
    )

    print("=" * 80)
    print("FinancePy Bond - Cashflows")
    print("=" * 80)
    print(f"Issue     : {issue_dt}")
    print(f"Maturity  : {maturity_dt}")
    print(f"Coupon    : {coupon_rate * 100:.2f}%")
    print(f"Frequency : {FrequencyTypes.QUARTERLY}")
    print(f"DayCount  : {DayCountTypes.ACT_360}")
    print(f"Calendar  : {CalendarTypes.NONE} (no holidays/weekends)")
    print(f"Face      : {face}")

    print("\n[cpn_dts] (unadjusted coupon dates used in analytics)")
    for i, dt in enumerate(bond.cpn_dts):
        print(f"{i:02d}: {dt}")

    print("\n[flow_amounts] (per-1 notional, coupon only; principal is not included here)")
    for i, fa in enumerate(bond.flow_amounts):
        print(f"{i:02d}: {fa:.10f}")

    print("\n[cashflows] (face-scaled; includes redemption at maturity)")
    # FinancePy의 Bond.print_payments는 settle_dt 이후의 flows를 출력합니다.
    # issue_dt를 넣으면 발행 이후의 모든 쿠폰 및 상환을 출력합니다.
    bond.print_payments(settle_dt=issue_dt, face=face)


if __name__ == "__main__":
    main()


