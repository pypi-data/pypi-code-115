def install_packages(names: ('list', 'tuple'), def_out: 'bool' = True, sys_out: 'bool' = True):
    r'''Устанавливает список пакетов, принимает список наименований в виде строк
    *Возвращает список с кодами ошибок. 0 означает что всё прошло успешно
    *При sys_out False, не подавляет вывод полностью. Ошибки и предупреждения всеравно видны
    *Требует подключения к интернету'''
    #exec('import wafdwafd') #сделать проверку импортами, перед загрузкой
    if def_out: print(f'installing packages... 0 / {len(names)}')
    out = []
    i = 1
    for name in names:
        if def_out: print(f'installing {name}... {i} / {len(names)}')
        if sys_out: out.append(os.system(f'pip install {name}'))
        else: out.append(os.system(f'pip install {name} -q'))
        i += 1
    if def_out: print(f'installing complite! {len(names)} / {len(names)}')
    return out