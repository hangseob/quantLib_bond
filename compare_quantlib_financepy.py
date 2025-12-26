"""
QuantLib vs FinancePy 채권 계산 결과 비교
========================================

두 라이브러리의 계산 결과를 비교하여 일치 여부를 확인합니다.
이번 버전은 **주말(Sat/Sun)만 비영업일**로 사용하고(휴일 미적용),
**Act/360** 컨벤션으로 비교합니다.
"""

import QuantLib as ql
from financepy.utils.date import Date
from financepy.utils.day_count import DayCountTypes, DayCount
from financepy.utils.frequency import FrequencyTypes
from financepy.utils.calendar import CalendarTypes, Calendar
from financepy.utils import BusDayAdjustTypes, DateGenRuleTypes
from financepy.products.bonds.bond import Bond, YTMCalcType
import csv


# =============================================================================
# CSV에서 휴일 읽기
# =============================================================================

def load_holidays_from_csv(filepath='korea_holidays.csv'):
    """CSV 파일에서 휴일 목록 읽기"""
    holidays = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            date_str = row['date']
            year, month, day = map(int, date_str.split('-'))
            holidays.append((year, month, day))
    return holidays


def create_quantlib_calendar_from_csv(holidays):
    """CSV 휴일로 QuantLib 커스텀 달력 생성
    
    Note: FinancePy가 커스텀 휴일을 지원하지 않으므로,
    이 예제에서는 **주말만 비영업일(holiday 없음)**로 맞추기 위해
    WeekendsOnly 달력을 사용합니다.
    """
    # 주말(Sat/Sun)만 비영업일
    return ql.WeekendsOnly()


def create_financepy_calendar_from_csv(holidays):
    """CSV 휴일로 FinancePy 커스텀 달력 생성"""
    # FinancePy Date 리스트로 변환
    fp_holidays = []
    for year, month, day in holidays:
        fp_holidays.append(Date(day, month, year))
    
    return fp_holidays


# =============================================================================
# 설정 비교 출력
# =============================================================================

def print_settings_comparison(ql_calendar, ql_settlement, fp_settlement, num_holidays):
    """두 라이브러리 설정 비교 출력"""
    print("\n" + "=" * 80)
    print("설정 비교")
    print("=" * 80)
    
    print(f"\n{'항목':20} {'QuantLib':25} {'FinancePy':25}")
    print("-" * 80)
    print(f"{'평가일':20} {'2024-12-26':25} {'2024-12-26':25}")
    print(f"{'결제일':20} {str(ql_settlement):25} {str(fp_settlement):25}")
    print(f"{'달력':20} {'WeekendsOnly':25} {'WEEKEND':25}")
    print(f"{'휴일 수 (CSV)':20} {str(num_holidays):25} {'(미적용)':25}")
    print(f"{'Day Count':20} {'Actual360':25} {'ACT_360':25}")
    print(f"{'쿠폰 빈도':20} {'Semiannual':25} {'SEMI_ANNUAL':25}")
    print(f"{'영업일 조정':20} {'Unadjusted':25} {'NONE':25}")


# =============================================================================
# QuantLib 채권 생성
# =============================================================================

def create_quantlib_bond(calendar):
    """QuantLib 고정금리채권 생성"""
    evaluation_date = ql.Date(26, 12, 2024)
    ql.Settings.instance().evaluationDate = evaluation_date
    
    issue_date = ql.Date(1, 1, 2024)
    maturity_date = ql.Date(1, 1, 2029)
    face_value = 100.0
    coupon_rate = 0.045
    
    # Act/360
    day_count = ql.Actual360()
    
    # Unadjusted: 쿠폰 날짜에 영업일 조정 안 함 (FinancePy와 동일)
    schedule = ql.Schedule(
        issue_date,
        maturity_date,
        ql.Period(ql.Semiannual),
        calendar,
        ql.Unadjusted,  # 영업일 조정 안 함
        ql.Unadjusted,
        ql.DateGeneration.Backward,
        False
    )
    
    # settlement_days = 0으로 설정하여 결제일 직접 제어
    bond = ql.FixedRateBond(0, face_value, schedule, [coupon_rate], day_count)
    
    # 결제일: 평가일 + 2 영업일
    settlement_date = calendar.advance(evaluation_date, 2, ql.Days)
    
    return bond, day_count, settlement_date, schedule, face_value, coupon_rate


# =============================================================================
# FinancePy 채권 생성
# =============================================================================

