import json
import xlwt
from json import JSONDecodeError

def parse_one_data(data, key_list=[], value_list=[],title="",list_format=","):

    if type(data) is list:
        for d in data:
            if type(d) is list or type(d) is dict:
                key_list, value_list = parse_one_data(d,key_list=key_list,value_list=value_list)
            else:
                key_list.append(str(title))
                value_list.append(list_format.join(data))
                break
        return key_list,value_list

    for key, value in data.items():
        if type(value) is dict or type(value) is list:
            key_list,value_list = parse_one_data(value,key_list=key_list,value_list=value_list,title=key)
        else:
            key_list.append(str(key))
            value_list.append(str(value))

    return key_list, value_list

def get_list_data(data,key):

    return data[key]


def parse_data(string, primary_key=".",is_print_key=False,list_format=',',**kwargs):
    data = json.loads(string)
    one_data = data
    for i in primary_key.split('.'):
        i = i.strip()
        if not i:
            continue
        if not one_data:
            continue
        one_data = get_list_data(one_data,i)
    if type(one_data) is not list:
        one_data = [one_data]
    for index,one in enumerate(one_data):
        key_list,value_list = parse_one_data(one,key_list=[],value_list=[])
        # print(key_list,value_list)
        if is_print_key and index==0:
            yield key_list
        yield value_list

def print_data(string, primary_key=".",is_print_key=False,list_format=',',**kwargs):
    iter_data = parse_data(string,primary_key=primary_key,is_print_key=is_print_key,list_format=list_format)
    for line_data in iter_data:
        print_string = list_format.join(line_data)
        print(print_string)

def parse_file_data(file_name,primary_key=".",is_print_key=False,list_format=",", **kwargs):
    excel_file_name = kwargs['excel_file_name'] if "excel_file_name" in kwargs else None
    xf = None
    if excel_file_name:
        xf = xlwt.Workbook()
        sheet = xf.add_sheet('sheet',cell_overwrite_ok=True)
    col = 0
    with open(file_name, 'r') as f:
        for i in f:
            i = i.strip()
            if not i:
                continue
            iter_data = parse_data(i,primary_key=primary_key,is_print_key=is_print_key,list_format=list_format)
            for line_data in iter_data:
                if excel_file_name:
                    for row,l in enumerate(line_data):
                        sheet.write(col,row,l)
                    col += 1
                print(list_format.join(line_data))
            else:
                pass
            if is_print_key:
                is_print_key = False
    
    if excel_file_name:
        xf.save(excel_file_name)
