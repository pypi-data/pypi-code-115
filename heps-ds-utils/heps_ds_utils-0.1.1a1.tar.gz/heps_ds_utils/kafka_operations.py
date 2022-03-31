# To be defined later !


class KafkaOperations:
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
