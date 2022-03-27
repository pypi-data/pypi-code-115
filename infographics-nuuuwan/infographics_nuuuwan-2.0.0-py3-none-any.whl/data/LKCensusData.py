
from infographics.data.GIGData import GIGData

DATA_GROUP = 'census'


class LKCensusData(GIGData):
    def __init__(self, table_id):
        GIGData.__init__(self, DATA_GROUP, table_id)
        self.source_text = 'Data Source: 2012 Census (statistics.gov.lk)'