def create_financepy_bond(fp_settlement_date):
    """FinancePy 고정금리채권 생성"""
    issue_dt = Date(1, 1, 2024)
    maturity_dt = Date(1, 1, 2029)
    coupon_rate = 0.045
    
    # 주말(Sat/Sun)만 비영업일 + Unadjusted(날짜 이동 없음)
    bond = Bond(
        issue_dt=issue_dt,
        maturity_dt=maturity_dt,
        coupon=coupon_rate,
        freq_type=FrequencyTypes.SEMI_ANNUAL,
        dc_type=DayCountTypes.ACT_360,
        cal_type=CalendarTypes.WEEKEND,  # 주말만 비영업일
        bd_type=BusDayAdjustTypes.NONE  # 영업일 조정 안 함
    )
    
    return bond, fp_settlement_date


# =============================================================================
# QuantLib 계산 함수들
# =============================================================================

def ql_yield_to_price(bond, yield_rate, day_count, settlement_date):
    """QuantLib: 수익률 → 가격"""
    ir = ql.InterestRate(yield_rate, day_count, ql.Compounded, ql.Semiannual)
    clean_price = ql.BondFunctions.cleanPrice(bond, ir, settlement_date)
    return clean_price


def ql_price_to_yield(bond, clean_price, day_count, settlement_date):
    """QuantLib: 가격 → 수익률"""
    bond_price = ql.BondPrice(clean_price, ql.BondPrice.Clean)
    ytm = ql.BondFunctions.bondYield(
        bond, bond_price, day_count, ql.Compounded, ql.Semiannual, settlement_date
    )
    return ytm


def ql_durations(bond, yield_rate, day_count, settlement_date):
    """QuantLib: 듀레이션 계산"""
    ir = ql.InterestRate(yield_rate, day_count, ql.Compounded, ql.Semiannual)
    
    macaulay = ql.BondFunctions.duration(bond, ir, ql.Duration.Macaulay, settlement_date)
    modified = ql.BondFunctions.duration(bond, ir, ql.Duration.Modified, settlement_date)
    convexity = ql.BondFunctions.convexity(bond, ir, settlement_date)
    
    return macaulay, modified, convexity


# =============================================================================
# FinancePy 계산 함수들
# =============================================================================

def fp_yield_to_price(bond, settlement_date, yield_rate):
    """FinancePy: 수익률 → 가격"""
    clean_price = bond.clean_price_from_ytm(settlement_date, yield_rate, YTMCalcType.US_STREET)
    return clean_price


def fp_price_to_yield(bond, settlement_date, clean_price):
    """FinancePy: 가격 → 수익률"""
    ytm = bond.yield_to_maturity(settlement_date, clean_price, YTMCalcType.US_STREET)
    return ytm


def fp_durations(bond, settlement_date, yield_rate):
    """FinancePy: 듀레이션 계산"""
    macaulay = bond.macauley_duration(settlement_date, yield_rate, YTMCalcType.US_STREET)
    modified = bond.modified_duration(settlement_date, yield_rate, YTMCalcType.US_STREET)
    convexity = bond.convexity_from_ytm(settlement_date, yield_rate, YTMCalcType.US_STREET)
    
    return macaulay, modified, convexity


# =============================================================================
# 쿠폰 스케줄/쿠폰금액(Act/360) 비교용 헬퍼
# =============================================================================

def ql_date_to_tuple(dt: ql.Date):
    return (dt.year(), dt.month(), dt.dayOfMonth())


def fp_date_to_tuple(dt: Date):
    return (dt.y, dt.m, dt.d)


def ql_coupon_schedule_from_schedule(schedule: ql.Schedule):
    """QuantLib Schedule에서 (start_dt, end_dt) 리스트 생성"""
    dts = list(schedule)
    periods = []
    for i in range(1, len(dts)):
        periods.append((dts[i - 1], dts[i]))
    return periods


def fp_coupon_schedule_from_bond(bond: Bond):
    """FinancePy Bond에서 (start_dt, end_dt) 리스트 생성 (unadjusted coupon dates)"""
    dts = list(bond.cpn_dts)
    periods = []
    for i in range(1, len(dts)):
        periods.append((dts[i - 1], dts[i]))
    return periods


def ql_coupon_amounts_act360(periods, coupon_rate, face_value):
    dc = ql.Actual360()
    rows = []
    for start_dt, end_dt in periods:
        accrual = dc.yearFraction(start_dt, end_dt)
        amt = face_value * coupon_rate * accrual
        rows.append((start_dt, end_dt, accrual, amt))
    return rows


