from futura import w
from futura.loader import FuturaLoader
from futura.utils import create_filter_from_description
from .image_data import FuturaImageElectricityMix
from .mendoza_beltran_utilities import ecoinvent_to_image_locations,\
    get_exchange_amounts,\
    find_average_mix,\
    find_ecoinvent_electricity_datasets_in_same_ecoinvent_location,\
    find_ecoinvent_electricity_datasets_in_image_location,\
    find_ecoinvent_electricity_datasets_in_all_locations

import numpy as np

def pretend_to_add_new_datasets_to_electricity_market(ds, db, df):
    # This function adds new electricity datasets to a market based on image results. We pass not only a dataset to modify, but also a pandas dataframe containing the new electricity mix information, and the db from which we should find the datasets
    # find out which image regions correspond to our dataset:

    image_locations = ecoinvent_to_image_locations(ds['location'])

    # here we find the mix of technologies in the new market and how much they contribute:
    mix = find_average_mix(df.loc[image_locations])  # could be several image locations - we just take the average

    # here we find the datasets that will make up the mix for each technology
    mock_ds = {'name':ds.get('name'),
               'location':ds.get('location'),
               'code': ds.get('code'),
               'exchanges':[]
               }
    datasets = {}
    for i in mix.index:
        if mix[i] != 0:
            # print('Next Technology: ',i)
            # First try to find a dataset that is from that location (or image region for new datasets):
            datasets[i] = find_ecoinvent_electricity_datasets_in_same_ecoinvent_location(i, ds['location'], db)
            # print('First round: ',i, [(ds['name'], ds['location']) for ds in datasets[i]])

            # If this doesn't work, we try to take a dataset from another ecoinvent region within the same image region
            if len(datasets[i]) == 0:
                datasets[i] = find_ecoinvent_electricity_datasets_in_image_location(i, ds['location'], db)
                # print('Second round: ',i, [(ds['name'], ds['location']) for ds in datasets[i]])

            # If even this doesn't work, try taking a global datasets
            if len(datasets[i]) == 0:
                datasets[i] = find_ecoinvent_electricity_datasets_in_same_ecoinvent_location(i, 'GLO', db)
                # print('Third round: ',i, [(ds['name'], ds['location']) for ds in datasets[i]])

            # if no global dataset available, we just take the average of all datasets we have:
            if len(datasets[i]) == 0:
                datasets[i] = find_ecoinvent_electricity_datasets_in_all_locations(i, db)
                # print('Fourth round: ',i, [(ds['name'], ds['location']) for ds in datasets[i]])

            # If we still can't find a dataset, we just take the global market group
            if len(datasets[i]) == 0:
                print('No match found for location: ', ds['location'], ' Technology: ', i,
                      '. Taking global market group for electricity')
                datasets[i] = [x for x in w.get_many(db, *[w.equals('name', 'market group for electricity, high voltage'),
                                                         w.equals('location', 'GLO')])]

    # Now we add the new exchanges:
    for i in mix.index:
        if mix[i] != 0:
            total_amount = mix[i]
            amount = total_amount / len(datasets[i])
            for dataset in datasets[i]:
                mock_ds['exchanges'].append({
                    'amount': amount,
                    'unit': dataset['unit'],
                    'input': (dataset['database'], dataset['code']),
                    'type': 'technosphere',
                    'name': dataset['name'],
                    'location': dataset['location']
                })

    # confirm that exchanges sum to 1!
    sum = np.sum([exc['amount'] for exc in w.technosphere(mock_ds, *[w.equals('unit', 'kilowatt hour'),
                                                              w.doesnt_contain_any('name', [
                                                                  'market for electricity, high voltage'])])])
    if round(sum, 4) != 1.00:  print(ds['location'], " New exchanges don't add to one! something is wrong!", sum)

    return mock_ds

class FuturaImageImporter():
    def __init__(self, loader, filepath, year=None, variable_file=None, auto=True):
        assert isinstance(loader, FuturaLoader), 'A FuturaLoader object is required'

        self.loader = loader

        if not year:
            self.year = 2020

        self.image_loader = FuturaImageElectricityMix(filepath, variable_file)

        self.markets = None
        self.grid_dict = None

        if auto:
            self.markets, self.grid_dict = self.find_markets()

    @property
    def regional_technologies(self):
        return self.image_loader.regional_technologies_for_year(self.year)

    def electricity_filter(self, grid_locations=None, voltage='high'):

        elec_filter_base = [
            {'filter': 'equals', 'args': ['unit', 'kilowatt hour']},
            {'filter': 'startswith', 'args': ['name', 'market for electricity, {} voltage'.format(voltage)]},
            {'filter': 'doesnt_contain_any', 'args': ['name', ['aluminium industry',
                                                               'internal use in coal mining',
                                                               'Swiss Federal Railways',
                                                               'label-certified',
                                                               'electricity, from municipal waste incineration'
                                                               ]]},
        ]

        if grid_locations:
            elec_filter_base += [{'filter': 'either', 'args':
                [{'filter': 'equals', 'args': ['location', x]} for x in grid_locations]
                                  }]

        return create_filter_from_description(elec_filter_base)

    def update_electricity_markets(self, grid_locations=None):
        image_electricity_market_df = self.image_loader.get_mixes(self.year)
        #print(image_electricity_market_df)


        changes = {}
        # update high voltage markets:
        for ds in w.get_many(self.loader.database.db, *self.electricity_filter(grid_locations, voltage='high')):
            print(ds['name'])
            changes[ds['code']] = {}
            changes[ds['code']].update({('meta data', x): ds[x] for x in ['name', 'location']})
            changes[ds['code']].update({('original exchanges', k): v for k, v in get_exchange_amounts(ds).items()})
            changes[ds['code']]['pretend'] = pretend_to_add_new_datasets_to_electricity_market(ds, self.loader.database.db, image_electricity_market_df)
            #changes[ds['code']].update({('updated exchanges', k): v for k, v in get_exchange_amounts(ds).items()})
        return changes



    ### Possibly don't need this

    def find_markets(self, grid_locations=None, voltage='high'):

        elec_filter_base = [
            {'filter': 'equals', 'args': ['unit', 'kilowatt hour']},
            {'filter': 'startswith', 'args': ['name', 'market for electricity, {} voltage'.format(voltage)]},
            {'filter': 'doesnt_contain_any', 'args': ['name', ['aluminium industry',
                                                               'internal use in coal mining',
                                                               'Swiss Federal Railways',
                                                               'label-certified',
                                                               'electricity, from municipal waste incineration'
                                                               ]]},
        ]

        if grid_locations:
            elec_filter_base += [{'filter': 'either', 'args':
                [{'filter': 'equals', 'args': ['location', x]} for x in grid_locations]
                                  }]

        elec_filter = create_filter_from_description(elec_filter_base)

        elec_list = list(w.get_many(self.loader.database.db, *elec_filter))

        grid_dict = {
            e['location']: ecoinvent_to_image_locations(e['location'])[0]
            for e in elec_list if 'IAI' not in e['location']
                                  and e['location'] not in ['GLO']
                                  and len(ecoinvent_to_image_locations(e['location'])) == 1
        }

        return elec_list, grid_dict
