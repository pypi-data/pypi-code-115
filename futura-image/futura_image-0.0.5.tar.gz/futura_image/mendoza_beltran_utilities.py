#!/usr/bin/env python
from wurst import *
from wurst.searching import *

from wurst.transformations.activity import change_exchanges_by_constant_factor
from wurst.transformations.uncertainty import rescale_exchange

from wurst.IMAGE.io import *
from wurst.IMAGE import *

from wurst.ecoinvent.electricity_markets import *
from wurst.ecoinvent.filters import *

from wurst.transformations.geo import *

import pandas as pd
from pprint import pprint

import os

dir_path = os.path.dirname(os.path.realpath(__file__))
image_filename = os.path.join(dir_path, 'assets/Image variable names.xlsx')

image_variable_names = pd.read_excel(image_filename)
REGIONS = image_variable_names['Regions'].dropna().values


scenarios = {'BAU': {}, '450': {}}
scenarios['BAU']['filepath'] = r'SSPs_data/SSPs/SSP2'
scenarios['BAU']['description'] = "Middle of the Road (Medium challenges to mitigation and adaptation)"
scenarios['450']['filepath'] = r'SSPs_data/SSPs/SSP2_450'
scenarios['450']['description'] = "Middle of the Road (Medium challenges to mitigation and adaptation), 4.5W.m-2 target"
#
# <p>We import some datasets from simapro. These functions clean up the datasets:</p>
#

def fix_unset_technosphere_and_production_exchange_locations(db, matching_fields=('name', 'unit')):
    for ds in db:
        for exc in ds['exchanges']:
            if exc['type'] == 'production' and exc.get('location') is None:
                exc['location'] = ds['location']
            elif exc['type'] == 'technosphere' and exc.get('location') is None:
                locs = find_location_given_lookup_dict(db,
                                                       {k: exc.get(k) for k in matching_fields})
                if len(locs) == 1:
                    exc['location'] = locs[0]
                else:
                    print("No unique location found for exchange:\n{}\nFound: {}".format(
                        pprint.pformat(exc), locs
                    ))


def find_location_given_lookup_dict(db, lookup_dict):
    return [x['location'] for x in get_many(db, *[equals(k, v) for k, v in lookup_dict.items()])]

exists = lambda x: {k: v for k, v in x.items() if v is not None}

def remove_nones(db):
    for ds in db:
        ds['exchanges'] = [exists(exc) for exc in ds['exchanges']]


def set_global_location_for_additional_datasets(db):
    """ This function is needed because the wurst function relink_technosphere exchanges needs global datasets if if can't find a regional one."""
    non_ecoinvent_datasets = [x['name'] for x in input_db if x['database'] != 'ecoinvent']
    ecoinvent_datasets = [x['name'] for x in input_db if x['database'] == 'ecoinvent']

    for ds in [x for x in db if x['database'] in ['Carma CCS', 'CSP']]:
        ds['location'] = 'GLO'
        for exc in [x for x in ds['exchanges'] if x['type'] != 'biosphere']:
            if exc['name'] in non_ecoinvent_datasets:
                if exc['name'] in ecoinvent_datasets and exc['location'] != 'GLO':
                    print(exc['name'], exc['location'])
                else:
                    exc['location'] = 'GLO'


def add_new_locations_to_added_datasets(db):
    # We create a new version of all added electricity generation datasets for each IMAGE region.
    # We allow the upstream production to remain global, as we are mostly interested in regionalizing
    # to take advantage of the regionalized IMAGE data.

    # step 1: make copies of all datasets for new locations
    # best would be to regionalize datasets for every location with an electricity market like this:
    # locations = {x['location'] for x in get_many(db, *electricity_market_filter_high_voltage)}

    # but this takes quite a long time. For now, we just use 1 location that is uniquely in each IMAGE region.
    possibles = {}
    for reg in REGIONS[:-1]:
        temp = [x for x in geomatcher.intersects(('IMAGE', reg)) if type(x) != tuple]
        possibles[reg] = [x for x in temp if len(ecoinvent_to_image_locations(x)) == 1]
        if not len(possibles[reg]): print(reg, ' has no good candidate')
    locations = [v[0] for v in possibles.values()]

    # This code would modify every new dataset, but this would be quite large:
    # for ds in  pyprind.prog_bar([ds for ds in db if ds['database'] in ['CSP','Carma CCS']]):
    # so we consider only the final electricity production dataset and not the upstream impacts:
    for ds in pyprind.prog_bar([ds for ds in db if ds['name'] in carma_electricity_ds_name_dict.keys()]):
        for location in locations:
            new_ds = copy_to_new_location(ds, location)
            db.append(new_ds)


def regionalize_added_datasets(db):
    # step 2: relink all processes in each dataset
    # This code would modify every new dataset, but this would be quite large:
    # for ds in  pyprind.prog_bar([ds for ds in db if ds['database'] in ['CSP','Carma CCS']]):
    # so we consider only the final electricity production dataset and not the upstream impacts:
    for ds in [ds for ds in db if ds['name'] in carma_electricity_ds_name_dict.keys()]:
        ds = relink_technosphere_exchanges(ds, db, exclusive=True, drop_invalid=False, biggest_first=False,
                                           contained=False)


#
# <h1 id="Modify-electricity-datasets">Modify electricity datasets<a class="anchor-link" href="#Modify-electricity-datasets">¶</a></h1>
#

# In[12]:


def update_ecoinvent_efficiency_parameter(ds, scaling_factor):
    parameters = ds['parameters']
    possibles = ['efficiency', 'efficiency_oil_country', 'efficiency_electrical']

    for key in possibles:
        try:
            parameters[key] /= scaling_factor
            return
        except KeyError:
            pass


# In[13]:


def find_coal_efficiency_scaling_factor(ds, year, image_efficiency, agg_func=np.average):
    # Input a coal electricity dataset and year. We look up the efficiency for this region and year
    # from the Image model and return the scaling factor by which to multiply all efficiency dependent exchanges.
    # If the ecoinvent region corresponds to multiple Image regions we simply average them.
    ecoinvent_eff = find_ecoinvent_coal_efficiency(ds)
    image_locations = ecoinvent_to_image_locations(ds['location'])
    image_eff = agg_func(
        image_efficiency.loc[year][image_locations].values)  # we take an average of all applicable image locations
    return ecoinvent_eff / image_eff


# In[14]:


def find_gas_efficiency_scaling_factor(ds, year, image_efficiency, agg_func=np.average):
    # Input a gas electricity dataset and year. We look up the efficiency for this region and year
    # from the Image model and return the scaling factor by which to multiply all efficiency dependent exchanges.
    # If the ecoinvent region corresponds to multiple Image regions we simply average them.
    ecoinvent_eff = find_ecoinvent_gas_efficiency(ds)
    image_locations = ecoinvent_to_image_locations(ds['location'])
    image_eff = agg_func(
        image_efficiency.loc[year][image_locations].values)  # we take an average of all applicable image locations
    return ecoinvent_eff / image_eff


# In[15]:


