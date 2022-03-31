import pandas as pd
import sys

def main():
    if len(sys.argv) < 3:
        print("Usage:\nexcel2json inputfile outputfile\n\n\
where the inputfile can be a json file, path or url, and the outputfile is the name of the html file which will be created.")
        exit()

    input = sys.argv[1]
    htmlfile = sys.argv[2]

    if htmlfile.endswith('.html') == False:
        htmlfile = htmlfile + '.html'

    json2thtml(input, htmlfile)


def json2thtml(jsoninput: str, htmlfile: str):
    '''Converts json text a html file.
    The parameter jsoninput can take a url, path, filename or string on json format, as long as it is on the format records.
    The parameter htmlfile is the name of the html file that the program creates'''

    try:
        data = pd.read_json(jsoninput, orient='records')

    except ValueError as e:
        print("Value Error occured when trying to read the json string, make sure you have the right url or that the json string or file is in the right format.\
\nError message: {}".format(e))
        exit()

    except FileNotFoundError as e:
        print("File Not Found when trying to read the json file.\nEroor message: {}".format(e))
        exit()

    except Exception as e:
        print("{} occured when trying to read the json input.\nError message: {}".format(sys.exc_info()[0], e))
        exit()

    data = data.fillna("")
    data.rename(columns=data.iloc[0], inplace = True)
    data.drop(data.index[0], inplace = True)

    try:    
        data.to_html(htmlfile, index=False)
    except Exception as e:
        print("{} occured when trying to convert the data to html.\nError message: {}".format(sys.exc_info()[0], e))
        exit()


if __name__ == '__main__':
    main()