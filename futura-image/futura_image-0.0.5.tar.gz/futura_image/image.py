from .image_data import FuturaImageElectricityMix
from futura import w
from futura.loader import FuturaLoader
from futura.utils import create_filter_from_description
from futura.markets import FuturaMarket

from wurst import geomatcher

from collections import OrderedDict, defaultdict
from tqdm import tqdm


def get_loc(loc):
    if loc == 'RoW':
        return ['World']
    loc_list = [x[1] for x in geomatcher.intersects(loc) if x[0] == 'IMAGE']
    # if len(loc_list)>1:
    # print('{} has more than one match {}'.format(loc, loc_list))
    return loc_list


def check_exchange_in_activity(base_activity, activity_to_link_to):
    exchange_template = {'uncertainty type': 0,
                         'loc': 0,
                         'amount': 0,
                         'type': 'technosphere',
                         'production volume': 0,
                         'product': '',
                         'name': '',
                         'unit': '',
                         'location': ''}

    rp = w.reference_product(activity_to_link_to)
    key_list = ['production volume', 'product', 'name', 'unit', 'location']
    for k in key_list:
        exchange_template[k] = rp[k]

    if exchange_template not in base_activity['exchanges']:
        return exchange_template
    else:
        return False


def find_possible_additional_electricity_exchanges(process, database, include_transmission=False, include_glo=False):
    assert isinstance(database, FuturaDatabase), "database needs to be a futura FuturaDatabase object"
    assert process['name'].startswith('market') and not process['name'].startswith('market group'), \
        'This function only works with market processes (not market groups or production processes)'

    technosphere_exchanges = [e for e in w.technosphere(process)]

    result = []
    # result_dict = {}

    for g, v in groupby(technosphere_exchanges, lambda x: (x['product'],
                                                           x['location'],
                                                           x['unit'])):
        # print(g)
        v_list = list(v)
        names = [e['name'] for e in v_list if e['name'] != process['name']]

        possible_additions_filter = []
        possible_additions_filter += [w.equals('unit', g[2])]
        possible_additions_filter += [w.equals('reference product', g[0])]
        possible_additions_filter += [exclude(w.startswith('name', 'market'))]
        possible_additions_filter += [exclude(w.equals('location', 'RoW'))]
        possible_additions_filter += [w.doesnt_contain_any('name', ['production mix',
                                                                    'pulp',
                                                                    'ethanol',
                                                                    'petroleum refinery',
                                                                    'blast furnace',
                                                                    'coal gas',
                                                                    'bagasse',
                                                                    'aluminium industry'
                                                                    ])]

        possible_additions_filter += [w.doesnt_contain_any('name', names)]

        if not include_transmission:
            possible_additions_filter += [w.doesnt_contain_any('name', ['transport', 'transmission'])]

        if include_glo:
            possible_additions_filter += [w.either(*[w.equals('location', g[1]), w.equals('location', 'GLO')])]
        else:
            possible_additions_filter += [w.equals('location', g[1])]

        possibles = list(w.get_many(database.db, *possible_additions_filter))

        if len(possibles) > 0:
            for p in possibles:
                e = check_exchange_in_activity(process, p)
                if e:
                    result.append(e)
            # result.extend(possibles)
            # result_dict[g] = possibles

    return result  # , result_dict


