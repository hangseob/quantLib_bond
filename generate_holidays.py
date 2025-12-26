"""
QuantLib 한국 휴일을 CSV로 추출
"""
import QuantLib as ql
import csv

# 한국 달력
calendar = ql.SouthKorea()

# 2020-2040년 휴일 추출 (주말 제외)
holidays = []
start_date = ql.Date(1, 1, 2020)
end_date = ql.Date(31, 12, 2040)

current = start_date
while current <= end_date:
    if calendar.isHoliday(current):
        # 주말 제외 (토=7, 일=1)
        weekday = current.weekday()
        if weekday != 7 and weekday != 1:
            # YYYY-MM-DD 형식으로 저장
            date_str = f"{current.year()}-{current.month():02d}-{current.dayOfMonth():02d}"
            holidays.append(date_str)
    current = current + 1

# CSV 저장
with open('korea_holidays.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['date', 'description'])
    for h in holidays:
        writer.writerow([h, 'Korean Holiday'])

print(f"총 휴일 수: {len(holidays)}")
print(f"CSV 저장 완료: korea_holidays.csv")
print(f"처음 10개: {holidays[:10]}")
print(f"마지막 10개: {holidays[-10:]}")

