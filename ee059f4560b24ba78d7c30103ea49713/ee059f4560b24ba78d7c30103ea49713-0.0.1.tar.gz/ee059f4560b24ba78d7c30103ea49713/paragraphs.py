# paragraphs.py

from lorem import get_paragraph


# ----------------------------------------------------------------

def gen_paragraphs(number: int, width: int = 80) -> [str]:
    """
    Print out a number of paragraphs.

    :param number: number of paragraphs to generate
    :param width: maximum line width
    :return: list of paragraphs
    """
    if number <= 0:
        return _undefined_behaviour(number)

    para_list = []

    for x in range(number):
        para_lines = ''
        column = 0

        for word in get_paragraph().split(' '):
            if column == 0:
                # First word in paragraph
                para_lines += word
                column = len(word)
            elif column + 1 + len(word) <= width:
                # Word fits on current line
                para_lines += ' '
                para_lines += word
                column += (1 + len(word))
            else:
                # Word does not fit on current line
                para_lines += '\n'
                para_lines += word
                column = len(word)

        para_list.append(para_lines)

    return para_list


# ----------------------------------------------------------------

def _undefined_behaviour(number: int):
    if number == 0:
        return ['''If a program has not been specified, it cannot be incorrect; it can
only be surprising.
 -- Young, Boebert, and Kain''']

    else:
        return ['''Halt and catch fire.''']