import pandas as pd
import sys

def main():
    if len(sys.argv) < 3:
        print("Usage:\nhtml2json inputfile outputfile\n\n\
where the inputfile can be a html file, path or url, and the outputfile is the name of the json file which will be created.")
        exit()

    input = sys.argv[1]
    jsonfile = sys.argv[2]

    if jsonfile.endswith('.json') == False:
        jsonfile = jsonfile + '.json'

    html2json(input, jsonfile)

def html2json(htmlinput: str, jsonfile: str):
    '''Function that converts html to a json file.
    The parameter htmlinput can take a html file, path or url.
    The parameter jsonfile takes the name of the json file that the program creates.'''

    try:
        data = pd.read_html(htmlinput, encoding='utf-8')[0]
    except ImportError as e:
        print("Import Error when trying to read the input {}, check if the url or filename is correct.\nError message: {}".format(htmlinput, e))
        exit()
    except Exception as e:
        print("{} occured when trying to read the input {}.\nError message: {}".format(sys.exc_info()[0], htmlinput, e))
        exit()

    data = data.fillna("")
    data.to_json(jsonfile, orient='records', indent=2, force_ascii=False)

if __name__ == '__main__':
    main()
