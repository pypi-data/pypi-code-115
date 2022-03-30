from time import sleep
import csv
from argparse import ArgumentParser
from typing import Dict
from paxstore_open_api_sdk.terminal_api import TerminalAPI
import functions
from mysql_helper import execute_select_for_results, execute as mysql_execute,  get_mysql_connection
from progress.bar import Bar
from progressbar import progressbar




def get_args():
    parser = ArgumentParser(description='Download Pax terminals list')
    # API client settings
    parser.add_argument("-k", "--pax-api-key", dest="pax_api_key",
                        help="the apiKey of marketplace, get this key from PAXSTORE admin console. Please visit: https://novelpay.whatspos.com/admin#/sysConfig")
    parser.add_argument("-s", "--pax-api-secret", dest="pax_api_secret",                     
                        help="apiSecret, get api secret from PAXSTORE admin console. Please visit: https://novelpay.whatspos.com/admin#/sysConfig")
    parser.add_argument("-u", "--pax-base-url", dest="pax_base_url",  default="https://api.whatspos.com/p-market-api",                   
                        help="Paxstore API URL.")
    # API response preferences
    parser.add_argument("-t", "--include-detail-info", dest="include_detail_info",  default=False, help="whether to include the terminal detail information in search result.")
    parser.add_argument("-l", "--include-geo-location", dest="include_geo_location",  default=False, help="whether to include geo location information in search result.")
    parser.add_argument("-a", "--include-installed_apks", dest="include_installed_apks",  default=False, help="whether to include install applications in search result.")
    parser.add_argument("-f", "--include-installed_firmware", dest="include_installed_firmware",  default=False, help="whether to include the firmware version of the terminal in search result.")
    # mysql config
    parser.add_argument("-m", "--mysql-host", dest="mysql_host", help="Mysql Host")
    parser.add_argument("-c", "--mysql-user", dest="mysql_user", help="Mysql User")
    parser.add_argument("-p", "--mysql-password", dest="mysql_password", help="Mysql User's password")
    parser.add_argument("-d", "--mysql-database", dest="mysql_database", help="Mysql database name")
    parser.add_argument("-b", "--mysql-table-terminals", dest="mysql_terminals_table_name", default="TPE", help="Terminals Table name")
    return parser.parse_args()


def create_terminals_csv_file(filename):
    # CSV file settings
    csv_headers = ['SERIAL_NUMBER', 'TPE', 'ID_TERMINAL_GP', 'ID_TERMINAL_PAX', 'ICCID', 'IMEI', 'MAC_ASSRESS', 'IP', 'CELL_ID','DATE_DERNIERE_CONNEXION']
    # Open file for writing    
    csv_file = open(f"{filename}","w")
    # Write csv file headers
    csv_writer = csv.writer(csv_file,delimiter=',')
    csv_writer.writerow(csv_headers)
    csv_file.close()

    return filename
    

def write_terminals_data_in_csv_file(terminals, filename):
    csv_file = open(f"{filename}","a")
    csv_writer = csv.writer(csv_file,delimiter=',')
    for terminal in terminals:
        iccid=  terminal['terminalDetail']['iccid'] if 'terminalDetail' in terminal and 'iccid' in terminal['terminalDetail'] else '-'
        imei= terminal['terminalDetail']['imei'] if 'terminalDetail' in terminal and 'imei' in terminal['terminalDetail'] else '-'
        mac_address= terminal['terminalDetail']['macAddress'] if 'terminalDetail' in terminal and 'macAddress' in terminal['terminalDetail'] else '-'
        ip= terminal['terminalDetail']['ip'] if 'terminalDetail' in terminal and 'ip' in terminal['terminalDetail'] else '-'
        cell_id= terminal['terminalDetail']['cellid'] if 'terminalDetail' in terminal and 'cellid' in terminal['terminalDetail'] else '-'
        serial_no = terminal["serialNo"] if "serialNo" in terminal else "-"
        name = terminal["name"] if "name" in terminal else "-"
        terminal_pax_id = terminal["id"] if "id" in terminal else "-"
        terminal_gp_id = terminal["gp_id"] if "gp_id" in terminal else "-"
        terminal_pax_last_active_time = terminal["lastActiveTime"] if "lastActiveTime" in terminal else "-"       
        csv_writer.writerow(([serial_no, name, terminal_gp_id, terminal_pax_id, iccid, imei, mac_address, ip, cell_id, terminal_pax_last_active_time]))
    csv_file.close()


