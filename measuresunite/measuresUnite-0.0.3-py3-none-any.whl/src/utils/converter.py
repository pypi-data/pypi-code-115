from measuresUnite.src.unit_systems.si import si_dict


def unit_extend(unit_0):
    lst = []
    curr = ''
    for item in list(unit_0):
        if item in '^*/':
            lst.append(curr)
            lst.append(item)
            curr = ''
        else:
            curr += item
    if curr != '':
        lst.append(curr)

    new_lst = []
    for item in lst:
        if item.isnumeric() or item in '^*/':
            new_lst.append(item)
        else:
            try:
                new_lst.append(si_dict[item])
            except:
                raise ValueError(f'Unit {item} is not supported. Consider using SI units.')

    return ''.join(new_lst)
