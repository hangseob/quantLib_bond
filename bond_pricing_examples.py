"""
QuantLib 채권 가격/수익률/듀레이션 계산 예시
============================================

1. 수익률 → 채권가격 계산
2. 채권가격 → 수익률 계산
3. 각종 듀레이션 계산
"""

import QuantLib as ql


def create_fixed_rate_bond():
    """
    예시용 고정금리채권 생성
    - 액면: 100
    - 쿠폰: 연 4.5% (반기 지급)
    - 만기: 5년
    """
    # 평가일 설정
    evaluation_date = ql.Date(26, 12, 2024)
    ql.Settings.instance().evaluationDate = evaluation_date
    
    # 채권 파라미터
    issue_date = ql.Date(1, 1, 2024)
    maturity_date = ql.Date(1, 1, 2029)
    face_value = 100.0
    coupon_rate = 0.045  # 4.5%
    
    # 달력 및 일수계산
    calendar = ql.SouthKorea()
    day_count = ql.ActualActual(ql.ActualActual.Bond)
    
    # 이자지급 스케줄 (반기)
    schedule = ql.Schedule(
        issue_date,
        maturity_date,
        ql.Period(ql.Semiannual),
        calendar,
        ql.Unadjusted,
        ql.Unadjusted,
        ql.DateGeneration.Backward,
        False
    )
    
    # 고정금리채권 생성
    bond = ql.FixedRateBond(
        2,  # settlement days
        face_value,
        schedule,
        [coupon_rate],
        day_count
    )
    
    return bond, day_count


# =============================================================================
# 1. 수익률 → 채권가격 계산
# =============================================================================

def yield_to_price(bond, yield_rate, day_count):
    """
    주어진 수익률로부터 채권 가격(Clean Price) 계산
    
    Parameters:
    -----------
    bond : ql.Bond - 채권 객체
    yield_rate : float - 수익률 (예: 0.05 = 5%)
    day_count : ql.DayCounter - 일수계산 방법
    
    Returns:
    --------
    float : Clean Price (정가)
    """
    # InterestRate 객체 생성
    interest_rate = ql.InterestRate(
        yield_rate,
        day_count,
        ql.Compounded,      # 복리
        ql.Semiannual       # 반기 복리
    )
    
    # 가격 계산
    clean_price = ql.BondFunctions.cleanPrice(bond, interest_rate)
    accrued = ql.BondFunctions.accruedAmount(bond)  # 경과이자
    dirty_price = clean_price + accrued  # 총가 = 정가 + 경과이자
    
    return clean_price, dirty_price


# =============================================================================
# 2. 채권가격 → 수익률 계산
# =============================================================================

def price_to_yield(bond, clean_price, day_count):
    """
    주어진 채권 가격으로부터 수익률(YTM) 계산
    
    Parameters:
    -----------
    bond : ql.Bond - 채권 객체
    clean_price : float - 정가 (Clean Price)
    day_count : ql.DayCounter - 일수계산 방법
    
    Returns:
    --------
    float : 만기수익률 (YTM)
    """
    # BondPrice 객체 생성 (최신 QuantLib API)
    bond_price = ql.BondPrice(clean_price, ql.BondPrice.Clean)
    
    # 수익률 계산
    ytm = bond.bondYield(
        bond_price,
        day_count,
        ql.Compounded,      # 복리
        ql.Semiannual       # 반기 복리
    )
    
    return ytm


# =============================================================================
# 3. 각종 듀레이션 계산
# =============================================================================

