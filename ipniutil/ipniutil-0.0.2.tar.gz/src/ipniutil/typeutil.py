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
        for type_holder_frag in s.split(';'):
            typeholder = dict()
            typeholder['type_of_type'] = type_holder_frag.split(' ', 1)[0]
            typeholder['type_holder'] = type_holder_frag.split(' ', 1)[1]
            if re.search('[0-9]', typeholder['type_holder']):
                prefix, id = separateId(typeholder['type_holder'])
                typeholder['type_holder'] = prefix
                typeholder['type_id'] = id
            typeholders.append(typeholder)
        pass
    return typeholders

def main():
    print(extractTypeHolders('holotype NSW 262035;isotype CANB;isotype K;isotype MEL'))

if __name__ == '__main__':
    main()
