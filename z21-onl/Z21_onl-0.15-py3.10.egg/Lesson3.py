import random

while 1:
    name = str(input('Enter your name: '))
    age = int(input('Enter your age: '))
    sex = str(input('Enter:\n'
                    '\'M\', if you are a man \n'
                    '\'W\', if you are a woman ')
              )
    if age >= 18:
        if sex == 'M' or sex == 'm':
            print(f'Hello, Mr. {name}')
        elif sex == 'W' or sex == 'w':
            print(f'Hello, Ms. {name}')
        continue
    else:
        print(f'Hello, {name}')
        continue





"""Задание 3: игра на угадывание числа от 0 до 9"""
name_gamers = str(input('Hey! This is the Lucky Number game 1! What is your name?'))
print(f'Okey, {name_gamers},Your task is to guess the '
      f'hidden number!')
number_generated_1 = random.randrange(10)
print(number_generated_1)
number_entered = int(input('Please, enter a number from 0 to 9'))
attempt = 1
while number_entered != number_generated_1:
    print('You lose! try again!')
    number_entered = int(input('Please, enter a number from 0 to 9'))
    attempt += 1
    continue
else:
    print(f'Congratulations! You won $100!you guessed the number for {attempt} attempts')


'''Задание 3/2 
Каждый раунд компьютер генерирует случайные уникальные числа (количество чисел увеличивается на 1 с каждым раундом)
На первых 3 турах при названии красного числа, компьютер "намекает" игроку,
что нужно задать новое число, таким образом проиграть на первых 3 турах невозможно, с 4 тура игрок
 не имеет права на ошибку и при названии красного числа он теряет все деньги и выбывает из игры! После каждого тура 
 игрок имеет право забрать все деньги и окончить игру или продолжить играть!
 С каждым туром выигрыш увеличивается, игрок прошедший финал получает 30000$
 В конце игры игрок может начать ее занаво'''
name_gamers = str(input('Hey! This is the Lucky Number game 2! What is your name?'))
print(f'Okey, {name_gamers},we start the first round!\n Your task is to bypass '
      f'the hidden number! If you do it,'
      f'your winnings will be $10! Good luck!')


def game():
    amount_rand_digit = 1
    prize = 10
    while amount_rand_digit <= 9:
        result = random.sample(range(10), amount_rand_digit)
        number_entered = int(input('Please, enter a number from 0 to 9: '))
        while number_entered not in range(10):
            number_entered = int(input('Attention! enter a number from 0 to 9: '))
        if amount_rand_digit < 4:
            while number_entered in result:
                number_entered = int(input('Are you sure? Let\'s think some more!'
                                           'Please, enter a new number from 0 to 9: '))
                continue
        else:
            if number_entered in result:
                print('You lose all the money! Game over')
                break
        if number_entered not in result:
            print(f'Congratulations! You won ${prize}!')
            if amount_rand_digit <= 8:
                quest = str(
                    input('Choose 1 - if you want continue\n'
                          'choose 2 - if you want take the money')
                )
                if quest != '1':
                    print('Thank yot for game! Bye!')
                    break
                else:
                    amount_rand_digit += 1
                    prize *= 2
    attempt = input('Try again?\n1. Yes\n2.No')
    if attempt == '1':
        game()


game()