def find_oil_efficiency_scaling_factor(ds, year, image_efficiency, agg_func=np.average):
    # Input a oil electricity dataset and year. We look up the efficiency for this region and year
    # from the Image model and return the scaling factor by which to multiply all efficiency dependent exchanges.
    # If the ecoinvent region corresponds to multiple Image regions we simply average them.
    ecoinvent_eff = find_ecoinvent_oil_efficiency(ds)
    image_locations = ecoinvent_to_image_locations(ds['location'])
    image_eff = agg_func(
        image_efficiency.loc[year][image_locations].values)  # we take an average of all applicable image locations
    return ecoinvent_eff / image_eff


# In[16]:


def find_biomass_efficiency_scaling_factor(ds, year, image_efficiency, agg_func=np.average):
    # Input an electricity dataset and year. We look up the efficiency for this region and year
    # from the Image model and return the scaling factor by which to multiply all efficiency dependent exchanges.
    # If the ecoinvent region corresponds to multiple Image regions we simply average them.
    ecoinvent_eff = find_ecoinvent_biomass_efficiency(ds)
    image_locations = ecoinvent_to_image_locations(ds['location'])
    image_eff = agg_func(
        image_efficiency.loc[year][image_locations].values)  # we take an average of all applicable image locations
    return ecoinvent_eff / image_eff


# In[17]:


def find_nuclear_efficiency_scaling_factor(ds, year, image_efficiency, agg_func=np.average):
    # Input an electricity dataset and year. We look up the efficiency for this region and year
    # from the Image model and return the scaling factor compared to the improvement since 2012.
    # We do not consider the ecoinvent efficiency in 2012 as it is rather difficult to calculate and
    # the burnup is not available.
    # This is a simplification and certainly has it's weaknesses,
    # however we argue that it's better than not chaning the datasets at all.
    # If the ecoinvent region corresponds to multiple Image regions we simply average them.
    image_locations = ecoinvent_to_image_locations(ds['location'])
    image_uranium_efficiency = agg_func(
        image_efficiency.loc[year][image_locations].values)  # we take an average of all applicable image locations
    image_uranium_efficiency_2012 = agg_func(image_efficiency.loc[2012][image_locations].values)
    return image_uranium_efficiency_2012 / image_uranium_efficiency


# In[18]:


def find_ecoinvent_coal_efficiency(ds):
    # Nearly all coal power plant datasets have the efficiency as a parameter.
    # If this isn't available, we back calculate it using the amount of coal used and
    # an average energy content of coal.
    try:
        return ds['parameters']['efficiency']
    except KeyError:
        pass

    # print('Efficiency parameter not found - calculating generic coal efficiency factor', ds['name'], ds['location'])

    fuel_sources = technosphere(ds,
                                either(contains('name', 'hard coal'), contains('name', 'lignite')),
                                doesnt_contain_any('name', ('ash', 'SOx')),
                                equals('unit', 'kilogram'))
    energy_in = 0
    for exc in fuel_sources:
        if 'hard coal' in exc['name']:
            energy_density = 20.1 / 3.6  # kWh/kg
        elif 'lignite' in exc['name']:
            energy_density = 9.9 / 3.6  # kWh/kg
        else:
            raise ValueError("Shouldn't happen because of filters!!!")
        energy_in += (exc['amount'] * energy_density)
    ds['parameters']['efficiency'] = reference_product(ds)['amount'] / energy_in
    # print(ds['parameters']['efficiency'])
    return reference_product(ds)['amount'] / energy_in


# In[19]:


def find_ecoinvent_gas_efficiency(ds):
    # Nearly all gas power plant datasets have the efficiency as a parameter.
    # If this isn't available, we back calculate it using the amount of gas used and an average energy content of gas.
    try:
        return ds['parameters']['efficiency']
    except KeyError:
        pass

    # print('Efficiency parameter not found - calculating generic gas efficiency factor', ds['name'], ds['location'])

    fuel_sources = technosphere(ds,
                                either(contains('name', 'natural gas, low pressure'),
                                       contains('name', 'natural gas, high pressure')),
                                equals('unit', 'cubic meter'))
    energy_in = 0
    for exc in fuel_sources:
        # (based on energy density of natural gas input for global dataset
        # 'electricity production, natural gas, conventional power plant')
        if 'natural gas, high pressure' in exc['name']:
            energy_density = 39 / 3.6  # kWh/m3

        # (based on average energy density of high pressure gas, scaled by the mass difference listed between
        # high pressure and low pressure gas in the dataset:
        # natural gas pressure reduction from high to low pressure, RoW)
        elif 'natural gas, low pressure' in exc['name']:
            energy_density = 39 * 0.84 / 3.6  # kWh/m3
        else:
            raise ValueError("Shouldn't happen because of filters!!!")
        energy_in += (exc['amount'] * energy_density)
    ds['parameters']['efficiency'] = reference_product(ds)['amount'] / energy_in
    # print(ds['parameters']['efficiency'])
    return reference_product(ds)['amount'] / energy_in


# In[20]:


def find_ecoinvent_oil_efficiency(ds):
    # Nearly all oil power plant datasets have the efficiency as a parameter.
    # If this isn't available, we use global average values to calculate it.
    try:
        return ds['parameters']['efficiency_oil_country']
    except KeyError:
        pass
    # print('Efficiency parameter not found - calculating generic oil efficiency factor', ds['name'], ds['location'])
    fuel_sources = [x for x in technosphere(ds, *[contains('name', 'heavy fuel oil'),
                                                  equals('unit', 'kilogram')]
                                            )]
    energy_in = 0
    for exc in fuel_sources:
        # (based on energy density of heavy oil input and efficiency parameter for dataset
        # 'electricity production, oil, RoW')
        energy_density = 38.5 / 3.6  # kWh/m3
        energy_in += (exc['amount'] * energy_density)
    ds['parameters']['efficiency'] = reference_product(ds)['amount'] / energy_in
    # print(ds['parameters']['efficiency'])
    return reference_product(ds)['amount'] / energy_in


# In[21]:


def find_ecoinvent_biomass_efficiency(ds):
    # Nearly all power plant datasets have the efficiency as a parameter. If this isn't available, we excl.
    try:
        return ds['parameters']['efficiency_electrical']
    except:
        pass

    if ds['name'] == 'heat and power co-generation, biogas, gas engine, label-certified':
        ds['parameters'] = {'efficiency_electrical': 0.32}
        return ds['parameters']['efficiency_electrical']  # in general comments for dataset

    elif ds['name'] == 'wood pellets, burned in stirling heat and power co-generation unit, 3kW electrical, future':
        ds['parameters'] = {'efficiency_electrical': 0.23}
        return ds['parameters']['efficiency_electrical']  # in comments for dataset

    print(ds['name'], ds['location'], ' Efficiency not found!')
    return 0


# In[22]:


def get_exchange_amounts(ds, technosphere_filters=None, biosphere_filters=None):
    result = {}
    for exc in technosphere(ds, *(technosphere_filters or [])):
        result[(exc['name'], exc['location'])] = exc['amount']
    for exc in biosphere(ds, *(biosphere_filters or [])):
        result[(exc['name'], exc.get('categories'))] = exc['amount']
    return result


