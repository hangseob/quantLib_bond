"""
IRSwap 내부 연산 확인을 위한 디버그 스크립트
"""

from datetime import date
from gs_quant.instrument import IRSwap
from gs_quant.common import Currency, PayReceive

# 채권 조건
issue_date = date(2025, 12, 30)
maturity_date = date(2029, 11, 10)
coupon_rate = 0.04  # 4% per annum

print("IRSwap 객체 생성 시작...")
print(f"Issue: {issue_date}")
print(f"Maturity: {maturity_date}")
print(f"Coupon Rate: {coupon_rate * 100}%")
print()

# 여기에 브레이크포인트를 설정하고 F11(Step Into)를 누르면
# IRSwap 클래스 내부로 들어갈 수 있습니다
bond = IRSwap(
    pay_or_receive=PayReceive.Receive,  # 쿠폰 수취
    termination_date=maturity_date.strftime('%Y-%m-%d'),
    effective_date=issue_date.strftime('%Y-%m-%d'),
    notional_currency=Currency.KRW,
    fixed_rate=coupon_rate,
    name='Korea Bond Synthetic'
)

print("IRSwap 객체 생성 완료!")
print(f"\n생성된 객체 정보:")
print(f"Type: {type(bond)}")
print(f"Pay/Receive: {bond.pay_or_receive}")
print(f"Currency: {bond.notional_currency}")
print(f"Fixed Rate: {bond.fixed_rate}")
print(f"Effective Date: {bond.effective_date}")
print(f"Termination Date: {bond.termination_date}")

# 객체의 모든 속성 확인
print(f"\n모든 속성:")
for attr in dir(bond):
    if not attr.startswith('_'):
        try:
            value = getattr(bond, attr)
            if not callable(value):
                print(f"  {attr}: {value}")
        except:
            pass

print("\n디버거 사용 방법:")
print("1. 이 파일(debug_irswap.py)을 엽니다")
print("2. 22번 줄 'bond = IRSwap(' 왼쪽 여백을 클릭하여 브레이크포인트 설정")
print("3. F5를 눌러 디버거 시작")
print("4. 브레이크포인트에서 멈추면 F11(Step Into)를 눌러 IRSwap 내부로 진입")
print("5. justMyCode=false 설정이 되어있으므로 gs-quant 라이브러리 내부로 들어갈 수 있습니다")


