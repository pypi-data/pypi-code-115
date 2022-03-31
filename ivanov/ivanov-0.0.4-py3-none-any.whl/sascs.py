from .core import get_sas_connect
import logging


class SASCS():
    def __init__(self, sasobjsp_user,
                       sasobjsp_pass,
                       sasobjsp_host='vs2458.imb.ru',
                       sasobjsp_port='8591',  **kwargs):
        self.sasobjsp_host = sasobjsp_host
        self.sasobjsp_port = sasobjsp_port
        self.sasobjsp_user = sasobjsp_user
        self.sasobjsp_pass = sasobjsp_pass
        self.connected = False

    def connect(self):
        logging.debug(f"Attempting to connect to {self.sasobjsp_host} on port {self.sasobjsp_port}")
        connection = get_sas_connect(sasobjsp_host=self.sasobjsp_host,
                                     sasobjsp_port=self.sasobjsp_port,
                                     sasobjsp_user=self.sasobjsp_user,
                                     sasobjsp_pass=self.sasobjsp_pass)
        if connection:
            logging.info(f"Successfully connected to {self.sasobjsp_host} on port {self.sasobjsp_port}")
            self.connected = True
            return connection




