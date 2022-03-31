import calendar

edge = int(input('Введите значения ребра куба'))
V = edge ** 3
S = edge ** 2
P = edge * 4
print(f'Плошадь грани куба равна {S},объем куба равен {V},'
      f'периметр грани куба равен {P}')

"""Первый  способ"""
year = int(input('Введите текущий год:'))

if (year % 4 == 0) and (year % 100 != 0) or (year % 400 == 0):
    print(f'{year} год - високосный')
else:
    print(f'{year} год - не високосный')

"""Второй способ"""

year_2 = int(input('Введите текущий год:'))
check_2 = calendar.isleap(year_2)
if check_2 is True:
    print(f'{year_2} год - високосный')
else:
    print(f'{year_2} год - не високосный')
