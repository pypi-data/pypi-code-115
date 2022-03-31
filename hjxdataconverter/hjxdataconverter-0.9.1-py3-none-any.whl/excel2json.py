import pandas as pd
import sys


def main():
    if len(sys.argv) < 3:
        print('Usage:\nexcel2json inputfile outputfile\n\n\
where the inputfile can be an excel file, path or url, and the outputfile is the name of the json file which will be created.')
        exit()

    input = sys.argv[1]
    jsonfile = sys.argv[2]

    if jsonfile.endswith('.json') == False:
        jsonfile = jsonfile + '.json'

    excel2json(input, jsonfile)

def excel2json(xlsxinput: str, jsonfile: str):
    '''Function that takes an excel file and convert it to a json file.
    The parameter xlsxinput can take either a file, path or url.
    The parameter jsonfile takes the name of the json file that the program creates.'''

    try:
        data = pd.read_excel(xlsxinput, header=2)
    except FileNotFoundError as e:
        print("File Not Found when trying to read the excel file {}.\nError message: {}".format(xlsxinput, e))
        exit()

    except ValueError as e:
        print("Value Error when trying to read the input {}, check if the url is correct or if the file is in the right format.\nError message: {}".format(xlsxinput, e))
        exit()

    except Exception as e:
        print("{} occured when trying to read the input{}.\nError message: {}".format(sys.exc_info()[0], xlsxinput, e))
        exit()

    data = data.fillna("")
    data.to_json(jsonfile, orient='records', indent=2, force_ascii=False)

if __name__ == '__main__':
    main()