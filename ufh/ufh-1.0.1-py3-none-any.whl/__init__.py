import os
import ufh.ufhUtils as utils

class redactor():

    def __init__(self, path):
        self.path = path


    def lineIndexer(self, index, lines, firstWord):
        array = utils.fileReader(self.path)
        for  i in range(len(array)):
            line = array[i]
            if (line.find('_') == len(firstWord)):
                j = 0
                number = ''
                while line[(len(firstWord)+1)+j].isdigit():
                    number += line[(len(firstWord)+1)+j]
                    j+=1

                lineReplaced = line.replace(f'_{number}_', f'_{int(i/lines)+index}_')
                array[i] = lineReplaced

        utils.fileWriter(array, self.path)
        print('\033[36m'+'INDEXES WAS UPDATED'+'\033[37m')


    def indexIncrice(self, relativeWord, n=1):
        array = utils.fileReader(self.path)
        for  i in range(len(array)):
            line = array[i]
            if (line.find(f'{relativeWord}_')) == -1: continue
            number = ''
            j = 0

            indexPos = len(relativeWord) + line.find(relativeWord) + 1

            while line[indexPos+j].isdigit():
                number += line[indexPos+j]
                j+=1

            lineReplaced = line.replace(f'{relativeWord}_{number}', f'{relativeWord}_{int(int(number)+n)}')
            array[i] = lineReplaced


        utils.fileWriter(array, self.path)
        print(f'\033[36mINDEXES AFTER \033[33m{relativeWord}_n \033[36mWAS UPDATED \033[1;32mOK\033[0;37m')


    def renamer(self, nameOld, nameNew):
        array = utils.utils().fileReader(self.path)
        for i in range(len(array)):
            line = array[i]

            if ((nameNew in line) != True):
                lineReplaced = line.replace(nameOld, nameNew)
                array[i] = lineReplaced
            elif ((nameNew in nameOld) == True):
                lineReplaced = line.replace(nameOld, nameNew)
                array[i] = lineReplaced

        utils.fileWriter(array, self.path)
        print('\033[36m'+f'NAMES WAS UPDATED ON [{nameNew}]'+'\033[37m')


    def pricer(self, relativeWord, multiple=0.5, newNumber=0, maxPrice=False):
        array = utils.utils().fileReader(self.path)
        for i in range(len(array)):
            line = array[i]
            if (line.find(f'{relativeWord}') != -1):
                j = 0
                number = ''
                while (line.find(f'{relativeWord}')+len(relativeWord)+1+j) < len(line):
                    number += line[line.find(f'{relativeWord}')+len(relativeWord)+1+j]
                    j+=1

                if newNumber:
                    lineReplaced = line.replace(f'{number}', f'{newNumber}')
                    array[i] = lineReplaced
                else:
                    if maxPrice:
                        newNum = int(int(number)*multiple)
                        if newNum > maxPrice: newNum = maxPrice
                        lineReplaced = line.replace(f'{number}', f'{newNum}')
                        array[i] = lineReplaced
                    else:
                        lineReplaced = line.replace(f'{number}', f'{int(int(number)*multiple)}')
                        array[i] = lineReplaced

        utils.fileWriter(array, self.path)
        print('\033[36m'+'PRICES WAS UPDATED'+'\033[37m')