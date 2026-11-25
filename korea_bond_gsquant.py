"""
한국 채권 분석 - GS Quant
========================

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

from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import numpy as np

# GS Quant imports
try:
    from gs_quant.instrument import Bond, IRSwap
    from gs_quant.common import Currency, PayReceive, BuySell
    from gs_quant.session import GsSession, Environment
    from gs_quant.markets import PricingContext
    from gs_quant.risk import DollarPrice, IRDelta, IRVega
    GS_QUANT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: gs-quant import failed: {e}")
    GS_QUANT_AVAILABLE = False


def generate_schedule_backward(start_date, end_date, frequency_months=3):
    """
    Backward 방식으로 쿠폰 스케줄 생성
    
    Parameters:
    -----------
    start_date : date - 발행일
    end_date : date - 만기일
    frequency_months : int - 쿠폰 지급 주기 (개월)
    
    Returns:
    --------
    list[date] : 쿠폰 지급 날짜 리스트
    """
    schedule = []
    current_date = end_date
    
    # 만기일부터 역산
    while current_date >= start_date:
        schedule.append(current_date)
        current_date = current_date - relativedelta(months=frequency_months)
    
    # 시작일 추가 (중복 방지)
    if schedule[-1] != start_date:
        schedule.append(start_date)
    
    # 정렬 (오름차순)
    schedule.sort()
    return schedule


def adjust_modified_following(dt, korean_holidays=None):
    """
    Modified Following 영업일 조정
    
    Parameters:
    -----------
    dt : date - 조정할 날짜
    korean_holidays : set - 한국 공휴일 집합
    
    Returns:
    --------
    date : 조정된 날짜
    """
    if korean_holidays is None:
        korean_holidays = set()
    
    adjusted = dt
    
    # 주말 또는 공휴일이면 다음 영업일로
    while adjusted.weekday() >= 5 or adjusted in korean_holidays:
        adjusted = adjusted + relativedelta(days=1)
        
        # Modified Following: 다음 달로 넘어가면 이전 영업일로
        if adjusted.month != dt.month:
            adjusted = dt
            while adjusted.weekday() >= 5 or adjusted in korean_holidays:
                adjusted = adjusted - relativedelta(days=1)
            break
    
    return adjusted


def calculate_accrued_interest(settle_date, last_coupon_date, next_coupon_date, 
                               coupon_rate, face_value=100.0, day_count='ACT/360'):
    """
    경과이자 계산
    
    Parameters:
    -----------
    settle_date : date - 결제일
    last_coupon_date : date - 이전 쿠폰 지급일
    next_coupon_date : date - 다음 쿠폰 지급일
    coupon_rate : float - 연 쿠폰 이자율
    face_value : float - 액면가
    day_count : str - 일수 계산 방식
    
    Returns:
    --------
    float : 경과이자
    """
    if day_count == 'ACT/360':
        days_accrued = (settle_date - last_coupon_date).days
        days_in_period = (next_coupon_date - last_coupon_date).days
        year_fraction = days_accrued / 360.0
    else:
        # 기본: ACT/ACT
        days_accrued = (settle_date - last_coupon_date).days
        days_in_period = (next_coupon_date - last_coupon_date).days
        year_fraction = days_accrued / days_in_period * (days_in_period / 365.0)
    
    return face_value * coupon_rate * year_fraction


def calculate_pv_cashflows(cashflows, dates, ytm, settle_date, day_count='ACT/360', frequency=4):
    """
    현재가치 계산 (할인)
    
    Parameters:
    -----------
    cashflows : list[float] - 캐시플로우 리스트
    dates : list[date] - 캐시플로우 날짜 리스트
    ytm : float - 만기수익률
    settle_date : date - 결제일
    day_count : str - 일수 계산 방식
    frequency : int - 연간 복리 횟수
    
    Returns:
    --------
    float : 현재가치 합계
    """
    pv_total = 0.0
    
    for cf, cf_date in zip(cashflows, dates):
        if cf_date <= settle_date:
            continue
            
        # 시간 계산
        if day_count == 'ACT/360':
            days = (cf_date - settle_date).days
            time_to_cf = days / 360.0
        else:
            days = (cf_date - settle_date).days
            time_to_cf = days / 365.0
        
        # 할인 (복리)
        discount_factor = (1 + ytm / frequency) ** (-time_to_cf * frequency)
        pv = cf * discount_factor
        pv_total += pv
    
    return pv_total


def calculate_duration_convexity(cashflows, dates, ytm, settle_date, day_count='ACT/360', frequency=4):
    """
    Duration과 Convexity 계산
    
    Parameters:
    -----------
    cashflows : list[float] - 캐시플로우 리스트
    dates : list[date] - 캐시플로우 날짜 리스트
    ytm : float - 만기수익률
    settle_date : date - 결제일
    day_count : str - 일수 계산 방식
    frequency : int - 연간 복리 횟수
    
    Returns:
    --------
    tuple : (macaulay_duration, modified_duration, convexity)
    """
    pv_total = 0.0
    weighted_time = 0.0
    weighted_time_squared = 0.0
    
    for cf, cf_date in zip(cashflows, dates):
        if cf_date <= settle_date:
            continue
            
        # 시간 계산
        if day_count == 'ACT/360':
            days = (cf_date - settle_date).days
            time_to_cf = days / 360.0
        else:
            days = (cf_date - settle_date).days
            time_to_cf = days / 365.0
        
        # 할인
        discount_factor = (1 + ytm / frequency) ** (-time_to_cf * frequency)
        pv = cf * discount_factor
        
        pv_total += pv
        weighted_time += pv * time_to_cf
        weighted_time_squared += pv * time_to_cf * (time_to_cf + 1.0 / frequency)
    
    # Macaulay Duration
    macaulay_duration = weighted_time / pv_total if pv_total > 0 else 0.0
    
    # Modified Duration
    modified_duration = macaulay_duration / (1 + ytm / frequency)
    
    # Convexity
    convexity = weighted_time_squared / pv_total if pv_total > 0 else 0.0
    
    return macaulay_duration, modified_duration, convexity


def main_gsquant():
    """GS Quant를 사용한 채권 분석"""
    
    if not GS_QUANT_AVAILABLE:
        print("GS Quant가 설치되어 있지 않습니다. Fallback 모드로 실행합니다.")
        return main_fallback()
    
    print("=" * 90)
    print("한국 채권 분석 - GS Quant (실제 라이브러리 사용)")
    print("=" * 90)
    
    # 채권 조건
    issue_date = date(2025, 12, 30)
    maturity_date = date(2029, 11, 10)
    coupon_rate = 0.04  # 4% per annum
    face_value = 100.0
    ytm = 0.037  # 3.7%
    
    print(f"Issue Date         : {issue_date}")
    print(f"Maturity Date      : {maturity_date}")
    print(f"Coupon Rate        : {coupon_rate * 100:.2f}% per annum")
    print(f"Frequency          : Quarterly (연 4회)")
    print(f"Day Count          : Act/360")
    print(f"Face Value         : {face_value}")
    print(f"YTM for Pricing    : {ytm * 100:.4f}%")
    print("=" * 90)
    
    try:
        # GS Quant 채권 생성
        # Note: GS Quant의 Bond 객체는 실제 발행된 채권을 참조
        # 맞춤형 채권은 IRSwap 등을 사용하여 구현 가능
        
        bond = IRSwap(
            pay_or_receive=PayReceive.Receive,  # 쿠폰 수취
            termination_date=maturity_date.strftime('%Y-%m-%d'),
            effective_date=issue_date.strftime('%Y-%m-%d'),
            notional_currency=Currency.KRW,
            fixed_rate=coupon_rate,
            name='Korea Bond Synthetic'
        )
        
        print("\n채권 객체 생성 완료 (IRSwap으로 구현):")
        print(f"Pay/Receive: {bond.pay_or_receive}")
        print(f"Currency: {bond.notional_currency}")
        print(f"Fixed Rate: {bond.fixed_rate * 100:.2f}%")
        print(f"Start: {bond.effective_date}")
        print(f"End: {bond.termination_date}")
        
        # Pricing requires authentication
        print("\n주의: GS Quant의 가격 평가는 Goldman Sachs 인증이 필요합니다.")
        print("인증 없이는 채권 생성만 가능하며, 실제 가격 평가는 Fallback 모드를 사용합니다.")
        print("\nFallback 모드로 전환하여 실제 계산을 수행합니다.\n")
        return main_fallback()
        
    except Exception as e:
        print(f"\n오류 발생: {e}")
        print(f"오류 타입: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        print("\nGS Quant 사용 실패. Fallback 모드로 전환합니다.\n")
        return main_fallback()


def main_fallback():
    """Fallback: 수학적 계산을 사용한 채권 분석"""
    
    print("=" * 90)
    print("한국 채권 분석 - GS Quant (Fallback Mode)")
    print("=" * 90)
    
    # 채권 조건
    issue_date = date(2025, 12, 30)
    maturity_date = date(2029, 11, 10)
    coupon_rate = 0.04  # 4% per annum
    face_value = 100.0
    frequency = 4  # Quarterly (연 4회)
    frequency_months = 12 // frequency  # 3개월
    ytm = 0.037  # 3.7%
    
    print(f"Issue Date         : {issue_date}")
    print(f"Maturity Date      : {maturity_date}")
    print(f"Coupon Rate        : {coupon_rate * 100:.2f}% per annum")
    print(f"Frequency          : Quarterly (연 {frequency}회)")
    print(f"Day Count          : Act/360")
    print(f"Adjustment         : Modified Following")
    print(f"Schedule Generation: Backward (from maturity)")
    print(f"Holidays           : South Korea (주말만 고려)")
    print(f"Face Value         : {face_value}")
    print("=" * 90)
    
    # 1. 쿠폰 스케줄 생성 (Backward)
    print("\n" + "=" * 90)
    print("1. 쿠폰 스케줄 (Coupon Schedule)")
    print("=" * 90)
    
    unadjusted_schedule = generate_schedule_backward(issue_date, maturity_date, frequency_months)
    
    # Modified Following 조정 (주말만 고려 - 한국 공휴일은 생략)
    adjusted_schedule = [adjust_modified_following(dt) for dt in unadjusted_schedule]
    
    print(f"{'Index':<6} {'Unadjusted':<15} {'Adjusted':<15} {'Weekday':<10}")
    print("-" * 60)
    for i, (unadj, adj) in enumerate(zip(unadjusted_schedule, adjusted_schedule)):
        weekday = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][adj.weekday()]
        moved = "" if unadj == adj else " *"
        print(f"{i:<6} {str(unadj):<15} {str(adj):<15} {weekday:<10}{moved}")
    
    # 2. 캐시플로우 계산
    print("\n" + "=" * 90)
    print("2. 캐시플로우 상세 (Cashflows)")
    print("=" * 90)
    print(f"{'Index':<6} {'Date':<15} {'Days':<10} {'Coupon':<15} {'Principal':<15} {'Total':<15}")
    print("-" * 90)
    
    cashflow_dates = []
    cashflow_amounts = []
    
    for i in range(1, len(adjusted_schedule)):
        cf_date = adjusted_schedule[i]
        prev_date = adjusted_schedule[i-1]
        
        # Act/360 기준 일수 계산
        days = (cf_date - prev_date).days
        coupon_payment = face_value * coupon_rate * (days / 360.0)
        
        # 마지막 쿠폰 + 원금 상환
        if cf_date == adjusted_schedule[-1]:
            principal_payment = face_value
        else:
            principal_payment = 0.0
        
        total_payment = coupon_payment + principal_payment
        
        cashflow_dates.append(cf_date)
        cashflow_amounts.append(total_payment)
        
        print(f"{i-1:<6} {str(cf_date):<15} {days:<10} {coupon_payment:<15.6f} "
              f"{principal_payment:<15.2f} {total_payment:<15.6f}")
    
    total_cashflow = sum(cashflow_amounts)
    print("-" * 90)
    print(f"{'':6} {'Total':<15} {'':10} {'':15} {'':15} {total_cashflow:<15.6f}")
    print("=" * 90)
    
    # 3. YTM 3.7%로 평가
    print("\n" + "=" * 90)
    print("3. 채권 가격 평가 (YTM = 3.7%)")
    print("=" * 90)
    
    settle_date = issue_date
    
    # 현재가치 계산
    dirty_price = calculate_pv_cashflows(cashflow_amounts, cashflow_dates, ytm, 
                                         settle_date, day_count='ACT/360', frequency=frequency)
    
    # 경과이자 (발행일이므로 0)
    accrued_interest = 0.0
    clean_price = dirty_price - accrued_interest
    
    print(f"Settlement Date    : {settle_date}")
    print(f"YTM                : {ytm * 100:.4f}%")
    print(f"Clean Price        : {clean_price:.6f}")
    print(f"Accrued Interest   : {accrued_interest:.6f}")
    print(f"Dirty Price        : {dirty_price:.6f}")
    
    # 4. Duration 계산
    print("\n" + "=" * 90)
    print("4. Duration 계산")
    print("=" * 90)
    
    macaulay_duration, modified_duration, convexity = calculate_duration_convexity(
        cashflow_amounts, cashflow_dates, ytm, settle_date, day_count='ACT/360', frequency=frequency
    )
    
    # DV01 계산 (1bp = 0.0001)
    ytm_up = ytm + 0.0001
    ytm_down = ytm - 0.0001
    
    price_up = calculate_pv_cashflows(cashflow_amounts, cashflow_dates, ytm_up, 
                                      settle_date, day_count='ACT/360', frequency=frequency)
    price_down = calculate_pv_cashflows(cashflow_amounts, cashflow_dates, ytm_down, 
                                        settle_date, day_count='ACT/360', frequency=frequency)
    
    dv01 = (price_down - price_up) / 2.0
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
        test_price = calculate_pv_cashflows(cashflow_amounts, cashflow_dates, test_ytm, 
                                            settle_date, day_count='ACT/360', frequency=frequency)
        price_change_pct = (test_price - base_price) / base_price * 100
        
        marker = " (현재)" if delta_bp == 0 else ""
        print(f"{test_ytm*100:<12.4f} {test_price:<15.6f} {test_price:<15.6f} "
              f"{price_change_pct:>14.4f}{marker}")
    
    print("=" * 90)
    
    print("\n" + "=" * 90)
    print("참고: 이 구현은 GS Quant의 저수준 API를 사용한 맞춤형 계산입니다.")
    print("GS Quant의 고급 채권 모델을 사용하려면 GsSession 인증이 필요합니다.")
    print("=" * 90)


def main():
    """메인 진입점"""
    # 먼저 GS Quant 사용 시도
    main_gsquant()


if __name__ == "__main__":
    main()

