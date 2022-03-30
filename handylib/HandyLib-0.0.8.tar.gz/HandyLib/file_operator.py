# coding=utf-8
'''
Operations relates to file
'''
import os
import json
import sys


def find_duplicates(path, mode=0):
    '''
    return a dict of all duplicate files
    mode: 0: if modified date and size are the same,then they are same file

    '''
    files = filter_folder_recursively(path)
    temp = {}
    if mode == 0:
        for f in files:
            changeDT = os.path.getmtime(f)
            size = os.path.getsize(f)
            if not size in temp:
                temp[size] = {}
            if not changeDT in temp[size]:
                temp[size][changeDT] = []
            temp[size][changeDT].append(f)

    # remove non-dup
    result = {}
    for s in temp:
        for dt in temp[s]:
            if len(temp[s][dt]) > 1:
                if not s in result:
                    result[s] = {}
                result[s][dt] = temp[s][dt]
    return result


def read_config(p='config.json'):
    return read_dict(p)


def read_dict(p):
    '''
    return a dict formated config file
    if file open error, then return a empty dict
    '''
    try:
        return json.loads(read_file(p))
    except:
        return {}


def save_config(d, p='config.json'):
    return save_dict(d, p)


def save_dict(d, p,ensure_ascii=True):
    '''
    save dict to json file
    '''
    save_file(p, json.dumps(d, sort_keys=True, indent=4,ensure_ascii=ensure_ascii), p + ' updated')


def save_file(p, d, m='', t='w'):
    '''
    write to file
    do not use this for large files
    you can use this to print messages
    p:path
    d:data
    m: message to print after finished writing
    t: type 'w' by default
    '''
    f = open(p, t)
    f.write(d)
    f.close()
    if not m == '':
        print(m)


def read_file(p, mode='r'):
    '''
    read file and return data
    do not use this for large files
    '''
    f = open(p)
    data = f.read()
    f.close()
    return data


