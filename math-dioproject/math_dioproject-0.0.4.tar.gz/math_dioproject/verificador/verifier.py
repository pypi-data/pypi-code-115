def primo(num1):
    if num1 <= 1:
        return False
    else:
        for i in range(2, num1):
            if num1 % i == 0:
                return print(f'{num1} nao é primo')
    return print(f'{num1} é primo')

def quadrado(num1, num2, num3, num4):
    if num1 == num2 == num3 == num4:
        print('As medidas resultam em um quadrado')
    else:
        print('As medidas nao resultam em um quadrado')

def retangulo(num1, num2, num3, num4):
    if num1 == num2 and num3 == num4 and num1 != num3:
        print('As medidas resultam em um retangulo')
    else:
        print('As medidas nao resultam em um retangulo')