def calculate_durations(bond, yield_rate, day_count):
    """
    각종 듀레이션 및 위험지표 계산
    
    Parameters:
    -----------
    bond : ql.Bond - 채권 객체
    yield_rate : float - 수익률
    day_count : ql.DayCounter - 일수계산 방법
    
    Returns:
    --------
    dict : 듀레이션 및 위험지표들
    """
    # InterestRate 객체 생성
    interest_rate = ql.InterestRate(
        yield_rate,
        day_count,
        ql.Compounded,
        ql.Semiannual
    )
    
    # 1. 맥컬레이 듀레이션 (Macaulay Duration)
    # - 현금흐름의 가중평균 만기 (년)
    macaulay_duration = ql.BondFunctions.duration(
        bond,
        interest_rate,
        ql.Duration.Macaulay
    )
    
    # 2. 수정 듀레이션 (Modified Duration)
    # - 금리 1% 변동시 가격 변화율
    # - Modified Duration = Macaulay Duration / (1 + y/n)
    modified_duration = ql.BondFunctions.duration(
        bond,
        interest_rate,
        ql.Duration.Modified
    )
    
    # 3. 단순 듀레이션 (Simple Duration)
    simple_duration = ql.BondFunctions.duration(
        bond,
        interest_rate,
        ql.Duration.Simple
    )
    
    # 4. 볼록성 (Convexity)
    # - 금리 변동에 대한 가격 변화의 2차 효과
    convexity = ql.BondFunctions.convexity(
        bond,
        interest_rate
    )
    
    # 5. BPV (Basis Point Value) / DV01
    # - 금리 1bp 변동시 가격 변화
    clean_price = ql.BondFunctions.cleanPrice(bond, interest_rate)
    bpv = modified_duration * clean_price * 0.0001
    
    return {
        'macaulay_duration': macaulay_duration,
        'modified_duration': modified_duration,
        'simple_duration': simple_duration,
        'convexity': convexity,
        'bpv': bpv,
        'clean_price': clean_price
    }


# =============================================================================
# 메인 실행
# =============================================================================

def main():
    # 채권 생성
    bond, day_count = create_fixed_rate_bond()
    
    print("=" * 60)
    print("채권 정보")
    print("=" * 60)
    print(f"발행일: {bond.issueDate()}")
    print(f"만기일: {bond.maturityDate()}")
    print(f"쿠폰: 4.5% (반기 지급)")
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
        clean, dirty = yield_to_price(bond, y, day_count)
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
        ytm = price_to_yield(bond, price, day_count)
        print(f"{price:>12.2f} {ytm*100:>14.4f}%")
    
    # =========================================================================
    # 3. 듀레이션 계산
    # =========================================================================
    print("\n" + "=" * 60)
    print("3. 듀레이션 및 위험지표 계산")
    print("=" * 60)
    
    yield_rate = 0.05  # 5%
    results = calculate_durations(bond, yield_rate, day_count)
    
    print(f"\n기준 수익률: {yield_rate * 100:.2f}%")
    print(f"기준 가격: {results['clean_price']:.4f}")
    print()
    print(f"맥컬레이 듀레이션 (Macaulay):  {results['macaulay_duration']:.4f} 년")
    print(f"수정 듀레이션 (Modified):      {results['modified_duration']:.4f}")
    print(f"단순 듀레이션 (Simple):        {results['simple_duration']:.4f}")
    print(f"볼록성 (Convexity):            {results['convexity']:.4f}")
    print(f"BPV (1bp 가격변동):            {results['bpv']:.4f}")
    
    # =========================================================================
    # 4. 듀레이션을 이용한 가격 변화 예측
    # =========================================================================
    print("\n" + "=" * 60)
    print("4. 금리 변동시 가격 변화 예측")
    print("=" * 60)
    
    price = results['clean_price']
    mod_dur = results['modified_duration']
    conv = results['convexity']
    
    rate_changes = [-0.01, -0.005, 0.005, 0.01]  # -100bp, -50bp, +50bp, +100bp
    
    print(f"\n{'금리변동':>10} {'듀레이션효과':>14} {'볼록성효과':>12} {'예상가격':>12} {'실제가격':>12}")
    print("-" * 62)
    
    for dr in rate_changes:
        # 듀레이션 효과: -Modified Duration × Price × Δr
        duration_effect = -mod_dur * price * dr
        
        # 볼록성 효과: 0.5 × Convexity × Price × (Δr)²
        convexity_effect = 0.5 * conv * price * (dr ** 2)
        
        # 예상 가격
        predicted_price = price + duration_effect + convexity_effect
        
        # 실제 가격 (새로운 수익률로 계산)
        new_yield = yield_rate + dr
        actual_price, _ = yield_to_price(bond, new_yield, day_count)
        
        print(f"{dr*10000:>+8.0f}bp {duration_effect:>+14.4f} {convexity_effect:>+12.4f} "
              f"{predicted_price:>12.4f} {actual_price:>12.4f}")
    
    print("\n" + "=" * 60)
    print("완료")
    print("=" * 60)


if __name__ == "__main__":
    main()

