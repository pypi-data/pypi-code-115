import re


def bold(part):
    return f"**{part}**"


def split_word(word):
    syllables = re.split("([aeiou])", word)
    syllables = [i for i in syllables if i]

    if len(syllables) == 1:
        return bold(word)

    prefix, remain_word_list = split_bold_by_length(syllables)
    bolded_word = bold(prefix) + "".join(remain_word_list)
    return bolded_word


def split_bold_by_length(syllables):
    if len(syllables) == 2:
        prefix = syllables[0]
        remain_word_list = syllables[1:]
    else:
        prefix = "".join(syllables[0:2])
        remain_word_list = syllables[2:]

    return prefix, remain_word_list


def run(sys_argv=None):
    words_list = sys_argv.split(" ")

    bolded_list = []
    for word in words_list:
        bolded_word = split_word(word)
        bolded_list.append(bolded_word)

    result = " ".join(bolded_list)
    return result
