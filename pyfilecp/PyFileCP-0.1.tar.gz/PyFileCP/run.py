from PyFileCP import copyfile

def command(string):
    if isinstance(string, list):
        notstring = string
        string = ' '.join(notstring)
    string = str(string)
    cmdList = string.strip().split(' ')
    file = copyfile.Copy(cmdList[1], cmdList[2])
    if '--replace' in cmdList:
        with file as replace:
            replace(cmdList[4], cmdList[5])

    file.commit()

if __name__ == '__main__':
    from sys import argv
    command(argv)