def fp_coupon_amounts_act360(periods, coupon_rate, face_value):
    dc = DayCount(DayCountTypes.ACT_360)
    rows = []
    for start_dt, end_dt in periods:
        accrual = dc.year_frac(start_dt, end_dt)[0]
        amt = face_value * coupon_rate * accrual
        rows.append((start_dt, end_dt, accrual, amt))
    return rows


def compare_coupon_schedules_and_amounts(
    ql_periods_rows,
    fp_periods_rows,
    amt_tolerance=1e-10,
    accrual_tolerance=1e-12,
):
    """기간(start/end), accrual, coupon amount를 순서대로 비교"""
    print("\n" + "=" * 80)
    print("0. 쿠폰 스케줄 및 쿠폰금액 비교 (Act/360)")
    print("=" * 80)

    all_passed = True
    n = min(len(ql_periods_rows), len(fp_periods_rows))
    if len(ql_periods_rows) != len(fp_periods_rows):
        print(f"[WARN] 기간 개수 불일치: QuantLib={len(ql_periods_rows)}, FinancePy={len(fp_periods_rows)}")
        all_passed = False

    print(f"\n{'기간(start->end)':32} {'Accrual(QL)':>12} {'Accrual(FP)':>12} {'Coupon(QL)':>12} {'Coupon(FP)':>12}  결과")
    print("-" * 90)

    for i in range(n):
        ql_start, ql_end, ql_acc, ql_amt = ql_periods_rows[i]
        fp_start, fp_end, fp_acc, fp_amt = fp_periods_rows[i]

        date_match = (ql_date_to_tuple(ql_start) == fp_date_to_tuple(fp_start)) and (
            ql_date_to_tuple(ql_end) == fp_date_to_tuple(fp_end)
        )
        acc_match = abs(ql_acc - fp_acc) <= accrual_tolerance
        amt_match = abs(ql_amt - fp_amt) <= amt_tolerance

        ok = date_match and acc_match and amt_match
        all_passed = all_passed and ok

        period_str = f"{ql_start.ISO()}->{ql_end.ISO()}"
        print(f"{period_str:32} {ql_acc:12.10f} {fp_acc:12.10f} {ql_amt:12.8f} {fp_amt:12.8f}  {'PASS' if ok else 'FAIL'}")

    return all_passed


# =============================================================================
# 비교 함수
# =============================================================================

def compare_values(name, ql_val, fp_val, tolerance=0.01):
    """두 값을 비교하고 결과 출력"""
    diff = abs(ql_val - fp_val)
    pct_diff = (diff / abs(ql_val)) * 100 if ql_val != 0 else 0
    match = "PASS" if diff < tolerance else "FAIL"
    
    print(f"{name:25} {ql_val:>12.4f} {fp_val:>12.4f} {diff:>10.4f} {pct_diff:>8.2f}%  {match}")
    
    return diff < tolerance


# =============================================================================
# 메인 비교
# =============================================================================

