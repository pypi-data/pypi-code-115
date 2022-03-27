
from infographics.data.GIGData import GIGData

DATA_GROUP = 'elections'


class LKElectionsData(GIGData):
    SOURCE_TEXT = 'Data Source: elections.gov.lk'

    def __init__(self, table_id):
        GIGData.__init__(self, DATA_GROUP, table_id)

    def get_label_from_color_value(self, color_value):
        return color_value.upper()

    def get_color_from_color_value(self, color_value):
        return {
            'SLPP': 'maroon',

            'UNP': 'green',
            'SJB': 'lightgreen',
            'NDF': 'green',

            'SLFP': 'blue',
            'UPFA': 'blue',
            'PA': 'blue',

            'EPDP': 'red',
            'TMVP': 'red',
            'ITAK': 'yellow',
            'ACTC': 'yellow',

            'MNA': 'darkgreen',

            'SLMP': 'purple',

        }.get(color_value, 'gray')
