

def list_generator(l):
    for elem in l:
        yield elem


def dict_generator(d):
    for elem in d:
        yield elem, d[elem]