# In[23]:


retained_filter = doesnt_contain_any('name', (
    'market for NOx retained',
    'market for SOx retained'
))

image_air_pollutants = {
    'Methane, fossil': 'CH4',
    'Sulfur dioxide': 'SO2',
    'Carbon monoxide, fossil': 'CO',
    'Nitrogen oxides': 'NOx',
    'Dinitrogen monoxide': 'N2O'
}

no_al = [exclude(contains('name', 'aluminium industry'))]
no_ccs = [exclude(contains('name', 'carbon capture and storage'))]
no_markets = [exclude(contains('name', 'market'))]
no_imports = [exclude(contains('name', 'import'))]
generic_excludes = no_al + no_ccs + no_markets

image_mapping = {
    'Coal ST': {
        'fuel2': 'Coal',
        'eff_func': find_coal_efficiency_scaling_factor,
        'technology filters': coal_electricity + generic_excludes,
        'technosphere excludes': [retained_filter],
    },
    'Coal CHP': {
        'fuel2': 'Coal',
        'eff_func': find_coal_efficiency_scaling_factor,
        'technology filters': coal_chp_electricity + generic_excludes,
        'technosphere excludes': [retained_filter],
    },
    'Natural gas OC': {
        'fuel2': 'Natural gas',
        'eff_func': find_gas_efficiency_scaling_factor,
        'technology filters': gas_open_cycle_electricity + generic_excludes + no_imports,
        'technosphere excludes': [],
    },
    'Natural gas CC': {
        'fuel2': 'Natural gas',
        'eff_func': find_gas_efficiency_scaling_factor,
        'technology filters': gas_combined_cycle_electricity + generic_excludes + no_imports,
        'technosphere excludes': [],
    },
    'Natural gas CHP': {
        'fuel2': 'Natural gas',
        'eff_func': find_gas_efficiency_scaling_factor,
        'technology filters': gas_chp_electricity + generic_excludes + no_imports,
        'technosphere excludes': [],
    },
    'Oil ST': {
        'fuel2': 'Heavy liquid fuel',
        'eff_func': find_oil_efficiency_scaling_factor,
        'technology filters': oil_open_cycle_electricity + generic_excludes + [exclude(contains('name', 'nuclear'))],
        'technosphere excludes': [],
    },
    'Oil CC': {
        'fuel2': 'Heavy liquid fuel',
        'eff_func': find_oil_efficiency_scaling_factor,
        'technology filters': oil_combined_cycle_electricity + generic_excludes + [
            exclude(contains('name', 'nuclear'))],
        'technosphere excludes': [],
    },
    'Oil CHP': {
        'fuel2': 'Heavy liquid fuel',
        'eff_func': find_oil_efficiency_scaling_factor,
        'technology filters': oil_chp_electricity + generic_excludes + [exclude(contains('name', 'nuclear'))],
        'technosphere excludes': [],
    },
    'Biomass ST': {
        'fuel2': 'Biomass',
        'eff_func': find_biomass_efficiency_scaling_factor,
        'technology filters': biomass_electricity + generic_excludes,
        'technosphere excludes': [],
    },
    'Biomass CHP': {
        'fuel2': 'Biomass',
        'eff_func': find_biomass_efficiency_scaling_factor,
        'technology filters': biomass_chp_electricity + generic_excludes,
        'technosphere excludes': [],
    },
    'Biomass CC': {
        'fuel2': 'Biomass',
        'eff_func': find_biomass_efficiency_scaling_factor,
        'technology filters': biomass_combined_cycle_electricity + generic_excludes,
        'technosphere excludes': [],
    },
    'Nuclear': {
        'fuel2': None,  # image parameter doesn't exist for nuclear
        'eff_func': find_nuclear_efficiency_scaling_factor,
        'technology filters': nuclear_electricity + generic_excludes,
        'technosphere excludes': [],
    },
}


def update_electricity_datasets_with_image_data(db, year, scenario, agg_func=np.average, update_efficiency=True,
                                                update_emissions=True):
    """
    #for the moment we assume that particulates reduce according to the efficiency as we don't have any better data.

    """
    changes = {}

    for image_technology in image_mapping:
        print('Changing ', image_technology)
        md = image_mapping[image_technology]
        image_efficiency = get_image_efficiencies(scenario, image_technology)
        if image_technology != 'Nuclear':
            image_emissions = get_image_electricity_emission_factors(scenario, image_efficiency, fuel2=md.get('fuel2'))

        for ds in get_many(db, *md['technology filters']):

            changes[ds['code']] = {}
            changes[ds['code']].update({('meta data', x): ds[x] for x in ['name', 'location']})
            changes[ds['code']].update({('meta data', 'Image technology'): image_technology})
            changes[ds['code']].update({('original exchanges', k): v for k, v in get_exchange_amounts(ds).items()})
            if update_efficiency == True:
                # Modify using IMAGE efficiency values:
                scaling_factor = md['eff_func'](ds, year, image_efficiency, agg_func)
                update_ecoinvent_efficiency_parameter(ds, scaling_factor)
                change_exchanges_by_constant_factor(ds, scaling_factor, md['technosphere excludes'],
                                                    [doesnt_contain_any('name', image_air_pollutants)])

            if image_technology != 'Nuclear':  # We don't update emissions for nuclear

                if update_emissions == True:
                    # Modify using IMAGE specific emissions data
                    for exc in biosphere(ds, either(*[contains('name', x) for x in image_air_pollutants])):
                        image_locations = (ds['location'])
                        flow = image_air_pollutants[exc['name']]
                        amount = agg_func(image_emissions[flow].loc[year][image_locations].values)

                        # if new amount isn't a number:
                        if np.isnan(amount):
                            print('Not a number! Setting exchange to zero' + ds['name'], exc['name'], ds['location'])
                            rescale_exchange(exc, 0)

                            # if old amound was zero:
                        elif exc['amount'] == 0:
                            exc['amount'] = 1
                            rescale_exchange(exc, amount / exc['amount'], remove_uncertainty=True)

                        else:
                            rescale_exchange(exc, amount / exc['amount'])

            changes[ds['code']].update({('updated exchanges', k): v for k, v in get_exchange_amounts(ds).items()})
    return changes


#
# <h2 id="Modify-Carma-Datasets">Modify Carma Datasets<a class="anchor-link" href="#Modify-Carma-Datasets">¶</a></h2>
#

#
# <p>Carma datasets are CCS datasets taken from project Carma - see Volkart 2013.</p>
#

# In[24]:


