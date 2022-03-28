import glob
import urllib.parse

from src.lib import find_todos, read_vault
from src.telegram import send_message


def print_tags(tags):
    res = []
    for tag in tags:
        if (len(tag) == 2):
            res.append(f"#{tag[0]} {tag[1]}")
        else:
            res.append(f"#{tag[0]}")
    return " ".join(res)

def main():
    todos = read_vault()
    res = ""
    for todo in todos:
        res += f"- □  {todo.body} "
        # res += f"obsidian://open?vault=notes&file={urllib.parse.quote(todo.file)} "
        if (len(todo.tags) > 0):
            res += f"*{print_tags(todo.tags)}*"
        res += "\n"
    send_message(res)

if __name__ == '__main__':
    main()
