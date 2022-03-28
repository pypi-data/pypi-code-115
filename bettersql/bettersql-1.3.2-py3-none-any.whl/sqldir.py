# pip install tabulate
import os
import pandas as pd

def find_owner(uid):
    from pwd import getpwuid
    return getpwuid(uid).pw_name

def unixtodate(ts):
    from datetime import datetime
    return datetime.fromtimestamp(ts) #.strftime('%Y-%m-%d %H:%M:%S')

class FileEntry():
    import os

    def __init__(self, file: os.DirEntry, rootdir = None):
        self.name = file.name
        self.fullname = file.path

        self.path = file.path[:-1 * len(file.name)]

        f = file.name.rfind('.')
        self.extension = '' if f == -1 else file.name[f + 1 :]
        self.basename = self.name if f == -1 else file.name[: f]
        self.isdir = file.is_dir()
        self.isfile = file.is_file()
        self.issymlink = file.is_symlink()
        stat = file.stat()
        self.size = stat.st_size
        self.created = unixtodate(stat.st_ctime)
        self.modified = unixtodate(stat.st_mtime)
        self.changed = unixtodate(stat.st_ctime)
        self.owner = find_owner(stat.st_uid)
        if rootdir:
            if rootdir[-1] == '/':
                rootdir = rootdir[:-1]
            self.parent = self.path[len(rootdir):]
            self.level = self.parent.count('/') # + 0 if len(x) > 0 and x[-1] == '/' else 1
        else:
            self.level = 0
            self.parent = '.'

    def __repr__(self) -> str: 
        return f'Name = "{self.name}" Path = "{self.path}" Size = {self.size} Owner = {self.owner} Created = {self.created} Modified = {self.modified} Changed = {self.changed}'
    
def scantree(path, follow_symlinks = False, recursive = True):
    for entry in os.scandir(path):
        if recursive and entry.is_dir(follow_symlinks = follow_symlinks):
            yield entry
            yield from scantree(entry.path)
        else:
            yield entry

 

# def get_table_names(sql):
#     import re
#     x = re.split('from |FROM |From |join |JOIN |Join ', sql)
#     print('******')
#     tables = [t[:f'{t} .'.index(' ')] for t in x][1:]
#     return tables


def sqldir(sql: str, output: str = 'dataframe'):
    from sqldf import sqldf, get_table_names
    from os.path import expanduser
    tablenames = get_table_names(sql)

    if len(tablenames) >= 1:
        sql0 = sql
        dirs = dict()
        cnt = 1
        for t in tablenames: 
            sql0 = sql0.replace(t, f'd{cnt}')
            scan = [FileEntry(f, rootdir = expanduser(t)) for f in scantree(expanduser(tablenames[cnt - 1]))]
            scandf = pd.DataFrame((o.__dict__ for o in scan))
            dirs[f'd{cnt}'] = scandf
            cnt += 1

        r = sqldf(sql0, output = output, **dirs)
        return r

# def format_df(df):
#     """
#     Return the test stats report as a single string
#     with left-justified columns.

#     """
#     import functools
#     # Columns containing boolean values need different format strings
#     # to avoid 'ValueError: Invalid format specifier' exceptions.
#     BOOL_COLUMNS = ['success',]

#     formatters = {}
#     for li in list(df.columns):
#         if li in BOOL_COLUMNS:
#             form = "{{!s:<5}}".format()
#         else:
#             max = df[li].str.len().max()
#             form = "{{:<{}s}}".format(max)

#         formatters[li] = functools.partial(str.format,form)

#     return df.ta.to_string(formatters=formatters, index=False)

if __name__ == '__main__':
    import sys
    from tabulate import tabulate

    args = sys.argv
    #print(args)
    if len(args) > 1:
        sql = args[1]
        print(sql)
    else:
        sql = '''select name, path, size, level, parent from ~/Downloads/dir1/ as t1'''
        #sql = '''select name, path, size, level, isfile from ~/Downloads/dir1 as t1 where level = 1'''
        sql = '''select name, path, size, level, parent from ~/Downloads/dir1/ as t1 where name like "file%"'''

 
    # sql = '''select * from /Users/joey/Downloads/dir1 as t1 
    # join /Users/joey/Downloads/dir2 as t2 on t1.name = t2.name'''

    # sql = '''select t1.name as name1, t2.name as name2 from /Users/joey/Downloads/dir1 as t1 
    # join /Users/joey/Downloads/dir2 as t2 on t1.name = t2.name'''

    sql = sql.replace('select 1 ', 'select name, created, size ')
    sql = sql.replace('select 2 ', 'select name, created, modified, size ')
    sql = sql.replace('select 3 ', 'select name, created, owner, size ')


    df = sqldir(sql, output = 'dataframe')
    #print(format_df(df))
    #df.style.set_properties(subset=['name'], **{'text-align': 'left'})
    #.set_table_styles([ dict(selector='th', props=[('text-align', 'left')] ) ])
#    print(type(d))
    #print(df)
    # for e in d:
    #     print(e)
    #print(df.to_string(index=False))
    print(tabulate(df, showindex=False, headers='keys', tablefmt='fancy_grid'))


    # for x in sqldir(sql):
    #     print(x)
    # import os.path as p
    # f = '~/Downloads/dir1/file1.csv'
    # f1 = p.expanduser(f)
    #print(f'{p.basename(f)=} {p.abspath(f)}= {p.dirname(f)=} {p.relpath(f, "/Users/Downloads/")=}')