carma_electricity_ds_name_dict = {
    'Electricity, at wood burning power plant 20 MW, truck 25km, post, pipeline 200km, storage 1000m/2025': 'Biomass CCS',
    'Electricity, at power plant/natural gas, NGCC, no CCS/2025/kWh': 'Natural gas CC',
    'Electricity, at power plant/natural gas, pre, pipeline 400km, storage 3000m/2025': 'Natural gas CCS',
    'Electricity, at BIGCC power plant 450MW, pre, pipeline 200km, storage 1000m/2025': 'Biomass CCS',
    'Electricity, at power plant/hard coal, PC, no CCS/2025': 'Coal ST',
    'Electricity, at power plant/hard coal, IGCC, no CCS/2025': 'IGCC',
    'Electricity, at wood burning power plant 20 MW, truck 25km, no CCS/2025': 'Biomass ST',
    'Electricity, at power plant/natural gas, pre, pipeline 200km, storage 1000m/2025': 'Natural gas CCS',
    'Electricity, at power plant/lignite, PC, no CCS/2025': 'Coal ST',
    'Electricity, at power plant/hard coal, pre, pipeline 200km, storage 1000m/2025': 'Coal CCS',
    'Electricity, from CC plant, 100% SNG, truck 25km, post, pipeline 200km, storage 1000m/2025': 'Biomass CCS',
    'Electricity, at wood burning power plant 20 MW, truck 25km, post, pipeline 400km, storage 3000m/2025': 'Biomass CCS',
    'Electricity, at power plant/hard coal, oxy, pipeline 400km, storage 3000m/2025': 'Coal CCS',
    'Electricity, at power plant/lignite, oxy, pipeline 200km, storage 1000m/2025': 'Coal CCS',
    'Electricity, at power plant/hard coal, post, pipeline 400km, storage 3000m/2025': 'Coal CCS',
    'Electricity, at power plant/lignite, pre, pipeline 200km, storage 1000m/2025': 'Coal CCS',
    'Electricity, at BIGCC power plant 450MW, pre, pipeline 400km, storage 3000m/2025': 'Biomass CCS',
    'Electricity, at power plant/natural gas, post, pipeline 400km, storage 1000m/2025': 'Natural gas CCS',
    'Electricity, at power plant/lignite, post, pipeline 400km, storage 3000m/2025': 'Coal CCS',
    'Electricity, at power plant/hard coal, post, pipeline 400km, storage 1000m/2025': 'Coal CCS',
    'Electricity, from CC plant, 100% SNG, truck 25km, post, pipeline 400km, storage 3000m/2025': 'Biomass CCS',
    'Electricity, at power plant/natural gas, ATR H2-CC, no CCS/2025': 'Natural gas CCS',
    'Electricity, at power plant/hard coal, pre, pipeline 400km, storage 3000m/2025': 'Coal CCS',
    'Electricity, at power plant/lignite, IGCC, no CCS/2025': 'IGCC',
    'Electricity, at power plant/hard coal, post, pipeline 200km, storage 1000m/2025': 'Coal CCS',
    'Electricity, at power plant/lignite, oxy, pipeline 400km, storage 3000m/2025': 'Coal CCS',
    'Electricity, at power plant/lignite, post, pipeline 200km, storage 1000m/2025': 'Coal CCS',
    'Electricity, at power plant/lignite, pre, pipeline 400km, storage 3000m/2025': 'Coal CCS',
    'Electricity, at power plant/natural gas, post, pipeline 200km, storage 1000m/2025': 'Natural gas CCS',
    'Electricity, at power plant/natural gas, post, pipeline 400km, storage 3000m/2025': 'Natural gas CCS',
    'Electricity, at BIGCC power plant 450MW, no CCS/2025': 'Biomass ST',
    'Electricity, from CC plant, 100% SNG, truck 25km, no CCS/2025': 'Biomass ST',
    'Electricity, at power plant/hard coal, oxy, pipeline 200km, storage 1000m/2025': 'Coal CCS'
}


# In[25]:


def modify_all_carma_electricity_datasets(db, year, scenario, update_efficiency=True, update_emissions=True):
    # First determine which image efficiency dataset needs to be used:

    image_emissions = {}
    for fuel2 in ['Coal', 'Natural gas', 'Biomass']:
        image_emissions[fuel2] = get_image_electricity_emissions_per_input_energy(scenario, fuel2,
                                                                                  sector='Power generation')

    fuel_dict = {'Biomass CCS': 'Biomass',
                 'Biomass ST': 'Biomass',
                 'Coal CCS': 'Coal',
                 'Coal ST': 'Coal',
                 'IGCC': 'Coal',
                 'Natural gas CC': 'Natural gas',
                 'Natural gas CCS': 'Natural gas'}

    for name, tech in carma_electricity_ds_name_dict.items():
        image_efficiency = get_image_efficiencies(scenario, tech)
        for ds in get_many(db, equals('name', name)):
            if update_efficiency:
                if 'Electricity, at BIGCC power plant 450MW' in ds['name']:
                    modify_carma_BIGCC_efficiency(ds, year, scenario, image_efficiency)
                else:
                    modify_standard_carma_dataset_efficiency(ds, year, scenario, image_efficiency)
            if update_emissions:
                modify_carma_dataset_emissions(db, ds, year, scenario, image_emissions[fuel_dict[tech]])

    # The efficiency defined by image also includes the electricity consumed in the carbon capture process,
    # so we have to set this exchange amount to zero:
    if update_efficiency:
        for ds in get_many(db, contains('name', 'CO2 capture')):
            for exc in technosphere(ds, *[contains('name', 'Electricity'), equals('unit', 'kilowatt hour')]):
                exc['amount'] = 0


# In[26]:


def modify_carma_dataset_emissions(db, ds, year, scenario, emission_df):
    # The dataset passed to this function doesn't have the biosphere flows directly.
    # Rather, it has an exchange (with unit MJ) that contains the biosphere flows per unit fuel input.

    biosphere_mapping = {'CH4': 'Methane, fossil',
                         'SO2': 'Sulfur dioxide',
                         'CO': 'Carbon monoxide, fossil',
                         'NOx': 'Nitrogen oxides',
                         'N2O': 'Dinitrogen monoxide'}

    image_locations = ecoinvent_to_image_locations(ds['location'])

    exc_dataset_names = [x['name'] for x in technosphere(ds, equals('unit', 'megajoule'))]

    for exc_dataset in get_many(db, *[
        either(*[equals('name', exc_dataset_name) for exc_dataset_name in exc_dataset_names])]):

        if len(list(biosphere(exc_dataset))) == 0:
            modify_carma_dataset_emissions(db, exc_dataset, year, scenario, emission_df)
            continue

        # Modify using IMAGE emissions data
        for key, value in biosphere_mapping.items():
            for exc in biosphere(exc_dataset, contains('name', value)):
                exc['amount'] = np.average(emission_df[key].loc[year][image_locations].values)
                if np.isnan(exc['amount']):
                    print('Not a number! Setting exchange to zero' + ds['name'], exc['name'], ds['location'])
                    exc['amount'] = 0
    return


# In[27]:


def modify_standard_carma_dataset_efficiency(ds, year, scenario, image_efficiency):
    if 'Electricity, at BIGCC power plant 450MW' in ds['name']:
        print("This function can't modify dataset: ", ds['name'], "It's got a different format.")
        return

    image_locations = ecoinvent_to_image_locations(ds['location'])
    image_efficiency = np.average(image_efficiency.loc[year][image_locations].values)

    # All other carma electricity datasets have a single exchange that is the combustion of a fuel in MJ.
    # We can just scale this exchange and efficiency related changes will be done

    for exc in technosphere(ds):
        exc['amount'] = 3.6 / image_efficiency

    return