def main():
    print("=" * 80)
    print("QuantLib vs FinancePy 채권 계산 결과 비교")
    print("=" * 80)
    print("(달력: 주말만 비영업일, 휴일 미적용 / DayCount: Act/360)")
    
    # CSV에서 휴일 로드
    holidays = load_holidays_from_csv('korea_holidays.csv')
    print(f"\nCSV에서 {len(holidays)}개 휴일 로드 완료")
    
    # QuantLib 커스텀 달력 생성
    ql_calendar = create_quantlib_calendar_from_csv(holidays)
    
    # 결제일 계산 (평가일 + 2 영업일, 주말만 비영업일)
    ql_eval_date = ql.Date(26, 12, 2024)
    ql.Settings.instance().evaluationDate = ql_eval_date
    ql_settlement = ql_calendar.advance(ql_eval_date, 2, ql.Days)

    fp_eval_date = Date(26, 12, 2024)
    fp_calendar = Calendar(CalendarTypes.WEEKEND)
    fp_settlement_calc = fp_calendar.add_business_days(fp_eval_date, 2)
    fp_settlement = fp_settlement_calc

    # 채권 생성
    ql_bond, day_count, _, ql_schedule, face_value, coupon_rate = create_quantlib_bond(ql_calendar)
    fp_bond, fp_settlement = create_financepy_bond(fp_settlement)
    
    # 설정 비교 출력
    print_settings_comparison(ql_calendar, ql_settlement, fp_settlement, len(holidays))
    
    print("\n" + "=" * 80)
    print("채권 정보")
    print("=" * 80)
    print(f"  쿠폰: 4.5% (반기)")
    print(f"  만기: 2029-01-01 (약 4년)")
    print(f"  액면: 100")
    print(f"  QuantLib 결제일: {ql_settlement}")
    print(f"  FinancePy 결제일: {fp_settlement}")
    
    all_passed = True

    # =========================================================================
    # 0. 쿠폰 스케줄 및 쿠폰금액(Act/360) 비교
    # =========================================================================
    ql_periods = ql_coupon_schedule_from_schedule(ql_schedule)
    fp_periods = fp_coupon_schedule_from_bond(fp_bond)

    ql_rows = ql_coupon_amounts_act360(ql_periods, coupon_rate, face_value)
    fp_rows = fp_coupon_amounts_act360(fp_periods, coupon_rate, face_value)

    passed0 = compare_coupon_schedules_and_amounts(ql_rows, fp_rows, amt_tolerance=1e-10, accrual_tolerance=1e-12)
    all_passed = all_passed and passed0
    
    # =========================================================================
    # 1. 수익률 → 가격 비교
    # =========================================================================
    print("\n" + "=" * 80)
    print("1. 수익률 -> 가격 비교")
    print("=" * 80)
    print(f"\n{'수익률':25} {'QuantLib':>12} {'FinancePy':>12} {'차이':>10} {'차이%':>8}  결과")
    print("-" * 80)
    
    test_yields = [0.03, 0.04, 0.045, 0.05, 0.06]
    
    for y in test_yields:
        ql_price = ql_yield_to_price(ql_bond, y, day_count, ql_settlement)
        fp_price = fp_yield_to_price(fp_bond, fp_settlement, y)
        passed = compare_values(f"YTM {y*100:.1f}% -> Price", ql_price, fp_price, tolerance=0.02)
        all_passed = all_passed and passed
    
    # =========================================================================
    # 2. 가격 → 수익률 비교
    # =========================================================================
    print("\n" + "=" * 80)
    print("2. 가격 -> 수익률 비교")
    print("=" * 80)
    print(f"\n{'가격':25} {'QuantLib':>12} {'FinancePy':>12} {'차이':>10} {'차이%':>8}  결과")
    print("-" * 80)
    
    test_prices = [95.0, 98.0, 100.0, 102.0, 105.0]
    
    for p in test_prices:
        ql_ytm = ql_price_to_yield(ql_bond, p, day_count, ql_settlement)
        fp_ytm = fp_price_to_yield(fp_bond, fp_settlement, p)
        passed = compare_values(f"Price {p:.0f} -> YTM", ql_ytm, fp_ytm, tolerance=0.0005)
        all_passed = all_passed and passed
    
    # =========================================================================
    # 3. 듀레이션 비교
    # =========================================================================
    print("\n" + "=" * 80)
    print("3. 듀레이션 및 볼록성 비교 (YTM 5%)")
    print("=" * 80)
    print(f"\n{'지표':25} {'QuantLib':>12} {'FinancePy':>12} {'차이':>10} {'차이%':>8}  결과")
    print("-" * 80)
    
    yield_rate = 0.05
    
    ql_mac, ql_mod, ql_conv = ql_durations(ql_bond, yield_rate, day_count, ql_settlement)
    fp_mac, fp_mod, fp_conv = fp_durations(fp_bond, fp_settlement, yield_rate)
    
    passed1 = compare_values("Macaulay Duration", ql_mac, fp_mac, tolerance=0.02)
    passed2 = compare_values("Modified Duration", ql_mod, fp_mod, tolerance=0.02)
    
    # Convexity: FinancePy는 다른 스케일 사용 (100으로 곱해서 비교)
    fp_conv_scaled = fp_conv * 100
    passed3 = compare_values("Convexity", ql_conv, fp_conv_scaled, tolerance=0.5)
    
    all_passed = all_passed and passed1 and passed2 and passed3
    
    # =========================================================================
    # 최종 결과
    # =========================================================================
    print("\n" + "=" * 80)
    print("최종 결과")
    print("=" * 80)
    
    if all_passed:
        print("\n[PASS] 모든 테스트 통과! QuantLib과 FinancePy의 계산 결과가 일치합니다.")
    else:
        print("\n[FAIL] 일부 테스트 실패. 차이가 있는 항목을 확인하세요.")
        print("\n참고: 일수계산(Day Count) 방식이나 결제일 차이로 인해")
        print("      약간의 차이가 발생할 수 있습니다.")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()

