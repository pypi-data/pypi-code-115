

from infographics.data.LKCensusData import LKCensusData


class LKCensusEthnicityData(LKCensusData):
    MAJORITY_LIMIT = 0.55
    TABLE_ID = 'ethnicity_of_population'

    def __init__(self):
        LKCensusData.__init__(self, LKCensusEthnicityData.TABLE_ID)

    def get_most_common_ethnicity(self, id):
        d = self[id]
        n_total = d['total_population']
        for color_value, fields in [
            ['sinhalese', ['sinhalese']],
            ['tamil', ['sl_tamil', 'ind_tamil']],
            ['muslim', ['sl_moor', 'malay']],
        ]:
            n = sum([d[field] for field in fields])
            if n > n_total * LKCensusEthnicityData.MAJORITY_LIMIT:
                return color_value
        return 'none'

    @staticmethod
    def get_color_from_color_value(color_value):
        return {
            'sinhalese': 'maroon',
            'tamil': 'orange',
            'muslim': 'green',
            'none': 'cyan',
        }.get(color_value)

    @staticmethod
    def get_label_from_color_value(color_value):
        if color_value == 'none':
            return 'No ethnicity with > ' \
                + f'{LKCensusEthnicityData.MAJORITY_LIMIT:.0%}'
        return color_value.title()