# In[28]:


def modify_carma_BIGCC_efficiency(ds, year, scenario, image_efficiency):
    image_locations = ecoinvent_to_image_locations(ds['location'])
    image_efficiency = np.average(image_efficiency.loc[year][image_locations].values)

    old_efficiency = 3.6 / get_one(technosphere(ds), *[contains('name', 'Hydrogen, from steam reforming')])['amount']

    for exc in technosphere(ds):
        exc['amount'] = exc['amount'] * old_efficiency / image_efficiency
        return


#
# <h1 id="Get-image-model-results">Get image model results<a class="anchor-link" href="#Get-image-model-results">¶</a></h1>
#

# In[29]:


def read_image_data_Reg_x_Tech(scenario, technology, filename_extension, world_calc_type):
    # This function imports a set of results from image for a certain scenario and returns
    # a dataframe with the values for all years and regions for a specific technology.
    # Possible choices are listed in  image_variable_names['Technology']

    fp = os.path.join(scenarios[scenario]['filepath'], filename_extension)

    image_output = load_image_data_file(fp)

    result = {}
    lookup_number = np.where(image_variable_names['Technology'] == technology)[0][0]
    for year in image_output.years:
        result[year] = {}
        for region, vector in zip(REGIONS[:],
                                  image_output.data[:, lookup_number, list(image_output.years).index(year)]):
            result[year][region] = vector
    result = pd.DataFrame.from_dict(result, orient='index')
    if world_calc_type == 'mean':
        result['World'] = result.mean(axis=1)
    elif world_calc_type == 'sum':
        result['World'] = result.sum(axis=1)
    else:
        print("can't calculate world")
    return result


#
# <h2 id="Nuclear-Electricity-Efficiency">Nuclear Electricity Efficiency<a class="anchor-link" href="#Nuclear-Electricity-Efficiency">¶</a></h2>
#

# In[30]:


def read_electricity_uranium_consumption(scenario):
    # This function imports the efficiency of nuclear power plants in GJ electricity /kg uranium

    fp = os.path.join(scenarios[scenario]['filepath'], "tuss", "nuclfueleff.out")
    image_output = load_image_data_file(fp)
    result = {}
    for year in image_output.years:
        result[year] = {}
        for region, vector in zip(REGIONS[:], image_output.data[:, list(image_output.years).index(year)]):
            result[year][region] = vector
    df = pd.DataFrame.from_dict(result, orient='index')
    df.replace({0: np.nan},
               inplace=True)  # we set all zero values to NaN so that the global average is calcuated only from values that exist.
    df['World'] = df.mean(axis=1)
    return df


#
# <h2 id="Fossil-Electricity-Efficiency">Fossil Electricity Efficiency<a class="anchor-link" href="#Fossil-Electricity-Efficiency">¶</a></h2>
#

# In[31]:


def get_image_efficiencies(scenario, technology):
    # This function imports a set of results from image for a certain scenario and returns
    # a dataframe with the efficiency values for all years and regions for a specific technology.
    # possible choices are listed in  image_variable_names['Technology']
    fp = os.path.join(scenarios[scenario]['filepath'], "tuss", "EPG", "ElecEffAvg.out")
    elec_eff_avg = load_image_data_file(fp)

    image_efficiency = {}
    lookup_number = np.where(image_variable_names['Technology'] == technology)[0][0]
    for year in elec_eff_avg.years:
        image_efficiency[year] = {}
        for region, vector in zip(REGIONS[:],
                                  elec_eff_avg.data[:, lookup_number, list(elec_eff_avg.years).index(year)]):
            image_efficiency[year][region] = vector
    image_efficiency = pd.DataFrame.from_dict(image_efficiency, orient='index')
    image_efficiency['World'] = image_efficiency.mean(axis=1)
    return image_efficiency


#
# <h2 id="Fossil-Electricity-Emissions">Fossil Electricity Emissions<a class="anchor-link" href="#Fossil-Electricity-Emissions">¶</a></h2>
#

# In[32]:


def get_image_electricity_emission_factors(scenario, image_efficiency, fuel2, sector='Power generation'):
    # This function imports a set of results from image for a certain scenario and returns
    # a dictionary of dataframes each with the emission values for all years and regions for one pollutant.
    # possible fuel2 choices are listed in  image_variable_names['Fuel2']

    emission_dict = {'CH4': "ENEFCH4.out",
                     'CO': "ENEFCO.out",
                     'N2O': "ENEFN2O.out",
                     'NOx': "ENEFNOx.out",
                     'SO2': "ENEFSO2.out",
                     'BC': "ENEFBC.out",
                     }

    elec_emission_factors = {}
    for k, v in emission_dict.items():
        fp = os.path.join(scenarios[scenario]['filepath'], "indicatoren", v)
        elec_emission_factors[k] = load_image_data_file(fp)

    # We currently don't have a good way to deal with the fact that ecoinvent has many different VOCs listed.
    # For the moment we just allow them to scale with the efficiency.

    # Note that we don't import CO2 results as these are calculated by scaling using efficiency.
    # This is more accurate as it considers that ecoinvent is more accurate regarding the energy content
    # of the specific fuel used.

    image_emissions = {}

    fuel2_number = np.where(image_variable_names['Fuel2'] == fuel2)[0][0]
    sector_number = np.where(image_variable_names['Sector'] == sector)[0][0]

    for key, value in elec_emission_factors.items():
        image_emissions[key] = {}
        for year in elec_emission_factors[key].years:
            image_emissions[key][year] = {}

            for region, vector in zip(REGIONS[:-1], value.data[:, sector_number, fuel2_number,
                                                    list(elec_emission_factors[key].years).index(year)]):
                image_emissions[key][year][region] = vector

        image_emissions[key] = pd.DataFrame.from_dict(image_emissions[key], orient='index')

        # Note that Image reports emissions pre unit of fuel in, so we have to make a couple of calculations
        if key == 'BC':
            image_emissions[key] = (image_emissions[key].divide(image_efficiency,
                                                                axis=0)) * 3.6e-3  # convert to kg/kWh of electricity
        else:
            image_emissions[key] = (image_emissions[key].divide(image_efficiency,
                                                                axis=0)) * 3.6e-6  # convert to kg/kWh of electricity
        image_emissions[key].replace({0: np.nan},
                                     inplace=True)  # we set all zero values to NaN so that the global average is calcuated only from values that exist.
        image_emissions[key]['World'] = image_emissions[key].mean(axis=1)
        image_emissions[key].fillna(0, inplace=True)  # set nan values back to zero.

    return image_emissions


# In[33]:


