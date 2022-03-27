
class Colors:
    GREEN = '\033[92m' 
    YELLOW = '\033[93m'
    RED = '\033[91m'


def colored_print(text, color):

    if color == 'green':
        print(Colors.GREEN + text + Colors.GREEN)
    elif color == 'yellow':
        print(Colors.YELLOW + text + Colors.YELLOW)
    elif color == 'red':
        print(Colors.RED + text + Colors.RED)