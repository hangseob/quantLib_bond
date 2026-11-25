# IRSwap 내부 구조 분석

## 1. IRSwap 클래스 구조

IRSwap은 **dataclass**로 구현되어 있습니다:

```python
@handle_camel_case_args
@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass(unsafe_hash=True, repr=False)
class IRSwap(Instrument):
    ...
```

### 주요 특징:
- **@dataclass**: Python의 dataclass 데코레이터로 자동으로 `__init__`, `__repr__` 등 생성
- **@dataclass_json**: JSON 직렬화/역직렬화 자동 지원
- **@handle_camel_case_args**: camelCase ↔ snake_case 자동 변환

## 2. 객체 생성 시 일어나는 일

```python
bond = IRSwap(
    pay_or_receive=PayReceive.Receive,
    termination_date='2029-11-10',
    effective_date='2025-12-30',
    notional_currency=Currency.KRW,
    fixed_rate=0.04,
    name='Korea Bond Synthetic'
)
```

### 단계별 처리:

1. **@handle_camel_case_args 데코레이터 실행**
   - 입력 파라미터의 snake_case → camelCase 변환
   - 예: `pay_or_receive` → `payOrReceive` (내부적으로)

2. **dataclass의 자동 생성된 __init__ 실행**
   - 각 field를 Optional로 정의된 속성에 할당
   - field_metadata를 통한 메타데이터 처리
   - 기본값 설정 (asset_class, type_ 등)

3. **필드 초기화**
   ```python
   pay_or_receive: Optional[PayReceive] = field(default=None, metadata=field_metadata)
   termination_date: Optional[Union[datetime.date, str]] = field(default=None, metadata=field_metadata)
   notional_currency: Optional[Currency] = field(default=None, metadata=field_metadata)
   fixed_rate: Optional[Union[float, str]] = field(default=None, metadata=field_metadata)
   ...
   asset_class: Optional[AssetClass] = field(init=False, default=AssetClass.Rates, metadata=field_metadata)
   type_: Optional[AssetType] = field(init=False, default=AssetType.Swap, metadata=config(field_name='type', exclude=exclude_none))
   ```

4. **자동 설정되는 필드**
   - `asset_class`: `AssetClass.Rates` (금리 자산)
   - `type_`: `AssetType.Swap` (스왑 타입)

## 3. 실제 가격 계산은 언제?

**중요**: IRSwap 객체 생성 시에는 **계산이 일어나지 않습니다**!

실제 가격 계산은:
```python
from gs_quant.markets import PricingContext
from gs_quant.risk import DollarPrice

with PricingContext():
    price = bond.dollar_price()  # 이 시점에 계산 발생
```

### 가격 계산 흐름:
1. `PricingContext` 진입
2. Goldman Sachs 서버에 요청 전송
3. 서버에서 다음 계산 수행:
   - 쿠폰 스케줄 생성
   - 할인 곡선 적용
   - 현재가치 계산
   - Duration, DV01 등 리스크 지표 계산
4. 결과 반환

## 4. 로컬에서 계산 없이 사용하는 이유

GS Quant는 **"Instrument Definition"**과 **"Pricing"**을 분리합니다:

- **Instrument Definition (로컬)**: 상품 정의만 (IRSwap 객체 생성)
- **Pricing (서버)**: 실제 계산은 Goldman Sachs 서버에서

이것이 인증이 필요한 이유입니다!

## 5. 디버거로 확인하는 방법

### Step 1: 브레이크포인트 설정
`debug_irswap.py` 파일의 22번 줄에 브레이크포인트 설정

### Step 2: 디버거 시작
- F5 누르기
- 또는 "Run and Debug" → "Python: Current File"

### Step 3: Step Into (F11)
- 브레이크포인트에서 멈추면 F11 눌러 IRSwap.__init__ 내부로 진입
- dataclass가 자동 생성한 __init__ 코드 확인
- 각 필드 할당 과정 단계별 확인

### Step 4: 확인할 내용
1. `@handle_camel_case_args` 데코레이터의 파라미터 변환
2. dataclass field 할당
3. asset_class, type_ 등 자동 필드 설정
4. Optional 타입 처리

## 6. 소스 코드 위치

```
C:\Users\hangs\AppData\Roaming\Python\Python312\site-packages\gs_quant\target\instrument.py
```

이 파일을 직접 열어서 전체 IRSwap 클래스 정의를 볼 수 있습니다.

## 7. 주요 메서드

### scale_in_place()
```python
def scale_in_place(self, scaling: Optional[float] = None, check_resolved: bool = True):
    # notional_amount를 스케일링
    # 음수 scaling이면 pay/receive 반전
```

이 메서드는 포지션 크기를 조정할 때 사용됩니다.

## 결론

IRSwap 객체 생성은 **단순히 데이터 구조를 만드는 것**이며, 
실제 금융 계산은 **Goldman Sachs 서버에서 수행**됩니다.

로컬에서 계산하려면 QuantLib 같은 라이브러리를 사용해야 합니다!


