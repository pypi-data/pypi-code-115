from .core import get_sas_connect


class SASMA():
    def __init__(self, sasobjsp_user,
                       sasobjsp_pass,
                       sasobjsp_host='vs246.imb.ru',
                       sasobjsp_port='8591',  **kwargs):
        self.sasobjsp_host = sasobjsp_host
        self.sasobjsp_port = sasobjsp_port
        self.sasobjsp_user = sasobjsp_user
        self.sasobjsp_pass = sasobjsp_pass
        self.connected = False

    def connect(self):
        connection = get_sas_connect(sasobjsp_host=self.sasobjsp_host,
                                     sasobjsp_port=self.sasobjsp_port,
                                     sasobjsp_user=self.sasobjsp_user,
                                     sasobjsp_pass=self.sasobjsp_pass)
        if connection:
            self.connected = True
            return connection
