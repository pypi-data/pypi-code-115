import pandas as pd
from datetime import datetime
import sys


def main():
    if len(sys.argv) < 3:
        print("Usage:\njson2excel inputfile outputfile\n\n\
where the inputfile can be a json file, path or url, and the outputfile is the name of the excel document which will be created.")
        exit()

    input = sys.argv[1]
    xlsxfile = sys.argv[2]

    if xlsxfile.endswith('.xlsx') == False:
        xlsxfile = xlsxfile + '.xlsx'

    json2excel(input, xlsxfile)


def json2excel(jsoninput: str, xlsxfile: str):
    '''Function that converts json text to an excel document.
    The parameter jsoninput can take a url, path, filename or string on json format, as long as it is in the format records. 
    The parameter xlsxfile takes the filename of the new excel file that the program creates.'''
    
    try:
        data_new = pd.read_json(jsoninput, orient='records')

    except ValueError as e:
        print("Value Error occured when trying to read the json input, make sure the json string, file or url is in the right format.\
\nError message: {}".format(e))
        exit()
    except FileNotFoundError as e:
        print("File Not Found when trying to read the json file.\nEroor message: {}".format(e))
        exit()
    except Exception as e:
        print("{} occured when trying to read the json input.\nError message: {}".format(sys.exc_info()[0], e))
        exit()


    text1='Landets Apotek'
    date=datetime.now().strftime("%d.%m.%Y")
    text2='Oversikt oppdatert: ' + date

    try:
        writer = pd.ExcelWriter(xlsxfile)
        
    except ValueError as e:
        print("Value Error occured when trying to create the Excel writer. Make sure that the xlsxfile {} is in one of the excel formats\n\
Error message: {}".format(xlsxfile, e))
        exit()
    except Exception as e:
        print("{} occured when trying to create the Excel writer with the file {}.\nError message: {}".format(sys.exc_info()[0],xlsxfile, e))
        exit()

    data_new.to_excel(writer, startrow=2, startcol=0, index=False)
    worksheet=writer.sheets['Sheet1']
    worksheet.write(0,0,text1)
    worksheet.write(1,0,text2)
    writer.save()


if __name__ == '__main__':
    main()