def empty_folder(str_path_to_folder):
    '''
    remove all files under this folder
    print error message if failed
    '''
    for the_file in os.listdir(str_path_to_folder):
        file_path = os.path.join(str_path_to_folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(e)


def split_big_file_by_line_number(path, line_num=60000):
    '''
    split big file, not working properlly
    '''
    f_r = open(path, 'r')
    name, extension = path.split('.')
    count = 0
    sub_file_num = 0
    out_f = open(name+'_{0}.{1}'.format(sub_file_num, extension), 'w')
    for line in f_r:
        out_f.write(line)
        count += 1
        if count == line_num:
            count = 0
            out_f.close()
            sub_file_num += 1
            out_f = open(name+'_{0}.{1}'.format(sub_file_num, extension), 'w')
    out_f.close()
    if count == 0:
        os.unlink(name+'_{0}.{1}'.format(sub_file_num, extension))


def if_file_has_keyword(f, keywords):
    for k in keywords:
        if f.find(k) >= 0:
            return True
    return False


def filter_folder(path='', filter_out_flag=False, key_words=[]):
    '''
    path: a string of the path. default is '',means use current folder.
    filter_out_flag: a boolean indicating whether is include or exclude key words
    key_words: a list of strings. default is empty, the function will return all files inside
    ignore folders inside
    list files with or without specific key words
    if keyword list is empty, then returns all files in that folder
    '''
    if path == '':
        raw_file_list = os.listdir()
    else:
        raw_file_list = os.listdir(path)
    temp = []
    for item in raw_file_list:
        if os.path.isfile(os.path.join(path, item)):
            temp.append(os.path.join(path, item))
    raw_file_list = temp
    have_keywords = []
    no_keywords = []
    if key_words == []:
        return raw_file_list
    for f in raw_file_list:
        if if_file_has_keyword(f, key_words):
            have_keywords.append(f)
        else:
            no_keywords.append(f)
    if filter_out_flag:
        return list((set(no_keywords)))
    else:
        return list((set(have_keywords)))


def filter_folder_recursively(base_path='', filter_out_flag=False, key_words=[]):
    '''
    list files with or without specifical key words
    if keyword list is empty, then returns all files in that folder
    if filter_out_flag is false,then returns all files with any word in key_words
    '''

    if base_path == '':
        raw_file_list = os.listdir()
    else:
        raw_file_list = os.listdir(base_path)
    raw_file_list = list(
        map(lambda x: os.path.join(base_path, x), raw_file_list))
    temp = []
    folders = []
    for item in raw_file_list:
        if os.path.isfile(item):
            temp.append(item)
        elif os.path.isdir(item):
            folders.append(item)
    sub_result = []

    for folder in folders:
        if (base_path == ''):
            sub_result += filter_folder_recursively(os.path.join(
                base_path, folder), filter_out_flag, key_words)
        else:
            sub_result += filter_folder_recursively(
                folder, filter_out_flag, key_words)
    raw_file_list = temp
    have_keywords = []
    no_keywords = []

    if key_words == []:
        return raw_file_list + sub_result
    for f in raw_file_list:
        for keyword in key_words:
            if f.find(keyword) >= 0:
                have_keywords.append(f)
            else:
                no_keywords.append(f)
    # print(have_keywords)
    # print(no_keywords)
    # input()
    if filter_out_flag:
        return no_keywords + sub_result
    else:
        return have_keywords + sub_result


def remove_empty_folder(path='', escape=['System Volume Information', '$RECYCLE.BIN', '.verysync']):
    '''
    remove all empty folders with in the given path recursively
    '''
    if path == '':
        path = os.getcwd()
    items = os.listdir(path)
    sub_files = []
    sub_dirs = []
    for i in items:
        if os.path.isdir(os.path.join(path, i)):
            if not (i in escape):
                sub_dirs.append(os.path.join(path, i))
        else:
            sub_files.append(os.path.join(path, i))
    for folder in sub_dirs:
        remove_empty_folder(os.path.join(path, folder))
    if not os.listdir(path):
        print("removing: {0}".format(path))
        try:
            os.rmdir(path)
        except Exception as e:
            print(e)
    else:
        # print(root)
        # input(sub_files)
        pass


def dig(path='', keep_path_info=False, saprater="-_-", escape=['$Recycle.Bin', sys.argv[0]]):
    if path == '':
        path = os.getcwd()
    for root, dirs, files in os.walk(path):
        for word in escape:
            if word in dirs:
                dirs.remove(word)
        for dir in dirs:
            dig(os.path.join(path, dir))
        while (len(files) == 0 and len(dirs) == 1):
            next_path = os.path.join(path, dirs[0])
            cmd = "move \"{0}\\*\" \"{1}\\.\"".format(next_path, root)
            input(cmd)
            os.system(cmd)
            if not os.listdir(next_path):
                os.removedirs(next_path)

    # dir()
                # shutil.move(os.path.join(path,sub_root,d),path)
                # for f in sub_files:
                # 	shutil.move(os.path.join(path,sub_root,f),path)
                # os.remove(os.path.join(path,sub_root))


def get_new_name(base_name, num, ext):
    '''add num until get a file name that do not exist'''

    name = '{0}_{1}.{2}'.format(base_name, num, ext)
    while os.path.isfile(name):
        num += 1
        name = '{0}_{1}.{2}'.format(base_name, num, ext)
    return name


def split_big_file(path):
    if os.path.isfile(path):
        split_big_file_by_line(path)
    elif os.path.isdir(path):
        files = os.listdir(path)
        for f in files:
            split_big_file_by_line(path+f)


def split_big_file_by_line(path, size=1000*10):
    '''
    split a big file based on line

    '''
    if os.path.isfile(path):
        f = open(path, 'r')
        tail = path.split('.')[-1]
        base_name = path[:-len(tail)-1]

        temp = []
        sub_num = 0
        for line in f:
            if len(temp) < size:
                temp.append(line)
            else:
                f_o = open(get_new_name(base_name, sub_num, tail), 'w')
                f_o.writelines(temp)
                f_o.close()
                temp = []
        f_o = open(get_new_name(base_name, sub_num, tail), 'w')
        f_o.writelines(temp)
        f_o.close()
        f.close()
        os.unlink(path)


if __name__ == "__main__":
    pass
