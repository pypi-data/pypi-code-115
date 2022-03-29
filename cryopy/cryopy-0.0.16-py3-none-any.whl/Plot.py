#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 29 09:48:40 2022

@author: valentinsauvage
"""

def phase_diagram(pressure):
    """
    ========== DESCRIPTION ==========

    This function plot the phase diagram of Helium 3 / Helium 4 mixture

    ========== VALIDITY ==========

    <pressure> : []

    ========== INPUT ==========
    
    <pressure>
        -- float --
        The pressure of Helium 3
        [Pa]

    ========== OUTPUT ==========

    <phase_diagram>
        -- plot --
        The phase diagram of Helium 3 / Helium 4 mixture
        []

    ========== STATUS ==========

    Status : Checked

    """
        
    ################## MODULES ################################################
    
    import matplotlib.pyplot as plt
    import numpy as np
    from cryopy.Helium import Helium7
    
    ################## INITIALISATION #########################################
    
    # Temperature and fraction of 3HE at the tricritical point
    TRICRITICAL_TEMPEATURE = tricritical_temperature(pressure)
    TRICRITICAL_FRACTION_3HE = tricritical_fraction_3he(pressure)
    
    # Along the transition line 
    FRACTION_3HE_TRANSITION = np.array(0,TRICRITICAL_FRACTION_3HE,0.001)
    TEMPERATURE_TRANSITION = Helium7.transition_temperature(pressure,FRACTION_3HE_TRANSITION)
    
    # Along the dilute curbe
    TEMPERATURE_DILUTE = np.array(0,TRICRITICAL_TEMPEATURE,0.001)
    FRACTION_3HE_DILUTE = Helium7.fraction_3he_dilute(TEMPERATURE_DILUTE,pressure)
    
    # Along the concentrate curbe
    TEMPERATURE_CONCENTRATE = np.array(0,TRICRITICAL_TEMPEATURE,0.001)
    FRACTION_3HE_CONCENTRATE = Helium7.fraction_3he_concentrate(TEMPERATURE_CONCENTRATE,pressure)  
    
    ################## FUNCTION ###############################################
    
    plt.figure()
    plt.plot(TRICRITICAL_FRACTION_3HE,TRICRITICAL_TEMPEATURE)
    plt.plot(FRACTION_3HE_TRANSITION,TEMPERATURE_TRANSITION)
    plt.plot(FRACTION_3HE_DILUTE,TEMPERATURE_DILUTE)
    plt.plot(FRACTION_3HE_CONCENTRATE,TEMPERATURE_CONCENTRATE)
    plt.title(r'Phase diagram of $^3He-^4He$ mixture at '+str(pressure)+ 'Pa')
    plt.xlabel('Fraction of $^3He$ [%]')
    plt.ylabel('Temperature [K]')
    plt.show()
    
    return 
