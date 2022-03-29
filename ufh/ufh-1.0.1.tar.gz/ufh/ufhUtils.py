import os

def fileReader(path):
    array = []
    with open(path) as file:
        array = [row.strip() for row in file]
    return array

def fileWriter(array, path):
    with open(path, 'w') as file:
        for  i in range(len(array)):
            line = array[i]
            file.write(line + '\n')

def datFiles(path):
    files = []
    n = 0
    for filename in os.listdir(path):
        if (os.path.isdir(f'{path}/{filename}')):
            datFiles(f'{path}/{filename}')
        else:
            if (filename.find('.dat') != -1):
                files.insert(n, f'{path}/{filename}')
                n+=1
    return files

def guidDeleter(path):
    for filename in datFiles(path):
        print(filename)
        array = fileReader(f'{filename}')
        if (array[0].find('GUID') != -1):
            array.remove(array[0])

            fileWriter(array, f'{filename}')
            print(f'GUID deleted in {filename}')