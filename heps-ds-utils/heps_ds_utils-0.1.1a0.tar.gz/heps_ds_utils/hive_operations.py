""" This Module is created to enable Hepsiburada Data Science to communicate with Hive """

from pyhive import hive
import pandas as pd
import numpy as np

class HiveOperations:
    """ This class is created to enable Hepsiburada Data Science to communicate with Hive """

    @staticmethod
    def connect_to_hive(host, port, username, password):
        """
        This function is used to connect to Hive Server 2 and return the connection object.
        :param host: Hive Server 2 host
        :param port: Hive Server 2 port
        :param username: Hive Server 2 username
        :param password: Hive Server 2 password
        :return: Hive Server 2 connection object
        """
        hive_connection = hive.connect(host=host, port=port,
                                username=username, password=password, auth='LDAP')
        return hive_connection

    @staticmethod
    def disconnect_from_hive(hive_connection):
        """
        This function is used to disconnect from Hive Server 2.
        :param hive_connection: Hive Server 2 connection object
        :return: None
        """
        hive_connection.close()

    @staticmethod
    def execute_query(hive_connection, query, return_type='dataframe', **kwargs):
        """
        This function is used to execute the query and return data in different types.
        :param hive_connection: Hive Server 2 connection object
        :param query: Hive query
        :param return_type: Type of return data
        :param kwargs return_colums: Return Columns for numpy array and list types.
        :return: Data frame
        """
        cursor = hive_connection.cursor()
        cursor.execute(query)
        columns = HiveOperations._rename_columns(cursor)

        if return_type == 'dataframe':
            cursor.close()
            return pd.DataFrame(cursor.fetchall(), columns=columns), None
        elif return_type == 'numpy':
            if kwargs['return_columns']:
                cursor.close()
                return np.array(cursor.fetchall()), columns
            cursor.close()
            return np.array(cursor.fetchall()), None
        elif return_type == 'list':
            if kwargs['return_columns']:
                cursor.close()
                return cursor.fetchall(), columns
            cursor.close()
            return cursor.fetchall(), None
        elif return_type == 'dict':
            cursor.close()
            return [dict(zip(columns, row)) for row in cursor.fecthall()], None
        else:
            raise NotImplementedError('Return type not implemented')

    @staticmethod
    def create_insert_table(hive_connection, query):
        """
        This function is used to create the table and insert data into the table.
        :param query: Hive query
        :param hive_connection: Hive Server 2 connection object
        :return: None
        """

        cursor = hive_connection.cursor()
        cursor.execute(query)
        cursor.close()
        return None

    @staticmethod
    def _rename_columns(cursor) -> list:
        """
        This function takes cursor description and rename the columns of the data frame.
        :param column_names: Column names
        :return: List of column names
        """
        columns = [column[0].split('.')[-1] for column in cursor.description]
        return columns

    @staticmethod
    def _parse_sql_query(query):
        """
        This function is used to parse the sql query and return the query with the table name.
        :param query: Hive query
        :return: Hive query with table name
        """

        ## TO BE WRITTEN !!

        query_list = query.split(' ')
        table_name = query_list[2]
        return table_name

    @staticmethod
    def _execute_sql_from_file(query_file, hive_connection):
        """
        This function is used to execute the sql query from file and return the data frame.
        :param query_file: Hive query file
        :param hive_connection: Hive Server 2 connection object
        :return: Data frame
        """

        ## TO BE WRITTEN !!

        with open(query_file, 'r', encoding='utf-8') as hiveql_file:
            query = hiveql_file.read()
        return HiveOperations.execute_query(hive_connection, query)
