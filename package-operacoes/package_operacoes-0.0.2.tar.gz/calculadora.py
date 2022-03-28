from package_operacoes import funcoes


print('Olá seja bem vindo')
print('Escolha uma opção')
print('1 - Soma')
print('2 - Subtração')

opcao = int(input("Digite sua opção: "))

if opcao == 1:
    print('Você Escolheu a opção de Soma')
    x = int(input('número 1: '))
    y = int(input('número 2: '))
    print('O resultado da soma foi:', funcoes.soma(x,y))
else: 
    print('Você Escolheu a opção de Subtação')
    x = int(input('número 1: '))
    y = int(input('número 2: '))
    print('O resultado da subtração foi:', funcoes.subtracao(x,y))
