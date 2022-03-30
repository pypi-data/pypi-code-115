# Electricity sorting constants from wurst paper (TODO: check citation)

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


### Constants relating to IMAGE

DEFAULT_REGIONS = [
    'Canada',
    'USA',
    'Mexico',
    'Central America',
    'Brazil',
    'Rest of South America',
    'Northern Africa',
    'Western Africa',
    'Eastern Africa',
    'South Africa',
    'Western Europe',
    'Central Europe',
    'Turkey',
    'Ukraine region',
    'Central Asia',
    'Russia Region',
    'Middle east',
    'India',
    'Korea Region',
    'China Region',
    'South Asia',
    'Indonesia Region',
    'Japan',
    'Oceania',
    'Rest of South Asia',
    'Rest of Southern Africa',
    'World',
]
DEFAULT_TECHNOLOGIES = [
    'Solar PV',
    'CSP',
    'Wind onshore',
    'Wind offshore',
    'Hydro',
    'Other renewables',
    'Nuclear',
    'EMPTY CATEGORY!!',
    'Coal ST',
    'Oil ST',
    'Natural gas OC',
    'Biomass ST',
    'IGCC',
    'Oil CC',
    'Natural gas CC',
    'Biomass CC',
    'Coal CCS',
    'Oil CCS',
    'Natural gas CCS',
    'Biomass CCS',
    'Coal CHP',
    'Oil CHP',
    'Natural gas CHP',
    'Biomass CHP',
    'Coal CHP CCS',
    'Oil CHP CCS',
    'Natural gas CHP CCS',
    'Biomass CHP CCS'
]