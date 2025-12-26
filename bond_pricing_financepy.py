"""
FinancePy 채권 가격/수익률/듀레이션 계산 예시
=============================================

1. 수익률 → 채권가격 계산
2. 채권가격 → 수익률 계산
3. 각종 듀레이션 계산
"""

from financepy.utils.date import Date
from financepy.utils.day_count import DayCountTypes
from financepy.utils.frequency import FrequencyTypes
from financepy.products.bonds.bond import Bond


def create_fixed_rate_bond():
    """
    예시용 고정금리채권 생성
    - 액면: 100
    - 쿠폰: 연 4.5% (반기 지급)
    - 만기: 5년
    """
    # 채권 파라미터
    issue_dt = Date(1, 1, 2024)
    maturity_dt = Date(1, 1, 2029)
    coupon_rate = 0.045  # 4.5%
    freq_type = FrequencyTypes.SEMI_ANNUAL
    day_count_type = DayCountTypes.ACT_ACT_ICMA
    
    # 채권 생성
    bond = Bond(
        issue_dt=issue_dt,
        maturity_dt=maturity_dt,
        coupon=coupon_rate,
        freq_type=freq_type,
        dc_type=day_count_type
    )
    
    # 결제일 (평가일 + 2영업일)
    settlement_date = Date(30, 12, 2024)
    
    return bond, settlement_date


# =============================================================================
# 1. 수익률 → 채권가격 계산
# =============================================================================

def yield_to_price(bond, settlement_date, yield_rate):
    """
    주어진 수익률로부터 채권 가격(Clean Price) 계산
    
    Parameters:
    -----------
    bond : Bond - 채권 객체
    settlement_date : Date - 결제일
    yield_rate : float - 수익률 (예: 0.05 = 5%)
    
    Returns:
    --------
    tuple : (clean_price, dirty_price)
    """
    # 정가 계산
    clean_price = bond.clean_price_from_ytm(settlement_date, yield_rate)
    
    # 총가 계산
    dirty_price = bond.dirty_price_from_ytm(settlement_date, yield_rate)
    
    return clean_price, dirty_price


# =============================================================================
# 2. 채권가격 → 수익률 계산
# =============================================================================

def price_to_yield(bond, settlement_date, clean_price):
    """
    주어진 채권 가격으로부터 수익률(YTM) 계산
    
    Parameters:
    -----------
    bond : Bond - 채권 객체
    settlement_date : Date - 결제일
    clean_price : float - 정가 (Clean Price)
    
    Returns:
    --------
    float : 만기수익률 (YTM)
    """
    ytm = bond.yield_to_maturity(settlement_date, clean_price)
    
    return ytm


# =============================================================================
# 3. 각종 듀레이션 계산
# =============================================================================

def calculate_durations(bond, settlement_date, yield_rate):
    """
    각종 듀레이션 및 위험지표 계산
    
    Parameters:
    -----------
    bond : Bond - 채권 객체
    settlement_date : Date - 결제일
    yield_rate : float - 수익률
    
    Returns:
    --------
    dict : 듀레이션 및 위험지표들
    """
    # 1. 맥컬레이 듀레이션 (Macaulay Duration)
    macaulay_duration = bond.macauley_duration(settlement_date, yield_rate)
    
    # 2. 수정 듀레이션 (Modified Duration)
    modified_duration = bond.modified_duration(settlement_date, yield_rate)
    
    # 3. 볼록성 (Convexity)
    convexity = bond.convexity_from_ytm(settlement_date, yield_rate)
    
    # 4. 가격 및 BPV
    clean_price = bond.clean_price_from_ytm(settlement_date, yield_rate)
    bpv = modified_duration * clean_price * 0.0001
    
    return {
        'macaulay_duration': macaulay_duration,
        'modified_duration': modified_duration,
        'convexity': convexity,
        'bpv': bpv,
        'clean_price': clean_price
    }


# =============================================================================
# 메인 실행
# =============================================================================

def main():
    # 채권 생성
    bond, settlement_date = create_fixed_rate_bond()
    
    print("=" * 60)
    print("채권 정보 (FinancePy)")
    print("=" * 60)
    print(f"발행일: {bond.issue_dt}")
    print(f"만기일: {bond.maturity_dt}")
    print(f"결제일: {settlement_date}")
    print(f"쿠폰: {bond.cpn * 100}% (반기 지급)")
    print(f"액면: 100")
    
    # =========================================================================
    # 1. 수익률 → 가격 계산
    # =========================================================================
    print("\n" + "=" * 60)
    print("1. 수익률 → 채권가격 계산")
    print("=" * 60)
    
    test_yields = [0.03, 0.04, 0.045, 0.05, 0.06]
    
    print(f"\n{'수익률':>10} {'정가(Clean)':>15} {'총가(Dirty)':>15}")
    print("-" * 42)
    
    for y in test_yields:
        clean, dirty = yield_to_price(bond, settlement_date, y)
        print(f"{y*100:>9.2f}% {clean:>15.4f} {dirty:>15.4f}")
    
    # =========================================================================
    # 2. 가격 → 수익률 계산
    # =========================================================================
    print("\n" + "=" * 60)
    print("2. 채권가격 → 수익률 계산")
    print("=" * 60)
    
    test_prices = [95.0, 98.0, 100.0, 102.0, 105.0]
    
    print(f"\n{'정가(Clean)':>12} {'수익률(YTM)':>15}")
    print("-" * 30)
    
    for price in test_prices:
        ytm = price_to_yield(bond, settlement_date, price)
        print(f"{price:>12.2f} {ytm*100:>14.4f}%")
    
    # =========================================================================
    # 3. 듀레이션 계산
    # =========================================================================
    print("\n" + "=" * 60)
    print("3. 듀레이션 및 위험지표 계산")
    print("=" * 60)
    
    yield_rate = 0.05  # 5%
    results = calculate_durations(bond, settlement_date, yield_rate)
    
    print(f"\n기준 수익률: {yield_rate * 100:.2f}%")
    print(f"기준 가격: {results['clean_price']:.4f}")
    print()
    print(f"맥컬레이 듀레이션 (Macaulay):  {results['macaulay_duration']:.4f} 년")
    print(f"수정 듀레이션 (Modified):      {results['modified_duration']:.4f}")
    print(f"볼록성 (Convexity):            {results['convexity']:.4f}")
    print(f"BPV (1bp 가격변동):            {results['bpv']:.4f}")
    
    print("\n" + "=" * 60)
    print("완료")
    print("=" * 60)


if __name__ == "__main__":
    main()

