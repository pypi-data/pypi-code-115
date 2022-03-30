import re
from os import path
from unittest import result


def get_lines_file(path):
    file = open(path, "r")
    lines = file.readlines()
    file.close()
    return lines


def get_words(line, word):
    if word in line:
        regex = r"\w+"
        list1 = re.findall(regex, line)
        c_line = clean_line(list1)
        return c_line


def clean_line(line):
    response = []
    for w in line:
        r = [re.sub(r"[^a-zA-Z]+", " ", w) for k in w.split("\n")]
        response += r
    return response


def format_output(list_line):
    st = ""
    for i in list_line:
        st_aux = "["
        for x in i:
            w = x.split(" ")
            for w1 in w:

                st_aux += " " + w1

        st_aux += " ]\n"
        st_aux = " ".join(st_aux.split(" "))
        st_aux.replace(",", "")
        st += st_aux

    return st


def get_match(file_path):
    result = []

    if path.exists(file_path):
        source_text = get_lines_file(file_path)
        search_term = (
            source_text[-1] if len(source_text) > 0 else print("File is empty")
        )
        print(f"Search term: {search_term}")
        for l in source_text[:-1]:
            m_words = get_words(l, search_term)

            if m_words:

                result.append(m_words)
        r = format_output(result)

        return r
    else:
        print("File path provided not found..")
