

from infographics.data.LKCensusData import LKCensusData


class LKCensusReligionData(LKCensusData):
    TABLE_ID = 'religious_affiliation_of_population'

    def __init__(self):
        LKCensusData.__init__(self, LKCensusReligionData.TABLE_ID)

    @staticmethod
    def get_color_from_color_value(color_value):
        return {
            'buddhist': 'yellow',
            'hindu': 'orange',
            'islam': 'green',
            'roman_catholic': 'blue',
            'other_christian': 'purple',
        }.get(color_value)