def get_image_electricity_emissions_per_input_energy(scenario, fuel2, sector='Power generation'):
    # This function imports a set of results from image for a certain scenario and returns
    # a dictionary of dataframes each with the emission values for all years and regions for one pollutant.
    # possible fuel2 choices are listed in  image_variable_names['Fuel2']
    elec_emission_factors = {}

    fp = os.path.join(scenarios[scenario]['filepath'], "indicatoren", "ENEFCH4.out")
    elec_emission_factors['CH4'] = load_image_data_file(fp)

    fp = os.path.join(scenarios[scenario]['filepath'], "indicatoren", "ENEFCO.out")
    elec_emission_factors['CO'] = load_image_data_file(fp)

    fp = os.path.join(scenarios[scenario]['filepath'], "indicatoren", "ENEFN2O.out")
    elec_emission_factors['N2O'] = load_image_data_file(fp)

    fp = os.path.join(scenarios[scenario]['filepath'], "indicatoren", "ENEFNOx.out")
    elec_emission_factors['NOx'] = load_image_data_file(fp)

    fp = os.path.join(scenarios[scenario]['filepath'], "indicatoren", "ENEFSO2.out")
    elec_emission_factors['SO2'] = load_image_data_file(fp)

    fp = os.path.join(scenarios[scenario]['filepath'], "indicatoren", "ENEFBC.out")
    elec_emission_factors['BC'] = load_image_data_file(fp)

    # We currently don't have a good way to deal with the fact that ecoinvent has many different VOCs listed.
    # For the moment we just allow them to scale with the efficiency.

    # Note that we don't import CO2 results as these are calculated by scaling using efficiency.
    # This is more accurate as it considers that ecoinvent is more accurate regarding the energy content of coal.

    image_emissions = {}

    fuel2_number = np.where(image_variable_names['Fuel2'] == fuel2)[0][0]
    sector_number = np.where(image_variable_names['Sector'] == sector)[0][0]

    for key, value in elec_emission_factors.items():
        image_emissions[key] = {}
        for year in elec_emission_factors[key].years:
            image_emissions[key][year] = {}

            for region, vector in zip(REGIONS[:-1], value.data[:, sector_number, fuel2_number,
                                                    list(elec_emission_factors[key].years).index(year)]):
                image_emissions[key][year][region] = vector

        image_emissions[key] = pd.DataFrame.from_dict(image_emissions[key], orient='index')

        # Note that Image reports emissions pre unit of fuel in, so we have to make a couple of calculations
        if key == 'BC':
            image_emissions[key] = image_emissions[key] * 1e-3  # convert to kg/MJ of input energy
        else:
            image_emissions[key] = image_emissions[key] * 1e-6  # convert to kg/MJ of input energy
        image_emissions[key].replace({0: np.nan},
                                     inplace=True)  # we set all zero values to NaN so that the global average is calcuated only from values that exist.
        image_emissions[key]['World'] = image_emissions[key].mean(axis=1)
        image_emissions[key].fillna(0, inplace=True)  # set nan values back to zero.

    return image_emissions


#
# <h1 id="Electricity-markets:">Electricity markets:<a class="anchor-link" href="#Electricity-markets:">¶</a></h1>
#

#
# <h2 id="Define-available-technologies:">Define available technologies:<a class="anchor-link" href="#Define-available-technologies:">¶</a></h2>
#

# In[34]:


available_electricity_generating_technologies = {

    'Solar PV': ['electricity production, photovoltaic, 3kWp slanted-roof installation, multi-Si, panel, mounted',
                 'electricity production, photovoltaic, 3kWp slanted-roof installation, single-Si, panel, mounted',
                 'electricity production, photovoltaic, 570kWp open ground installation, multi-Si'],

    'CSP': ['Electricity production for a 50MW parabolic trough power plant',  # Will be available in ecoinvent 3.4
            'Electricity production at a 20MW solar tower power plant'],  # Will be available in ecoinvent 3.4

    'Wind onshore': ['electricity production, wind, <1MW turbine, onshore',
                     'electricity production, wind, 1-3MW turbine, onshore',
                     'electricity production, wind, >3MW turbine, onshore'],

    'Wind offshore': ['electricity production, wind, 1-3MW turbine, offshore'],

    'Hydro': ['electricity production, hydro, reservoir, alpine region',
              'electricity production, hydro, reservoir, non-alpine region',
              'electricity production, hydro, reservoir, tropical region',
              'electricity production, hydro, run-of-river'],

    'Other renewables': ['electricity production, deep geothermal'],

    'Nuclear': ['electricity production, nuclear, boiling water reactor',
                'electricity production, nuclear, pressure water reactor, heavy water moderated',
                'electricity production, nuclear, pressure water reactor'],

    'Coal ST': ['electricity production, hard coal',
                'electricity production, lignite'],

    'Coal CHP': ['heat and power co-generation, hard coal',
                 'heat and power co-generation, lignite'],

    'IGCC': ['Electricity, at power plant/hard coal, IGCC, no CCS/2025',  # From Carma project
             'Electricity, at power plant/lignite, IGCC, no CCS/2025'],  # From Carma project

    'Oil ST': ['electricity production, oil'],

    'Oil CHP': ['heat and power co-generation, oil'],

    'Oil CC': ['electricity production, oil'],  # Use copy of Oil ST here as this doesn't exist in ecoinvent

    'Natural gas OC': ['electricity production, natural gas, conventional power plant'],

    'Natural gas CC': ['electricity production, natural gas, combined cycle power plant'],

    'Natural gas CHP': ['heat and power co-generation, natural gas, combined cycle power plant, 400MW electrical',
                        'heat and power co-generation, natural gas, conventional power plant, 100MW electrical'],

    'Biomass CHP': ['heat and power co-generation, wood chips, 6667 kW, state-of-the-art 2014',
                    'heat and power co-generation, wood chips, 6667 kW',
                    'heat and power co-generation, biogas, gas engine'],

    'Biomass CC': ['heat and power co-generation, wood chips, 6667 kW, state-of-the-art 2014',
                   # Use copy of Biomass CHP here as this not available in ecoinvent
                   'heat and power co-generation, wood chips, 6667 kW',
                   'heat and power co-generation, biogas, gas engine'],

    'Biomass ST': ['heat and power co-generation, wood chips, 6667 kW, state-of-the-art 2014',
                   # Use copy of Biomass CHP here as this not available in ecoinvent
                   'heat and power co-generation, wood chips, 6667 kW',
                   'heat and power co-generation, biogas, gas engine'],

    'Coal CCS': ['Electricity, at power plant/hard coal, pre, pipeline 200km, storage 1000m/2025',
                 'Electricity, at power plant/lignite, pre, pipeline 200km, storage 1000m/2025',
                 'Electricity, at power plant/hard coal, post, pipeline 200km, storage 1000m/2025',
                 'Electricity, at power plant/lignite, post, pipeline 200km, storage 1000m/2025',
                 'Electricity, at power plant/lignite, oxy, pipeline 200km, storage 1000m/2025',
                 'Electricity, at power plant/hard coal, oxy, pipeline 200km, storage 1000m/2025'],

    'Coal CHP CCS': ['Electricity, at power plant/hard coal, pre, pipeline 200km, storage 1000m/2025',
                     # Carma project didn't include Coal CHP CCS
                     'Electricity, at power plant/lignite, pre, pipeline 200km, storage 1000m/2025',
                     'Electricity, at power plant/hard coal, post, pipeline 200km, storage 1000m/2025',
                     'Electricity, at power plant/lignite, post, pipeline 200km, storage 1000m/2025',
                     'Electricity, at power plant/lignite, oxy, pipeline 200km, storage 1000m/2025',
                     'Electricity, at power plant/hard coal, oxy, pipeline 200km, storage 1000m/2025'],

    'Oil CCS': ['Electricity, at power plant/hard coal, pre, pipeline 200km, storage 1000m/2025',
                # Carma project didn't include oil - we just use all coal and gas datasets as a proxy
                'Electricity, at power plant/lignite, pre, pipeline 200km, storage 1000m/2025',
                'Electricity, at power plant/hard coal, post, pipeline 200km, storage 1000m/2025',
                'Electricity, at power plant/lignite, post, pipeline 200km, storage 1000m/2025',
                'Electricity, at power plant/lignite, oxy, pipeline 200km, storage 1000m/2025',
                'Electricity, at power plant/hard coal, oxy, pipeline 200km, storage 1000m/2025',
                'Electricity, at power plant/natural gas, pre, pipeline 200km, storage 1000m/2025',
                'Electricity, at power plant/natural gas, post, pipeline 200km, storage 1000m/2025'],

    'Oil CHP CCS': ['Electricity, at power plant/hard coal, pre, pipeline 200km, storage 1000m/2025',
                    # Carma project didn't include oil - we just use all coal and gas datasets as a proxy
                    'Electricity, at power plant/lignite, pre, pipeline 200km, storage 1000m/2025',
                    'Electricity, at power plant/hard coal, post, pipeline 200km, storage 1000m/2025',
                    'Electricity, at power plant/lignite, post, pipeline 200km, storage 1000m/2025',
                    'Electricity, at power plant/lignite, oxy, pipeline 200km, storage 1000m/2025',
                    'Electricity, at power plant/hard coal, oxy, pipeline 200km, storage 1000m/2025',
                    'Electricity, at power plant/natural gas, pre, pipeline 200km, storage 1000m/2025',
                    'Electricity, at power plant/natural gas, post, pipeline 200km, storage 1000m/2025'],

    'Natural gas CCS': ['Electricity, at power plant/natural gas, pre, pipeline 200km, storage 1000m/2025',
                        'Electricity, at power plant/natural gas, post, pipeline 200km, storage 1000m/2025'],

    'Natural gas CHP CCS': ['Electricity, at power plant/natural gas, pre, pipeline 200km, storage 1000m/2025',
                            # Copy normal natural gas CCS datasets here
                            'Electricity, at power plant/natural gas, post, pipeline 200km, storage 1000m/2025'],

    'Biomass CCS': ['Electricity, from CC plant, 100% SNG, truck 25km, post, pipeline 200km, storage 1000m/2025',
                    'Electricity, at wood burning power plant 20 MW, truck 25km, post, pipeline 200km, storage 1000m/2025',
                    'Electricity, at BIGCC power plant 450MW, pre, pipeline 200km, storage 1000m/2025'],

    'Biomass CHP CCS': ['Electricity, from CC plant, 100% SNG, truck 25km, post, pipeline 200km, storage 1000m/2025',
                        # Copy normal wood CCS datasets here as CHP not available
                        'Electricity, at wood burning power plant 20 MW, truck 25km, post, pipeline 200km, storage 1000m/2025',
                        'Electricity, at BIGCC power plant 450MW, pre, pipeline 200km, storage 1000m/2025'],

}