def run_pax_exclusive(terminal_api_client: TerminalAPI, progress_bar: Bar, filename: str, include_geo_location=False, include_installed_apks=False, include_installed_firmware=False, include_detail_info=False ):
   
    # Get terminals from paxstore only without cross checking with any other data source like GP database
    # Count available terminals in paxstore
    terminals_search_result = terminal_api_client.search_terminal(page_size=1)
    terminals_search_result_count = terminals_search_result["totalCount"] if "totalCount" in terminals_search_result else 0
    # Configure progress bar maximum valu
    download_bar_count = terminals_search_result_count
    if progress_bar is not None:
        progress_bar.max = download_bar_count

    """
    Get all availables terminals in paxstore recursively, base on response fiels 'hasNext'
    """
    def get_terminals_from_pax_and_write(filename, page_no=1, ask_for_next_results=True):
        terminals = []
        results = terminal_api_client.search_terminal(include_detail_info=include_detail_info, include_geolocation=include_geo_location, include_installed_apks=include_installed_apks, include_installed_firmwares=include_installed_firmware, page_no=page_no)
        more_results = "hasNext" in results and results["hasNext"] is True
        current_page_no = (1, results["pageNo"])["pageNo" in results]
        if "dataset" in results and not results["dataset"] is None and len(results["dataset"] ) > 0:
            for terminal in results["dataset"]:
                #print(terminal),exit()
                if include_detail_info:
                    terminal_data = terminal_api_client.get_terminal(terminal["id"],include_detail_info=include_detail_info)
                    if progress_bar is not None:
                        progress_bar.next()
                    terminals.append(terminal_data)
                else:
                    if progress_bar is not None:
                        progress_bar.next()
                    terminals.append(terminal)
            # Write terminals on disk
            write_terminals_data_in_csv_file(terminals=terminals, filename=filename)
        if more_results and ask_for_next_results:
            # Do it again :)
            get_terminals_from_pax_and_write(page_no=current_page_no+1, filename=filename)
    
    # Start progress bar
    if progress_bar is not None:
        progress_bar.start()

    # Get terminals from paxstore and write them on the disk
    get_terminals_from_pax_and_write(page_no=1, filename=filename)

    # Update progress bar to finish status
    if progress_bar is not None:
        progress_bar.finish()


def run_with_database_cross_checking(terminal_api_client: TerminalAPI, progress_bar: Bar, filename: str,  include_geo_location=False, include_installed_apks=False, include_installed_firmware=False, include_detail_info=False, mysql_host=None, mysql_user=None, mysql_password=None, mysql_database=None, mysql_terminals_table_name=None ):
    
    # Get Mysql Connection
    connection = get_mysql_connection(host=mysql_host,user=mysql_user,password=mysql_password,database=mysql_database)

    # Get All Terminals in database
    print("Reading terminals from database.")
    db_tpe = execute_select_for_results(f"select * from {mysql_terminals_table_name}",connection)
    print("Done !")

    if progress_bar is not None:
        progress_bar.max = len(db_tpe)

    # Start progress bar
    if progress_bar is not None:
        progress_bar.start()

    for tpe in db_tpe:

        terminal_data = terminal_api_client.get_terminal_by_sn(tpe[4], include_detail_info=include_detail_info ,include_installed_apks = include_installed_apks, include_installed_firmwares = include_installed_firmware )
        #print(terminal_data),exit()
        if terminal_data is not None:            
            terminal_data["gp_id"] = tpe[3]
            if progress_bar is not None:
                progress_bar.next()
            write_terminals_data_in_csv_file(terminals=[terminal_data], filename=filename)
        

    # Update progress bar to finish status
    if progress_bar is not None:
        progress_bar.finish()



def run(api_key, api_secret, api_url = None, include_geo_location=False, include_installed_apks=False, include_installed_firmware=False, include_detail_info=False, mysql_host=None, mysql_user=None, mysql_password=None, mysql_database=None, mysql_terminals_table_name=None ):
    
    # Which algorithm ?
    pax_exclusive = False if mysql_host is not None and mysql_user is not None and mysql_database is not None else True

    # Create reslt csv file
    filename = functions.generate_file_name()
    create_terminals_csv_file(filename)
    
    # Create progress bar
    bar = Bar( f"Generating file '{filename}' " + ('[PAX]','[xBDx]')[not pax_exclusive], fill='█', empty_fill="░", suffix=' %(index)d/%(max)d - %(percent).1f%% - %(eta)ds', max = 0)
    
    # Instanciating new paxstore api client
    terminal_api_client =  (TerminalAPI(api_key=api_key, api_secret= api_secret), TerminalAPI(api_key=api_key, api_secret= api_secret, base_url=api_url))[api_url is None]
    
    if pax_exclusive : 
        # Get terminals from paxstore only without cross checking with any other data source like GP database
        run_pax_exclusive(terminal_api_client=terminal_api_client, progress_bar=bar, filename=filename, include_geo_location=include_geo_location, include_installed_apks=include_installed_apks, include_installed_firmware=include_installed_firmware, include_detail_info=include_detail_info ) 
    else:
        # Get terminals from paxstore by cross checking with Mysql database
        run_with_database_cross_checking(terminal_api_client=terminal_api_client, progress_bar=bar, filename=filename, include_geo_location=include_geo_location, include_installed_apks=include_installed_apks, include_installed_firmware=include_installed_firmware, include_detail_info=include_detail_info, mysql_host=mysql_host, mysql_user=mysql_user, mysql_password=mysql_password, mysql_database=mysql_database, mysql_terminals_table_name=mysql_terminals_table_name )
    
    print(f"download completed: {filename}")

args = get_args()



run(
      api_key=args.pax_api_key
    , api_secret=args.pax_api_secret
    , api_url=args.pax_base_url

    , include_detail_info= bool(args.include_detail_info)
    , include_geo_location=bool(args.include_geo_location)
    , include_installed_apks=bool(args.include_installed_apks)
    , include_installed_firmware=bool(args.include_installed_firmware)

    , mysql_host=args.mysql_host
    , mysql_user=args.mysql_user
    , mysql_password=args.mysql_password
    , mysql_database=args.mysql_database
    , mysql_terminals_table_name=args.mysql_terminals_table_name)
