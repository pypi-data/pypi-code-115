from . import utils

class TerminalAPI:

    def __init__(self, api_key, api_secret, base_url="https://api.whatspos.com/p-market-api", options=None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.options = self.__get_default_options(options)

    def __get_default_options(self, options=None):    

        default_options = {
            "serviceEndPoint": self.base_url,  
            "cookie": None,
            "algorithm": "md5",
            "timeout": 3000
        }

        if not options is None:
            for key in options:
                if options[key] is not None:
                    default_options[key] = options[key]

        return default_options


    def get_terminal(self, terminal_id, include_detail_info = False):      
        
        url = f"{self.base_url}/v1/3rdsys/terminals/{terminal_id}"
        qs = utils.get_query_string_mandatory_values(self.api_key)
        qs["includeDetailInfo"] =  include_detail_info                 
        headers = {"signature": utils.sign_query(qs=qs, secret=self.api_secret)}        
        r = utils.send_http_request(url=url, qs=qs, headers=headers)
        result =  r.json()
        if result is not None and "data" in result :
            result = result['data']
        else:
            result = None

        return result


    def get_terminal_by_tid(self, terminal_tid, include_installed_apks = False, include_installed_firmwares = False, include_detail_info = False):
        result = self.search_terminal(sn_name_tid=terminal_tid, include_installed_apks=include_installed_apks, include_installed_firmwares=include_installed_firmwares, include_detail_info=include_detail_info)        
        if result is not None and "dataset" in result and  len(result['dataset']) > 0:
            result = result['dataset'][0]
            return result
        else:
            return None

    def get_terminal_by_sn(self, serial_number, include_installed_apks = False, include_installed_firmwares = False, include_detail_info = False):
        result = self.search_terminal(sn_name_tid=serial_number, include_installed_apks=include_installed_apks, include_installed_firmwares=include_installed_firmwares, include_detail_info=include_detail_info)
        if result is not None and "dataset" in result and len(result['dataset']) > 0:
            result = result['dataset'][0]
            return result
        else:
            return None


    def get_terminal_by_name(self, terminal_name, include_installed_apks = False, include_installed_firmwares = False, include_detail_info = False):
        result = self.search_terminal(sn_name_tid=terminal_name, include_installed_apks=include_installed_apks, include_installed_firmwares=include_installed_firmwares, include_detail_info=include_detail_info)
        if result is not None and "dataset" in result and len(result['dataset']) > 0:
            result = result['dataset'][0]
            return result
        else:
            return None

    def get_terminal_by_sn_name_tid(self, sn_name_tid, include_installed_apks = False, include_installed_firmwares = False, include_detail_info = False):
        return self.search_terminal(sn_name_tid=sn_name_tid, include_installed_apks=include_installed_apks, include_installed_firmwares=include_installed_firmwares, include_detail_info=include_detail_info)
        

    def get_terminal_id_using_sn(self, serial_number):
        result = self.search_terminal(sn_name_tid=serial_number)
        if result is not None and "dataset" in result and len(result['dataset']) > 0:
            result = result['dataset'][0]
            return result['id']
        else:
            return None

    def search_terminal(self, order_by=None, status=None, sn_name_tid=None, include_geolocation = False, include_installed_apks = False, include_installed_firmwares = False, include_detail_info = False, page_no = 1, page_size = 30):
        
        url = f"{self.base_url}/v1/3rdsys/terminals"
        qs = utils.get_query_string_mandatory_values(self.api_key)

        if page_no is not None:
            qs["pageNo"]=page_no

        if page_size is not None:
            qs["pageSize"]=page_size

        if order_by is not None:
            qs["orderBy"]=order_by

        if status is not None:
            qs["status"]=status

        if sn_name_tid is not None:
            qs["snNameTID"]=sn_name_tid

        if include_geolocation is not None:
            qs["includeGeoLocation"]=include_geolocation

        if include_installed_apks is not None:
            qs["includeInstalledApks"]=include_installed_apks

        if include_installed_firmwares is not None:
            qs["includeInstalledFirmware"]=include_installed_firmwares

        if include_detail_info is not None:
            qs["includeDetailInfo"]=include_detail_info

        qs["includeDetailInfo"]=True

        headers = {"signature": utils.sign_query(qs=qs, secret=self.api_secret)}     

        r = utils.send_http_request(url=url, qs=qs, headers=headers)
        result = r.json() 

        return result

