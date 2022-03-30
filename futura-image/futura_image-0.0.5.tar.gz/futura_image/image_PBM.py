import pandas as pd

from .constants import DEFAULT_REGIONS, DEFAULT_TECHNOLOGIES

class FuturaPBMImageData:
    def __init__(self, filepath, variable_file=None, sheet_index=0):
        self.regions = DEFAULT_REGIONS
        self.technologies = DEFAULT_TECHNOLOGIES
        if variable_file:
            self.get_data_from_variable_file(variable_file)

        self.image_data = pd.read_excel(filepath, sheet_name=sheet_index)
        self.processed_data = self.process_image_data()

    def process_image_data(self):
        raise NotImplementedError('Subclass this to represent different image outputs')

    def get_data_from_variable_file(self, variable_file):
        variables = pd.read_excel(variable_file)

        self.regions = list(variables['Regions'].dropna().values)
        self.technologies = list(variables['Technology'].dropna().values)


class FuturaPBMImageElectricityMix(FuturaPBMImageData):

    def __init__(self, *args, **kwargs):
        super(FuturaPBMImageElectricityMix, self).__init__(*args, **kwargs)

        self.regional_technologies = {k: [i for i in v.sum().index if v.sum()[i]] for k, v in
                                      self.processed_data.items()}
        self.technologies = {item for k, sublist in self.regional_technologies.items() for item in sublist}

    def regional_technologies_for_year(self, year):
        return {k: [i for i in v.loc[year].index if v.loc[year][i]] for k, v in self.processed_data.items()}

    def process_image_data(self):

        elec_prod_dfs = {}

        req_pbm_data = self.image_data[['t', 'NRC2', 'NTC2', 'Value']]

        for name, group in req_pbm_data.groupby('NRC2'):
            elec_prod_dfs[name] = group.pivot(index='t', columns='NTC2', values='Value')

        return elec_prod_dfs

    def get_mixes(self, year):
        df = pd.concat([pd.Series(self.processed_data[region].loc[year], name=region) for region in self.regions[:-1]],
                       axis=1)
        df['World'] = df.sum(axis=1)
        df = df.divide(df.sum(axis=0)).sort_values(by='World', ascending=False).T

        return df