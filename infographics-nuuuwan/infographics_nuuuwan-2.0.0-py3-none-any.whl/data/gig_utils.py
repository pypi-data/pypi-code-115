from gig import ent_types, ents


def get_full_name(region_id):
    region_ent = ents.get_entity(region_id)
    region_name = region_ent['name']
    region_entity_type = ent_types.get_entity_type(region_id)
    if region_entity_type == 'country':
        return region_name
    return f'{region_name} {region_entity_type.upper()}'


def get_by_name(region_type, label):
    return f'{label} by {region_type.upper()}'
