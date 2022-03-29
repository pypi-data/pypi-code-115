import itertools

case_list = ['username', 'password']
value_list = ['yes', 'no', 'err']


def gen_case(item=case_list, value=value_list):
    for i in itertools.product(item, value):
        print(' '.join(i))


def test_print():
    print("test print hello world")


if __name__ == '__main__':
    test_print()
