import glob
import re
from dataclasses import dataclass, field

RE_TODO = r'^[ \t]*-[ \t]{1,}\[[ \t]{1}\][ \t]*(.*)$'
RE_TODO_BODY = r'(.*?)(?:[ \t]*@|$)'
RE_TODO_TAGS = r'(?:@([\w_]+)[ \t]*(?:([\w ]+?))?)(?=@|$)'

@dataclass
class ToDo:
    file: str
    body: str
    tags: list = field(default_factory=list)

def tail(lst):
  return lst[1:] if len(lst) > 1 else lst

def find_todos(text, file):
    matches = re.findall(RE_TODO, text, re.MULTILINE)

    if len(matches) == 0:
        return []

    todos = []
    for match in matches:

        tags = []
        if "@" in match:
            _tags = tail(match.split('@'))

            for tag in _tags:
                tag = tag.split(' ', 1)
                tags.append(tag)

        todo = ToDo(
            body = re.findall(RE_TODO_BODY, match)[0],
            tags = tags,
            file = file
        )
        todos.append(todo)
        
    return todos

def read_vault():
    todos = []
    for file in glob.glob("**/*.md"):
        with open(file) as f:
            text=f.read()
            todos = todos + find_todos(text, file)
    return todos

def today():
    print("today")

def tomorrow():
    print("today")

def no_due_date():
    print("no due date")

def someday():
    print("someday")
