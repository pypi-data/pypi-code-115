"""Provisional HST instrument and observational settings.
See Optics and Observation Conditions spreadsheet at
https://docs.google.com/spreadsheets/d/1pMUB_OOZWwXON2dd5oP8PekhCT5MBBZJO1HV7IMZg4Y/edit?usp=sharing for list of
sources. """
import lenstronomy.Util.util as util

__all__ = ['HST']

# F160W filter configs
WFC3_F160W_band_obs = {'exposure_time': 5400.,  # ~90mins orbit on HST, but this number corresponds to
                       # approximately two HST orbits with overheads, guide star aquisition. ~2700s science exposure per orbit
              'sky_brightness': 22.3,
              'magnitude_zero_point': 25.96,
              'num_exposures': 1,
              'seeing': 0.08, # set equal to the approx pixel size for drizzled PSF. Note that undrizzled PSF FWHM ~ 0.15" (Windhorst et al 2011)
              'psf_type': 'GAUSSIAN'
              }

# configs meant to simulate images close to those provided as part of the Time Delay Lens Modeling Challenge
TDLMC_F160W_band_obs = {'exposure_time': 5400.,  # ~90mins orbit on HST, but this number corresponds to
                       # approximately two HST orbits with overheads, guide star aquisition. ~2700s science exposure per orbit
              'sky_brightness': 22.0,
              'magnitude_zero_point': 25.9463,
              'num_exposures': 1,
              'seeing': None,
              'psf_type': 'PIXEL' # note kernel_point_source (the PSF map) must be provided separately
              }

"""
:keyword exposure_time: exposure time per image (in seconds)
:keyword sky_brightness: sky brightness (in magnitude per square arcseconds in units of electrons)
:keyword magnitude_zero_point: magnitude in which 1 count (e-) per second per arcsecond square is registered
:keyword num_exposures: number of exposures that are combined (depends on coadd_years)
:keyword seeing: Full-Width-at-Half-Maximum (FWHM) of PSF
:keyword psf_type: string, type of PSF ('GAUSSIAN' and 'PIXEL' supported)
"""


class HST(object):
    """
    class contains HST instrument and observation configurations
    """

    def __init__(self, band='TDLMC_F160W', psf_type='PIXEL', coadd_years=None):
        """

        :param band: string, 'WFC3_F160W' or 'TDLMC_F160W' supported. Determines obs dictionary.
        :param psf_type: string, type of PSF ('GAUSSIAN', 'PIXEL' supported).
        :param coadd_years: int, number of years corresponding to num_exposures in obs dict. Currently supported: None.
        """

        if band == 'TDLMC_F160W':
            self.obs = TDLMC_F160W_band_obs
        elif band == 'WFC3_F160W' or band == 'F160W':
            self.obs = WFC3_F160W_band_obs

        else:
            raise ValueError("band %s not supported! Choose 'WFC3_F160W' or 'TDLMC_F160W'." % band)

        if psf_type == 'GAUSSIAN':
            self.obs['psf_type'] = 'GAUSSIAN'
        elif psf_type != 'PIXEL':
            raise ValueError("psf_type %s not supported!" % psf_type)

        if coadd_years is not None:
            raise ValueError(" %s coadd_years not supported! "
                             "You may manually adjust num_exposures in obs dict if required." % coadd_years)

        # WFC3 camera settings
        self.camera = {'read_noise': 4,
                       'pixel_scale': 0.08, # approx pixel size for drizzled PSF
                       'ccd_gain': 2.5,
                       }
        """
        :keyword read_noise: std of noise generated by read-out (in units of electrons)
        :keyword pixel_scale: scale (in arcseconds) of pixels
        :keyword ccd_gain: electrons/ADU (analog-to-digital unit).
        """

    def kwargs_single_band(self):
        """

        :return: merged kwargs from camera and obs dicts
        """
        kwargs = util.merge_dicts(self.camera, self.obs)
        return kwargs
