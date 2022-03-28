"""
Saved accounts management plugin.
"""
import re
from os.path import join
from json import dump,load
from colorama import Style,Fore

from .sute.config import Files

class Account:
    def __init__(self,acc_name=None,mail=None,nick=None,pwd=None,custom=None):
        """ Convert input to dictionary & save if necessary """
        self.acc_name=acc_name
        self.json = ({"Mail":mail} if mail else {}
            )| ({"Nick":nick} if nick else {}
            )| ({"Pass":pwd} if pwd else {}
            )| ({ x:y for [x,y] in custom} if custom else {})

        if acc_name:
            self.save()
    def print(self=None,acc_name=None,json_=None):
        bold,reset = Style.BRIGHT, Style.RESET_ALL
        yellow,green = Fore.YELLOW, Fore.GREEN
        json = self.json if not json_ else json_
        acc_name=self.acc_name if self else acc_name
        suffix = " Account" if len(acc_name)<12 else ""

        print(
          f"  {green}{bold}─────── {acc_name.title()}{suffix} ───────{reset}\n" if acc_name else "",
          "\n".join([ f"  ● {yellow}{bold}{key}{reset}:\t{val}" for key,val in json.items()]), "\n",
        sep="")
    def save(self):
        """ Save the account credentials to accounts.json """
        with open(Files.accounts) as file:
            accounts = load(file)
            self.acc_name = self.rename_if_same(self.acc_name,accounts)
            accounts[self.acc_name] = self.json
        with open(Files.accounts,"w") as file:
            dump(accounts,file,indent=1)
    def rename_if_same(self=None,name=None,json_=None):
        """ Check if account name already exists and rename if necessary """
        while name in json_:
            index = re.search(r" (\d{1,3})$",name)
            name = name.replace(
                    index.group(1),
                    str(int(index.group(1))+1)
                ) if index else name+" 2"
        return name


def search_account(string):
    with open(Files.accounts) as file:
        accounts = load(file)
    string = string.lower()
    results = [(a,b) for a,b in accounts.items() if string in a.lower()]

    for name,account in results:
        Account.print(acc_name=name,json_=account)


def old2json():
    """ Convert old accounts file to new accounts.json format """
    with open(Files.accounts_old) as file:
        accs = file.read()

    while accs[-2:] != "\n\n":
        accs += "\n"

    js,accs = {},accs.replace("\n","%NEWLINE")

    for acc in re.findall("===.*?===.*?%NEWLINE%NEWLINE",accs):
        acc = acc.split("%NEWLINE")
        name = re.search("=== (.*) ===",acc[0]).group(1).replace(" Account","")
        name = Account.rename_if_same(name=name,json_=js)
        js[name]={}
        for cred in acc[1:-2]:
            if not cred:
                continue
            key,val = re.findall(r"^(\w+): (.*)",cred)[0]
            js[name][key] = val

    with open(join(Files.accounts), "w") as file:
        dump(js,file,indent=1)



if __name__ == '__main__':
    print("Updating accounts file from old format to json..")
    old2json()
