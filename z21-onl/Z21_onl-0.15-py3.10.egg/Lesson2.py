"""Ex.1"""
first_day_of_year = 'Monday'
first_day_of_month = 'Monday'
first_day_of_week = 'Monday'
print(id(first_day_of_year), id(first_day_of_month), id(first_day_of_week))
if first_day_of_year == first_day_of_month and first_day_of_year == first_day_of_week:
    print('Задание 1: Значения переменных равны (true)')
else:
    print('Задание 1: Значения переменных не равны (false)')
if first_day_of_year is first_day_of_month and first_day_of_year is first_day_of_week:
    print('Задание 1: ID переменных равны (true)')
else:
    print('Задание 1: ID переменных не равны (false)')

"""Ex.2"""
ann_age = '12'
bob_age = str(12)
print(id(ann_age), id(bob_age))
if ann_age == bob_age:
    print('Задание 2: Значения переменных равны (true)')
else:
    print('Задание 2: Значения переменных не равны (false)')
if ann_age is bob_age:
    print('Задание 2: ID переменных равны (true)')
else:
    print('Задание 2: ID переменных не равны (false)')

"""2 способ"""
ob1 = 'I like sleep'
ob2 = 'I like '
if ob1 == ob2 + 'sleep':
    print('Задание 2(2): Значения переменных равны (true)')
else:
    print('Задание 2(2):Значения переменных не равны (false)')
if ob1 is ob2 + 'sleep':
    print('Задание 2(2):ID переменных равны (true)')
else:
    print('Задание 2(2):ID переменных не равны (false)')


"""Ex.3.part1"""
a = 'Mon'
b = 'day'
first_day_of_year = 'Monday'
first_day_of_month = 'Mon' + b
first_day_of_week = a + 'day'
print(id(first_day_of_year), id(first_day_of_month), id(first_day_of_week))
if first_day_of_year == first_day_of_month and first_day_of_year == first_day_of_week:
    print('Задание 3 (часть 1): Значения переменных равны (true)')
else:
    print('Задание 3 (часть 1): Значения переменных не равны (false)')
if first_day_of_year is first_day_of_month and first_day_of_year is first_day_of_week:
    print('Задание 3 (часть 1): ID переменных равны (true)')
else:
    print('Задание 3 (часть 1): ID переменных не равны (false)')

"""Ex.3.part2"""
ann_age = '12'
bob_age = str(12)
print(id(int(ann_age)), id(int(bob_age)))
if int(ann_age) == int(bob_age):
    print('Задание 3 (часть 2): Значения переменных равны (true)')
else:
    print('Задание 3 (часть 2):Значения переменных не равны (false)')
if int(ann_age) is int(bob_age):
    print('Задание 3 (часть 2):ID переменных равны (true)')
else:
    print('Задание 3 (часть 2): ID переменных не равны (false)')
