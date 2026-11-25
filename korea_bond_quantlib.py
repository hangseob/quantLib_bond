"""
한국 채권 분석 - QuantLib
=========================

조건:
- Issue date: 2025-12-30
- Maturity date: 2029-11-10
- Schedule generation: from the end (backward)
- Frequency: Quarterly (연 4회)
- Adjusted: Yes
- Day Count: Act/360
- Business Day Adjustment: Modified Following
- Holidays: South Korea
- Coupon: 4% per annum
- YTM 평가: 3.7%
- Duration 계산
"""

import QuantLib as ql


def print_schedule(schedule):
    """스케줄 출력"""
    print(f"{'Index':<6} {'Date':<15} {'Weekday':<10}")
    print("-" * 40)
    for i, date in enumerate(schedule):
        weekday = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][date.weekday()]
        print(f"{i:<6} {date.ISO():<15} {weekday:<10}")


def main():
    # 평가일 설정 (발행일로 설정)
    evaluation_date = ql.Date(30, 12, 2025)
    ql.Settings.instance().evaluationDate = evaluation_date
    
    # 채권 조건
    issue_date = ql.Date(30, 12, 2025)
    maturity_date = ql.Date(10, 11, 2029)
    face_value = 100.0
    coupon_rate = 0.04  # 4% per annum
    
    # 달력 및 일수계산
    # SouthKorea 캘린더는 기본적으로 주말을 휴일로 처리하지만,
    # 명시적으로 Settlement 마켓을 지정해야 주말이 제대로 처리됩니다
    calendar = ql.SouthKorea(ql.SouthKorea.Settlement)
    day_count = ql.Actual360()
    business_convention = ql.ModifiedFollowing
    
    # 쿠폰 지급 스케줄 생성 (분기별 = Quarterly)
    schedule = ql.Schedule(
        issue_date,
        maturity_date,
        ql.Period(ql.Quarterly),  # 3개월마다
        calendar,
        business_convention,  # Modified Following
        business_convention,
        ql.DateGeneration.Backward,  # 만기일부터 역산
        False  # End of month rule
    )
    
    # 고정금리채권 생성
    bond = ql.FixedRateBond(
        0,  # settlement days (발행일 기준 평가이므로 0)
        face_value,
        schedule,
        [coupon_rate],
        day_count
    )
    
    print("=" * 90)
    print("한국 채권 분석 - QuantLib")
    print("=" * 90)
    print(f"Issue Date         : {issue_date.ISO()}")
    print(f"Maturity Date      : {maturity_date.ISO()}")
    print(f"Coupon Rate        : {coupon_rate * 100:.2f}% per annum")
    print(f"Frequency          : Quarterly (연 4회)")
    print(f"Day Count          : Act/360")
    print(f"Adjustment         : Modified Following")
    print(f"Schedule Generation: Backward (from maturity)")
    print(f"Calendar           : South Korea")
    print(f"Face Value         : {face_value}")
    print("=" * 90)
    
    # 1. 쿠폰 스케줄 출력
    print("\n" + "=" * 90)
    print("1. 쿠폰 스케줄 (Coupon Schedule)")
    print("=" * 90)
    print_schedule(schedule)
    
    # 2. 캐시플로우 상세 출력
    print("\n" + "=" * 90)
    print("2. 캐시플로우 상세 (Cashflows)")
    print("=" * 90)
    print(f"{'Index':<6} {'Date':<15} {'Amount':<15} {'Type':<20}")
    print("-" * 90)
    
    cashflows = bond.cashflows()
    total_cashflow = 0.0
    for i, cf in enumerate(cashflows):
        date = cf.date()
        amount = cf.amount()
        cf_type = type(cf).__name__
        print(f"{i:<6} {date.ISO():<15} {amount:<15.6f} {cf_type:<20}")
        total_cashflow += amount
    
    print("-" * 90)
    print(f"{'':6} {'Total Cashflow':<15} {total_cashflow:<15.6f}")
    print("=" * 90)
    
    # 3. YTM 3.7%로 평가
    ytm = 0.037  # 3.7%
    settle_date = evaluation_date
    
    print("\n" + "=" * 90)
    print("3. 채권 가격 평가 (YTM = 3.7%)")
    print("=" * 90)
    
    # YTM에 해당하는 InterestRate 객체 생성
    # Quarterly compounding (분기 복리)
    interest_rate = ql.InterestRate(
        ytm,
        day_count,
        ql.Compounded,
        ql.Quarterly
    )
    
    # 가격 계산
    clean_price = ql.BondFunctions.cleanPrice(bond, interest_rate)
    accrued = ql.BondFunctions.accruedAmount(bond)
    dirty_price = clean_price + accrued
    
    print(f"Settlement Date    : {settle_date.ISO()}")
    print(f"YTM                : {ytm * 100:.4f}%")
    print(f"Clean Price        : {clean_price:.6f}")
    print(f"Accrued Interest   : {accrued:.6f}")
    print(f"Dirty Price        : {dirty_price:.6f}")
    
    # 4. Duration 계산
    print("\n" + "=" * 90)
    print("4. Duration 계산")
    print("=" * 90)
    
    # Yield curve 설정 (flat curve at YTM)
    flat_forward = ql.FlatForward(
        settle_date,
        ql.QuoteHandle(ql.SimpleQuote(ytm)),
        day_count,
        ql.Compounded,
        ql.Quarterly
    )
    
    bond_engine = ql.DiscountingBondEngine(
        ql.YieldTermStructureHandle(flat_forward)
    )
    bond.setPricingEngine(bond_engine)
    
    # Macaulay Duration (년 단위)
    # QuantLib의 duration은 Modified Duration을 반환하므로, 
    # Macaulay Duration = Modified Duration * (1 + y/f)
    # 여기서 y = YTM, f = frequency (분기 = 4)
    
    # BondFunctions를 사용한 duration 계산
    modified_duration = ql.BondFunctions.duration(
        bond,
        interest_rate,
        ql.Duration.Modified
    )
    
    macaulay_duration = ql.BondFunctions.duration(
        bond,
        interest_rate,
        ql.Duration.Macaulay
    )
    
    # Convexity
    convexity = ql.BondFunctions.convexity(bond, interest_rate)
    
    # DV01 (Dollar Value of 01 basis point)
    # 1bp = 0.0001
    ytm_up = ytm + 0.0001
    ytm_down = ytm - 0.0001
    
    ir_up = ql.InterestRate(ytm_up, day_count, ql.Compounded, ql.Quarterly)
    ir_down = ql.InterestRate(ytm_down, day_count, ql.Compounded, ql.Quarterly)
    
    clean_up = ql.BondFunctions.cleanPrice(bond, ir_up)
    clean_down = ql.BondFunctions.cleanPrice(bond, ir_down)
    price_up = clean_up + accrued
    price_down = clean_down + accrued
    
    dv01 = (price_down - price_up) / 2.0
    
    # BPV (Basis Point Value) - 100 기준
    bpv = dv01 * face_value / 100.0
    
    print(f"Macaulay Duration  : {macaulay_duration:.6f} years")
    print(f"Modified Duration  : {modified_duration:.6f} years")
    print(f"Convexity          : {convexity:.6f}")
    print(f"DV01 (per 100 face): {dv01:.6f}")
    print(f"BPV (Basis Point Value): {bpv:.6f}")
    print()
    print(f"금리 1bp 상승 시 가격 변화: -{dv01:.6f} ({-dv01/dirty_price*100:.4f}%)")
    print(f"금리 1bp 하락 시 가격 변화: +{dv01:.6f} ({dv01/dirty_price*100:.4f}%)")
    
    # 5. 다양한 YTM에서의 가격 민감도
    print("\n" + "=" * 90)
    print("5. 금리 변화에 따른 가격 민감도")
    print("=" * 90)
    print(f"{'YTM (%)':<12} {'Clean Price':<15} {'Dirty Price':<15} {'가격 변화 (%)':<15}")
    print("-" * 90)
    
    base_ytm = ytm
    base_price = dirty_price
    
    for delta_bp in [-100, -50, -10, 0, 10, 50, 100]:
        test_ytm = base_ytm + delta_bp / 10000.0
        test_ir = ql.InterestRate(test_ytm, day_count, ql.Compounded, ql.Quarterly)
        test_clean = ql.BondFunctions.cleanPrice(bond, test_ir)
        test_dirty = test_clean + accrued
        price_change_pct = (test_dirty - base_price) / base_price * 100
        
        marker = " (현재)" if delta_bp == 0 else ""
        print(f"{test_ytm*100:<12.4f} {test_clean:<15.6f} {test_dirty:<15.6f} "
              f"{price_change_pct:>14.4f}{marker}")
    
    print("=" * 90)
    
    # 6. 추가 정보
    print("\n" + "=" * 90)
    print("6. 추가 채권 정보")
    print("=" * 90)
    
    # NPV (Net Present Value)
    npv = bond.NPV()
    print(f"NPV (Net Present Value): {npv:.6f}")
    
    # 다음 쿠폰 지급일
    next_coupon_rate = bond.nextCouponRate(settle_date)
    print(f"Next Coupon Rate       : {next_coupon_rate * 100:.4f}%")
    
    # 이전 쿠폰 지급일
    prev_coupon_rate = bond.previousCouponRate(settle_date)
    print(f"Previous Coupon Rate   : {prev_coupon_rate * 100:.4f}%")
    
    print("=" * 90)


if __name__ == "__main__":
    main()

