"""
Tamar Ervin
Date: June 23, 2021

functions for plotting images and various
solar observable comparison plots

"""

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from scipy import stats
from SolAster.tools.settings import PlotDir


def plot_image(los_image, nfig=None, cmap='gray', title=None):
    """
    function to plot AIA los disk images

    Parameters
    ----------
    los_image: 2D line of sight image to plot
    nfig: figure number
    cmap: colormap to use
    title: figure title

    Returns
    -------

    """

    plot_arr = los_image.data

    plot_arr[plot_arr < .001] = .001

    norm_max = max(1.01, np.nanmax(plot_arr))
    norm = colors.LogNorm(vmin=1.0, vmax=norm_max)

    # plot the initial image
    if nfig is None:
        cur_figs = plt.get_fignums()
        if not nfig:
            nfig = 0
        else:
            nfig = cur_figs.max() + 1

    plt.figure(nfig)

    plt.imshow(plot_arr, extent=[los_image.x.min(), los_image.x.max(), los_image.y.min(), los_image.y.max()],
               origin="lower", cmap=cmap, aspect="equal", norm=norm)
    plt.xlabel("Latitude")
    plt.ylabel("Carrinton Longitude")
    if title is not None:
        plt.title(title)

    return None


def hmi_plot(int_map, mag_map, vel_map, fac_inds, spot_inds, mu, save_fig=None):
    """
    fucntion to plot diagnostic plots showing HMI images and thresholded maps
    Identical to Figure 1 in Ervin et al. (2021) - In prep.

    Parameters
    ----------
    int_map: Sunpy map
        flattened intensitygram
    mag_map: Sunpy map
        corrected magntogram
    vel_map: Sunpy map
        spacecraft velocity and differential rotation subtracted Dopplergram
    fac_inds: int, array
        array of indices where faculae are detected
    spot_inds: int, array
        array of indices where sunspots are detected
    mu: float, array
        array of mu (cosine theta) values
    save_fig: str
        path to save file, None if not saving

    Returns
    -------

    """

    # make cute plots
    fig, axs = plt.subplots(2, 2, sharey='row', sharex='col', figsize=[12, 12],
                            gridspec_kw={'hspace': 0.1, 'wspace': 0.1})

    # intensity map
    int_data = int_map.data
    int_data = np.where(int_data == 0, np.nan, int_data)
    axs[0, 0].imshow(int_data, cmap=plt.get_cmap('hinodesotintensity'))
    axs[0, 0].set_title("Flattened Continuum Intensity")

    # magnetic field map
    mag_data = np.abs(mag_map.data)
    axs[1, 0].imshow(mag_data, cmap=plt.get_cmap('Purples'))
    axs[1, 0].set_title("Unsigned Magnetic Flux Density")

    # Doppler map
    good_mu = np.logical_and(mu > 0.3, mu != np.nan)
    vel_data = np.full(vel_map.data.shape, np.nan)
    vel_data[good_mu] = vel_map.data[good_mu]
    axs[0, 1].imshow(vel_data, cmap=plt.get_cmap('Greys'))
    axs[0, 1].set_title("Line-of-sight Corrected Doppler Velocity")

    # threshold image
    fac = fac_inds.astype(int)
    spot = 1 - spot_inds.astype(int)
    thresh = spot + fac
    axs[1, 1].imshow(thresh, cmap=plt.get_cmap('bwr'))
    axs[1, 1].set_title("Thresholded Map")

    # tick marks
    for i in range(0, 2):
        for j in range(0, 2):
            axs[i, j].set_xticks([])
            axs[i, j].set_yticks([])

    # save if needed
    if save_fig is not None:
        plt.savefig(save_fig)
