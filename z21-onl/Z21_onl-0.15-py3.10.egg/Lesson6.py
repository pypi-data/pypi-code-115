import json
import csv
import openpyxl


def create_dict():
    lst_users = []
    for j in range(3):
        name = str(input('Введите ваше имя: '))
        age = str(input('Введите ваш возраст: '))
        users = {'name': name, 'age': age}
        lst_users.append(users)
    return lst_users


data = create_dict()

FILENAME_1 = 'users.json'

# Сериализации в json
with open(FILENAME_1, 'w') as file:
    json.dump(data, file)

with open(FILENAME_1, 'r') as file:
    reader = json.load(file)
    print(reader)

# Сериализации в CSV
FILENAME_2 = 'users.csv'
with open(FILENAME_2, 'w') as file:
    columns = ['name', 'age']
    writer = csv.DictWriter(file, fieldnames=columns)
    writer.writeheader()
    writer.writerows(data)

with open(FILENAME_2, 'r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        print(row["name"], "-", row["age"])

# Отправка в exel
FILENAME_3 = 'users.xlsx'
wb = openpyxl.load_workbook(FILENAME_3)
sheet = wb.create_sheet('Users')
row = 1
sheet['A'+str(row)] = 'Name'
sheet['B'+str(row)] = 'Age'
for i in data:
    row += 1
    for key, value in i.items():
        if key == 'name':
            sheet['A'+str(row)] = value
        if key == 'age':
            sheet['B' + str(row)] = value

wb.save(FILENAME_3)


def write_data():
    with open('text.txt', 'w', encoding="utf-8") as f:
        content = str(input('Input text'))
        f.write(content)


def read_data():
    with open('text.txt', 'r') as f:
        content = f.read()
        print(content)


def encod_ascii():
    with open('text.txt', encoding='ascii', errors='ignore') as f:
        text = f.read()
        print(text)


def encod_utf_16():
    with open('text.txt', encoding='utf-16-le') as f:
        text = f.read()
        print(text)


for i in range(5):
    choice = int(input('Enter 1, if you want write data:\n'
                       'Enter 2, if you want read data:\n'
                       'Enter 3, if you want change encoding of file(ASCII):\n'
                       'Enter 4, if you want change encoding of file(Utf-16):\n'))
    if choice == 1:
        write_data()
    elif choice == 2:
        read_data()
    elif choice == 3:
        encod_ascii()
    elif choice == 4:
        encod_utf_16()
    else:
        print('Please, enter correct data')
        continue
