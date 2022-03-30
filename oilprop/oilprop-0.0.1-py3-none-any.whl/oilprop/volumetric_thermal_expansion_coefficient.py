def volumetric_thermal_expansion_coefficient(rho):
    """
    Takes oil density and returns oil volumetric thermal expansion coefficient
    :param rho: the density of an oil, kg/m3
    :return: volumetric thermal expansion coefficient, 1/(Celsius degree)
    """
    a = None
    if 700 <= rho <= 719:
        a = 0.001225
    elif 720 <= rho <= 739:
        a = 0.001183
    elif 740 <= rho <= 759:
        a = 0.001118
    elif 760 <= rho <= 779:
        a = 0.001054
    elif 780 <= rho <= 799:
        a = 0.000995
    elif 800 <= rho <= 819:
        a = 0.000937
    elif 820 <= rho <= 839:
        a = 0.000882
    elif 840 <= rho <= 859:
        a = 0.000831
    elif 860 <= rho <= 879:
        a = 0.000782
    elif 880 <= rho <= 899:
        a = 0.000734
    elif 900 <= rho <= 919:
        a = 0.000688
    elif 920 <= rho <= 939:
        a = 0.000645
    return a
