import re

def separateId(s):
    prefix=s
    id=None
    if s is not None and ' ' in s:
        id = s.rsplit(' ',1)[1]
        patterns=['[0-9]+[\.\-]?[0-9]+','[0-9]+[\.\-]?[0-9]+[A-Za-z]','[A-Z]+\-?[0-9]+[\.\-]?[0-9]+']
        if re.match('|'.join(patterns),id):
            prefix = s.rsplit(' ',1)[0]
        else:
            id = None
    else:
        pattern='([A-Z]+)[\-\.]?([0-9]+.*)'
        m = re.match(pattern,s)
        if m:
            prefix=m.groups()[0]
            id=m.groups()[1]
    return (prefix,id)

def extractTypeHolders(s):
    typeholders = None
    if s is not None:
        typeholders = []
        prev_type_of_type = None
        prev_type_holder = None
        for type_holder_frag in s.split(';'):
            if type_holder_frag in ['null', '']:
                continue
            typeholder = dict()
            if not ' ' in type_holder_frag and prev_type_of_type is not None and prev_type_holder is not None:
                # This type is simply an object number, the type of type and holder must be read from the previous iteration
                typeholder['type_of_type'] = prev_type_of_type
                typeholder['type_holder'] = prev_type_holder
                typeholder['type_id'] = type_holder_frag
            else:
                typeholder['type_of_type'] = type_holder_frag.split(' ', 1)[0]
                typeholder['type_holder'] = type_holder_frag.split(' ', 1)[1]
                if re.search('[0-9]', typeholder['type_holder']):
                    prefix, id = separateId(typeholder['type_holder'])
                    typeholder['type_holder'] = prefix
                    typeholder['type_id'] = id
            typeholders.append(typeholder)
            prev_type_of_type = typeholder['type_of_type']
            prev_type_holder = typeholder['type_holder']
        pass
    return typeholders

def main():
    s="holotype MICH;isotype AMES;isotype DAV 89230;105887;isotype F;isotype MA;isotype NY [2 sheets]"
    print(s)
    print(extractTypeHolders(s))

if __name__ == '__main__':
    main()
