import re

def parseCollation(s):
    collation={'volume':None
            , 'issue':None
            , 'page':None}
    if re.match('^[0-9]+$', s):
        collation['page'] = s
    elif re.match('^[IVXLC]+$', s):
        collation['page'] = s
    elif re.match('[0-9]+ \(-[0-9]+\)$', s) or re.match('[0-9]+ \([0-9]+-[0-9]+\)$', s):
        collation['page'] = s.split(' ')[0]
    elif re.match('^[0-9]+, fig\. .*$', s):
        collation['page'] = s.split(',')[0]
    elif re.match(r'^(?P<volume>.*)\((?P<issue>.*?)\):\s*(?P<page>[0-9]+).*', s):
        m = re.match(r'^(?P<volume>.*)\((?P<issue>.*?)\):\s*(?P<page>[0-9]+).*', s)
        collation = m.groupdict()
    elif re.match(r'^(?P<volume>.*):\s*(?P<page>e?[0-9]+).*', s):
        m = re.match(r'^(?P<volume>.*):\s*(?P<page>e?[0-9]+).*', s)
        collation = m.groupdict()
        collation['issue'] = None
    return collation

def collation2volume(s):
    return parseCollation(s)['volume']

def collation2issue(s):
    return parseCollation(s)['issue']

def collation2page(s):
    return parseCollation(s)['page']

def isBook(publication):
    flag = False
    if 'isbn' in publication.keys() and publication['isbn'] is not None:
        flag = True
    if not flag: 
        if 'tl2Author' in publication.keys() and publication['tl2Author'] is not None \
                and 'date' in publication.keys() and publication['date'] is not None \
                and re.match('^(1[6-9][0-9][0-9]|20[0-2][0-9])$',publication['date']):
            flag = True
    return flag    

if __name__ == '__main__':
    main()