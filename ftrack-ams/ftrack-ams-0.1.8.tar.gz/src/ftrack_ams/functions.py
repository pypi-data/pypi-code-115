import os

from pick import pick

import ftrack_api

server = "https://ams.ftrackapp.com/api?"


def create_project_name(num, client, name):
    return f"{num}_{client.upper()}_{name.upper()}"


def clearConsole():
    return os.system("cls" if os.name in ("nt", "dos") else "clear")


def get_ftrack_session():
    return ftrack_api.Session(
        server_url=server,
        api_key=os.getenv("FTRACK_API_KEY"),
        api_user=os.getenv("FTRACK_API_USER"),
    )


def select_artist(team, users, question):
    ia, index = pick([u["username"] for u in team], question, indicator="👉")
    return [i for i in users if ia.lower() in i["username"].lower()][0]


def number_to_letter(input: int) -> str:
    return str(chr(ord('@') + input + 1))


def shotnumber_to_letter(input: int) -> str:
    res = divmod(input, 26)
    quotient = res[0]
    remainder = res[1]
    if quotient > 0:
        return f"{number_to_letter(quotient-1)}{number_to_letter(remainder)}"
    else:
        return number_to_letter(input)


if __name__ == "__main__":
    shotnumber_to_letter(27)