#
# <h2 id="Overall-function-to-change-markets">Overall function to change markets<a class="anchor-link" href="#Overall-function-to-change-markets">¶</a></h2>
#

#
# <p>Function that returns all IMAGE locations that are interested by an ecoinvent location:</p>
#

# In[35]:


# these locations aren't found correctly by the constructiive geometries library - we correct them here:
fix_names = {'CSG': 'CN-CSG',
             'SGCC': 'CN-SGCC',

             'RFC': 'US-RFC',
             'SERC': 'US-SERC',
             'TRE': 'US-TRE',
             'ASCC': 'US-ASCC',
             'HICC': 'US-HICC',
             'FRCC': 'US-FRCC',
             'SPP': 'US-SPP',
             'MRO, US only': 'US-MRO',
             'NPCC, US only': 'US-NPCC',
             'WECC, US only': 'US-WECC',

             'IAI Area, Africa': 'IAI Area 1, Africa',
             'IAI Area, South America': 'IAI Area 3, South America',
             'IAI Area, Asia, without China and GCC': 'IAI Area 4&5, without China',
             'IAI Area, North America, without Quebec': 'IAI Area 2, without Quebec',
             'IAI Area, Gulf Cooperation Council': 'IAI Area 8, Gulf'
             }


# In[36]:


def ecoinvent_to_image_locations(loc):
    if loc == 'RoW':
        loc = 'GLO'

    if loc in fix_names.keys():
        new_loc_name = fix_names[loc]
        return [r[1] for r in geomatcher.intersects(new_loc_name) if r[0] == 'IMAGE']

    else:
        return [r[1] for r in geomatcher.intersects(loc) if r[0] == 'IMAGE']


# In[37]:


def update_electricity_markets(db, year, scenario):
    # import the image market mix from the image result files:
    image_electricity_market_df = get_image_markets(year, scenario)

    # Remove all electricity producers from markets:
    db = empty_low_voltage_markets(db)
    db = empty_medium_voltage_markets(db)
    db = empty_high_voltage_markets(db)  # This function isn't working as expected - it needs to delete imports as well.

    changes = {}
    # update high voltage markets:
    for ds in get_many(db, *electricity_market_filter_high_voltage):
        changes[ds['code']] = {}
        changes[ds['code']].update({('meta data', x): ds[x] for x in ['name', 'location']})
        changes[ds['code']].update({('original exchanges', k): v for k, v in get_exchange_amounts(ds).items()})
        delete_electricity_inputs_from_market(
            ds)  # This function will delete the markets. Once Wurst is updated this can be deleted.
        add_new_datasets_to_electricity_market(ds, db, image_electricity_market_df)
        changes[ds['code']].update({('updated exchanges', k): v for k, v in get_exchange_amounts(ds).items()})
    return changes


#
# <h2 id="Define-electricity-market-filters">Define electricity market filters<a class="anchor-link" href="#Define-electricity-market-filters">¶</a></h2>
#

# In[38]:


electricity_market_filter_high_voltage = [contains('name', 'market for electricity, high voltage'),
                                          doesnt_contain_any('name',
                                                             ['aluminium industry', 'internal use in coal mining'])]

electricity_market_filter_medium_voltage = [contains('name', 'market for electricity, medium voltage'),
                                            doesnt_contain_any('name', ['aluminium industry',
                                                                        'electricity, from municipal waste incineration'])]

electricity_market_filter_low_voltage = [contains('name', 'market for electricity, low voltage')]


#
# <h2 id="Modify-high-voltage-markets">Modify high voltage markets<a class="anchor-link" href="#Modify-high-voltage-markets">¶</a></h2>
#

# In[39]:


