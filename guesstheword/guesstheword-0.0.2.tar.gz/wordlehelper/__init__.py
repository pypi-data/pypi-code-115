import random
from wordlehelper.words import LIST

def check_for_not_included(not_included, word, characters_to_include):
    response = True
    if not_included != None:
        for letter in not_included:
            if letter in word:
                response = False

        if response:
            for letter in characters_to_include :
                if letter not in word:
                    response = False

    return response

def check_word(input_str, not_included = None, not_included_words=None, characters_to_include=None):
    random.shuffle(LIST)
    if input_str == "*****" and not_included == "" and not_included_words == "":
        for word in LIST:
            all_random = True
            for i in range(0, 5):
                if word.count(word[i]) != 1:
                    all_random = False

            if all_random and check_for_not_included(not_included, word, characters_to_include) and word not in not_included_words:
                return word
    else:

        for word in LIST:
            all_random = True
            for i in range(0, 5):
                if word[i] != input_str[i] and input_str[i] != "*":
                    all_random = False
            if all_random and check_for_not_included(not_included, word, characters_to_include):
                return word

def execute():
    do_continue = True
    not_included_words = []
    characters_to_include = ""
    not_to_include = ""
    while (do_continue):
        input_pattern = input("Type initial word, if all characters are unknown type ***** \nelse type character for known position and * for unknowns position\n>> ")
        if characters_to_include == "":
            characters_to_include = input("Characters to include with position unknown\n>> ")
        else:
            characters_to_include += input("Type other character than '{}' that has to be included with unknown position\n>> ".format(characters_to_include))

        if not_to_include == "":
            not_to_include = input("Type all characters which has to be excluded from search word\n>> ")
        else:
            not_to_include += input("Type other character than '{}' that has to be exluded\n>> ".format(not_to_include))

        word = check_word(input_pattern, not_to_include, not_included_words, characters_to_include)
        print ("\n\n Selected word is\n\n\t", word)
        do_continue_input = input("Do you want to continue search y/n >> ")
        if str(do_continue_input).lower() == "n":
            do_continue = False
            not_included_words.append(word)