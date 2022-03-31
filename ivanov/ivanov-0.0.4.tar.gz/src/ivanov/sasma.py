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
        self.connection = None

    def connect(self):
        connection = get_sas_connect(sasobjsp_host=self.sasobjsp_host,
                                     sasobjsp_port=self.sasobjsp_port,
                                     sasobjsp_user=self.sasobjsp_user,
                                     sasobjsp_pass=self.sasobjsp_pass)
        if connection:
            self.connected = True
            self.connection = connection
            return self.connection

    def disconnect(self):
        if self.connected:
            self.connection.endsas()
            self.connected = False

    def read_dataset(self, libname, tablename):
        df = self.connection.sasdata2dataframe(table=tablename, libref=libname)
        return df

    def write_dataset(self, df, libname, tablename):
        result = self.connection.dataframe2sasdata(df=df, table=tablename, libref=libname)
        return result

    def show_libs(self):
        libs = self.connection.assigned_librefs()
        return libs
