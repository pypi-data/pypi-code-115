"""Some resources for cleaning Rushmore data."""
from typing import Optional, Tuple


def rig_type(arg: str) -> Tuple[str, bool]:
    """Converts Rushmore Rig Type designation keyword to text.

    Returns:
        Tuple, where:
          1st element is the rig type
          2nd element is for determining whether a dual action rig was part
          of the supplied argument - useful for Drilling Performance Review.

    Raises:
        ValueError for rig types not specified in Rushmore documentation.
    """
    rig_types = {
        # Land rigs
        "LA": "Land rig (Rented)",
        "LO": "Land rig (Owned)",
        "HR": "Heli-rig",
        "OL": "Other land rig",
        # Shallow barge rigs
        "SU": "Submersible",
        "BA": "Barge",
        # Offshore rigs - fixed
        "HP": "Hydraulic workover unit",
        "PL": "Platform - rigid leg",
        "PT": "Platform - tethered leg",
        "PS": "Platform - spar",
        "SP": "Permanently moored",
        # Offshore rigs - mobile
        "JK": "Jack-up",
        "JP": "Jack-up over platform",
        "TB": "Platform tender-assisted barge",
        "TS": "Platform tender-assisted semi-sub",
        "TJ": "Platform tender-assisted jack-up",
        "DS": "Drillship",
        "SS": "Semi-submersible",
    }

    if not arg:
        return ("N/A", False)

    distinct_rigs = {i for i in rig_types if i in arg}

    if not distinct_rigs:
        raise ValueError(f"Rig type designation '{arg}' is unknown.")

    if len(distinct_rigs) > 1:
        if distinct_rigs == {"SS", "TS"}:
            output_type = rig_types["SS"]
        elif distinct_rigs == {"BA", "TB"}:
            output_type = rig_types["BA"]
        elif distinct_rigs == {"JK", "TJ"}:
            output_type = rig_types["JK"]
        else:
            output_type = "Several"
    else:
        [rig] = distinct_rigs
        output_type = rig_types[rig]

    # Assuming if dual action is listed among a list of rigs, it is significant
    is_dual_action = "(2)" in arg

    return (output_type, is_dual_action)


def hole_type(arg: str) -> Optional[str]:
    """Converts Rushmore hole types to text."""
    hole_types = {
        "N": "New well",
        "G": "Geological sidetrack",
        "S": "Slot recovery",
        "O": "Other",
    }
    return hole_types.get(arg.upper(), None)


def well_type(arg: str) -> Optional[str]:
    """Converts Rushmore well types to text."""
    well_types = {
        "E": "Exploration",
        "D": "Development",
        "A": "Appraisal",
    }
    return well_types.get(arg.upper(), None)