class OriginalFuturaImageImporter():
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

        self.df = None
        self.aggregated_data = None
        self.formatted_data = None
        # self.all_locations = self.image_loader.regions

    def find_markets(self, grid_locations=None):

        elec_filter_base = [
            {'filter': 'equals', 'args': ['unit', 'kilowatt hour']},
            {'filter': 'startswith', 'args': ['name', 'market for electricity, high voltage']},
            {'filter': 'doesnt_contain_any', 'args': ['name', ['Swiss Federal Railways', 'label-certified']]},
        ]

        if grid_locations:
            elec_filter_base += [{'filter': 'either', 'args':
                [{'filter': 'equals', 'args': ['location', x]} for x in grid_locations]
                                  }]

        elec_filter = create_filter_from_description(elec_filter_base)

        elec_list = list(w.get_many(self.loader.database.db, *elec_filter))

        grid_dict = {
            e['location']: get_loc(e['location'])[0]
            for e in elec_list if 'IAI' not in e['location']
                                  and e['location'] not in ['GLO']
                                  and len(get_loc(e['location'])) == 1
        }

        return elec_list, grid_dict

    @staticmethod
    def classify_by_name(name):

        convert_dict = OrderedDict()
        convert_dict["import"] = "Imports"
        convert_dict.update(
            {
                'coal, post': 'Coal CCS',
                'coal, oxy': 'Coal CCS',
                'coal, pre': 'Coal CCS',
                'lignite, post': 'Coal CCS',
                'lignite, pre': 'Coal CCS',
                'lignite, oxy': 'Coal CCS',
                'gas, post': 'Natural gas CCS',
                'gas, pre': 'Natural gas CCS',
                'gas, oxy': 'Natural gas CCS',
                'wood burning power plant 20 MW, truck 25km, post': 'Biomass CCS',

                'co-generation, biogas': 'Biomass CHP',
                'co-generation, wood': 'Biomass CHP',
                'biogas': 'Biomass ST',
                'biogas': 'Biomass ST',
                'wood': 'Biomass ST',
                'co-generation, hard coal': 'Coal CHP',
                'co-generation, lignite': 'Coal CHP',
                'hard coal': 'Coal ST',
                'lignite': 'Coal ST',
                'hydro': 'Hydro',
                'co-generation, natural gas': 'Natural gas CHP',
                'natural gas, combined cycle': 'Natural gas CC',
                'natural gas': 'Natural gas OC',
                'nuclear': 'Nuclear',
                'co-generation, oil': 'Oil CHP',
                'oil': 'Oil ST',
                'solar': 'Solar PV',
                'offshore': 'Wind offshore',
                'onshore': 'Wind onshore',
                'peat': 'Other',
                'blast furnace gas': 'Other',
                'geothermal': 'Other',
                'coal': 'Coal ST',
                'diesel': 'Other',
                'digester sludge': 'Other',

                'CC plant': 'Other',
                'BIGCC': 'IGCC',
            }
        )

        for n in convert_dict.keys():
            if n in name:
                return convert_dict[n]
                break

        return 'Non-Specified'

    def classify_technologies(self, elec_list=None):

        if not elec_list:
            elec_list = self.markets

        assert elec_list

        exchange_filter = [{'filter': 'equals', 'args': ['unit', 'kilowatt hour']},
                           {'filter': 'exclude', 'args': [
                               {'filter': 'startswith', 'args': ['name', 'market ']},
                           ]},
                           ]
        wurst_exchange_filter = create_filter_from_description(exchange_filter)

        exchange_dict = defaultdict(list)

        for x in elec_list:
            exc_list = list(w.get_many(x['exchanges'], *wurst_exchange_filter))

            for e in exc_list:
                e['image_location'] = get_loc(x['location'])[0]
                e['image_classification'] = classify_by_name(e['name'])

            assert not exchange_dict[x['location']]

            exchange_dict[x['location']] = exc_list

        return exchange_dict

    def add_additional_suppliers(self, include_glo=False):

        count = 0

        assert self.markets, "Can't check for suppliers without finding markets"

        for m in tqdm(self.markets):
            possibles = find_possible_additional_electricity_exchanges(m, i.loader.database, include_glo=include_glo)

            # print("{} [{}]\n".format(m['name'], m['location']))
            # print(possibles)
            m['exchanges'].extend(possibles)
            count += len(possibles)

        print("Added {} exchanges to {} markets".format(count, len(self.markets)))

    def classify_exchanges(self, elec_list=None):

        if not elec_list:
            elec_list = self.markets

        assert elec_list

        exchange_filter = [{'filter': 'equals', 'args': ['unit', 'kilowatt hour']},
                           {'filter': 'exclude', 'args': [
                               {'filter': 'startswith', 'args': ['name', 'market ']},
                           ]},
                           ]
        wurst_exchange_filter = create_filter_from_description(exchange_filter)

        full_exchange_list = []

        for x in elec_list:
            full_exchange_list.extend(list(w.get_many(x['exchanges'], *wurst_exchange_filter)))

        exchange_tuples = {(x['name'], x['location']) for x in full_exchange_list}

        # return exchange_names

        # assert 0

        convert_dict = OrderedDict()
        convert_dict["import"] = "Imports"
        convert_dict.update(
            {
                'coal, post': 'Coal CCS',
                'coal, oxy': 'Coal CCS',
                'coal, pre': 'Coal CCS',
                'lignite, post': 'Coal CCS',
                'lignite, pre': 'Coal CCS',
                'lignite, oxy': 'Coal CCS',
                'gas, post': 'Natural gas CCS',
                'gas, pre': 'Natural gas CCS',
                'gas, oxy': 'Natural gas CCS',
                'wood burning power plant 20 MW, truck 25km, post': 'Biomass CCS',

                'co-generation, biogas': 'Biomass CHP',
                'co-generation, wood': 'Biomass CHP',
                'biogas': 'Biomass ST',
                'biogas': 'Biomass ST',
                'wood': 'Biomass ST',
                'co-generation, hard coal': 'Coal CHP',
                'co-generation, lignite': 'Coal CHP',
                'hard coal': 'Coal ST',
                'lignite': 'Coal ST',
                'hydro': 'Hydro',
                'co-generation, natural gas': 'Natural gas CHP',
                'natural gas, combined cycle': 'Natural gas CC',
                'natural gas': 'Natural gas OC',
                'nuclear': 'Nuclear',
                'co-generation, oil': 'Oil CHP',
                'oil': 'Oil ST',
                'solar': 'Solar PV',
                'offshore': 'Wind offshore',
                'onshore': 'Wind onshore',
                'peat': 'Other',
                'blast furnace gas': 'Other',
                'geothermal': 'Other',
                'coal': 'Coal ST',
                'diesel': 'Other',
                'digester sludge': 'Other',

                'CC plant': 'Other',
                'BIGCC': 'IGCC',
            }
        )

        # translate all exchanges to their IMAGE equivalents

        exchange_dict = {}
        for e in exchange_tuples:
            found = False
            for n in convert_dict.keys():
                if n in e[0]:
                    exchange_dict[e] = convert_dict[n]
                    found = True
                    break

            if not found:
                exchange_dict[e] = 'Non-Specified'

        return exchange_dict

    def update_grid(self, year=None, grid_locations=None):

        # if not grid_locations:
        #    grid_locations = self.all_locations

        if isinstance(grid_locations, str):
            grid_locations = [grid_locations]

        # assert isinstance(grid_locations, list)

        if not year:
            year = self.year

        # get electricity market(s)

        if not self.markets:
            elec_list, grid_dict = self.find_markets(grid_locations)
        elif grid_locations:
            elec_list, grid_dict = self.find_markets(grid_locations)
        else:
            elec_list = self.markets
            grid_dict = self.grid_dict

        pprint(grid_dict)

        # get exchanges to categorise

        exchange_dict = self.classify_exchanges(elec_list)

        # return exchange_dict
        stratification_dicts = {}

        last_fm = None

        df = self.image_loader.get_mixes(year)
        # print(year)
        # print(df.loc['Western Europe'])

        # pprint([m['location'] for m in elec_list])

        for market in tqdm(elec_list):

            if market['location'] in grid_dict.keys():
                # print(market['location'])

                # stratification_dict = self.aggregated_data.xs(market['location'][:2]).to_dict()['Latest Year Total']
                stratification_dict = df.stack().xs([grid_dict[market['location']]][:2]).to_dict()
                fm = FuturaMarket(market, self.loader.database)

                # create a dataframe of market production volumes by exchange
                pv_df = pd.DataFrame(
                    [{'input': k, 'production volume': v['production volume']} for k, v in fm.process_dict.items()])

                # add a Group column to classify each exchange to an IEA type
                pv_df['Group'] = pv_df['input'].apply(lambda x: exchange_dict.get(x, None))

                grand_total = pv_df['production volume'].sum()

                # figure out how to stratify the data based on the proportion of production within IEA groups
                stratification_data = {}

                for g, v in pv_df.groupby('Group'):
                    this_total = v['production volume'].sum()
                    stratification_data[g] = {}

                    # print(v)
                    for row_index, row in v.iterrows():
                        if this_total != 0:
                            stratification_data[g][row['input']] = row['production volume'] / this_total
                        else:
                            stratification_data[g][row['input']] = 0

                print(stratification_data)

                # multiply these proportions by the actual new grid mix sections
                actual_stratification = {k: v * grand_total for k, v in stratification_dict.items()}

                final_dict = {}

                for k, v in stratification_data.items():
                    if k not in ['Imports', 'Other']:
                        this_pv = actual_stratification[k]
                        for x, n in v.items():
                            final_dict[x] = n * this_pv

                stratification_dicts[market['location']] = final_dict

        return stratification_dicts

        # apply the new numbers to the FuturaMarket

        # for k, v in final_dict.items():
        #    fm.set_pv(k, v)

        # fm.relink()

        # print('Updated grid mix for {}'.format(cc.convert(market['location'], to="short_name")))


def main():
    pass