def delete_electricity_inputs_from_market(ds):
    # This function reads through an electricity market dataset and deletes all electricity inputs that are not own consumption.
    ds['exchanges'] = [exc for exc in get_many(ds['exchanges'], *[either(*[exclude(contains('unit', 'kilowatt hour')),
                                                                           contains('name',
                                                                                    'market for electricity, high voltage'),
                                                                           contains('name',
                                                                                    'market for electricity, medium voltage'),
                                                                           contains('name',
                                                                                    'market for electricity, low voltage'),
                                                                           contains('name',
                                                                                    'electricity voltage transformation')])])]


# In[40]:


def get_image_markets(year, scenario):
    # This returns a pandas dataframe containing the electricity mix for a certain year for all image locations.
    # This function is totally inefficient and should be rewritten to consider the year in question. Currently it calculates for all years and then filters out the year in question!
    fp = os.path.join(scenarios[scenario]['filepath'], "T2RT", "ElecProdSpec.out")
    elec_production = load_image_data_file(fp)

    elec_prod = {}
    elec_prod_dfs = {}
    for i, region in enumerate(REGIONS):
        elec_prod[region] = elec_production.data[i, :, :]
        elec_prod_dfs[region] = pd.DataFrame(elec_production.data[i, :, :], columns=elec_production.years,
                                             index=image_variable_names['Technology'].dropna().values).T.drop(
            'EMPTY CATEGORY!!', axis=1)

    for region in REGIONS[:-1]:
        elec_prod_dfs['World'] += elec_prod_dfs[region]

    df = pd.concat([pd.Series(elec_prod_dfs[region].loc[year], name=region) for region in REGIONS[:-1]], axis=1)
    df['World'] = df.sum(axis=1)
    empty_columns = find_empty_columns(df)
    df = df.divide(df.sum(axis=0)).sort_values(by='World', ascending=False).T.drop(empty_columns, axis=1)
    return df


def find_average_mix(df):
    # This function considers that there might be several image regions that match the ecoinvent region. This function returns the average mix across all regions.
    return df.divide(df.sum().sum()).sum()


# In[41]:


def find_ecoinvent_electricity_datasets_in_same_ecoinvent_location(tech, location, db):
    # first try ecoinvent location code:
    try:
        return [x for x in get_many(db, *[
            either(*[equals('name', name) for name in available_electricity_generating_technologies[tech]]),
            equals('location', location), equals('unit', 'kilowatt hour')])]
    # otherwise try image location code (for new datasets)
    except:
        return [x for x in get_many(db, *[
            either(*[equals('name', name) for name in available_electricity_generating_technologies[tech]]),
            equals('location', ecoinvent_to_image_locations(location)), equals('unit', 'kilowatt hour')])]


# In[42]:


def find_other_ecoinvent_regions_in_image_region(loc):
    if loc == 'RoW':
        loc = 'GLO'

    if loc in fix_names:
        new_loc_name = fix_names[loc]
        image_regions = [r for r in geomatcher.intersects(new_loc_name) if r[0] == 'IMAGE']

    else:
        image_regions = [r for r in geomatcher.intersects(loc) if r[0] == 'IMAGE']

    temp = []
    for image_region in image_regions:
        temp.extend([r for r in geomatcher.contained(image_region)])

    result = []
    for temp in temp:
        if type(temp) == tuple:
            result.append(temp[1])
        else:
            result.append(temp)
    return set(result)


# In[43]:


def find_ecoinvent_electricity_datasets_in_image_location(tech, location, db):
    return [x for x in get_many(db, *[
        either(*[equals('name', name) for name in available_electricity_generating_technologies[tech]]),
        either(*[equals('location', loc) for loc in find_other_ecoinvent_regions_in_image_region(location)]),
        equals('unit', 'kilowatt hour')
        ])]


# In[44]:


def find_ecoinvent_electricity_datasets_in_all_locations(tech, db):
    return [x for x in get_many(db, *[
        either(*[equals('name', name) for name in available_electricity_generating_technologies[tech]]),
        equals('unit', 'kilowatt hour')])]


# In[45]:


def add_new_datasets_to_electricity_market(ds, db, df):
    # This function adds new electricity datasets to a market based on image results. We pass not only a dataset to modify, but also a pandas dataframe containing the new electricity mix information, and the db from which we should find the datasets
    # find out which image regions correspond to our dataset:

    image_locations = ecoinvent_to_image_locations(ds['location'])

    # here we find the mix of technologies in the new market and how much they contribute:
    mix = find_average_mix(df.loc[image_locations])  # could be several image locations - we just take the average

    # here we find the datasets that will make up the mix for each technology
    datasets = {}
    for i in mix.index:
        if mix[i] != 0:
            print('Next Technology: ',i)
            # First try to find a dataset that is from that location (or image region for new datasets):
            datasets[i] = find_ecoinvent_electricity_datasets_in_same_ecoinvent_location(i, ds['location'], db)
            print('First round: ',i, [(ds['name'], ds['location']) for ds in datasets[i]])

            # If this doesn't work, we try to take a dataset from another ecoinvent region within the same image region
            if len(datasets[i]) == 0:
                datasets[i] = find_ecoinvent_electricity_datasets_in_image_location(i, ds['location'], db)
                print('Second round: ',i, [(ds['name'], ds['location']) for ds in datasets[i]])

            # If even this doesn't work, try taking a global datasets
            if len(datasets[i]) == 0:
                datasets[i] = find_ecoinvent_electricity_datasets_in_same_ecoinvent_location(i, 'GLO', db)
                print('Third round: ',i, [(ds['name'], ds['location']) for ds in datasets[i]])

            # if no global dataset available, we just take the average of all datasets we have:
            if len(datasets[i]) == 0:
                datasets[i] = find_ecoinvent_electricity_datasets_in_all_locations(i, db)
                print('Fourth round: ',i, [(ds['name'], ds['location']) for ds in datasets[i]])

            # If we still can't find a dataset, we just take the global market group
            if len(datasets[i]) == 0:
                print('No match found for location: ', ds['location'], ' Technology: ', i,
                      '. Taking global market group for electricity')
                datasets[i] = [x for x in get_many(db, *[equals('name', 'market group for electricity, high voltage'),
                                                         equals('location', 'GLO')])]

    # Now we add the new exchanges:
    for i in mix.index:
        if mix[i] != 0:
            total_amount = mix[i]
            amount = total_amount / len(datasets[i])
            for dataset in datasets[i]:
                ds['exchanges'].append({
                    'amount': amount,
                    'unit': dataset['unit'],
                    'input': (dataset['database'], dataset['code']),
                    'type': 'technosphere',
                    'name': dataset['name'],
                    'location': dataset['location']
                })

    # confirm that exchanges sum to 1!
    sum = np.sum([exc['amount'] for exc in technosphere(ds, *[equals('unit', 'kilowatt hour'),
                                                              doesnt_contain_any('name', [
                                                                  'market for electricity, high voltage'])])])
    if round(sum, 4) != 1.00:  print(ds['location'], " New exchanges don't add to one! something is wrong!", sum)
    return

# In[ ]:




