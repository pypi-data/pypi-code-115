import numpy as np
from astropy import wcs
from astropy.io.fits import getdata
from astropy.stats import sigma_clipped_stats
from photutils.detection import DAOStarFinder

#216.3969016 32.8258449
data = getdata('/Users/daniel/Desktop/NDWFS_Tiles/Bw_FITS/NDWFSJ1426p3236_Bw_03_fix.fits')

mean, median, std = sigma_clipped_stats(data, sigma=3.0) 

daofind = DAOStarFinder(fwhm=3.0, threshold=2.*std)  
sources = daofind(data - median)  
for col in sources.colnames:  
    sources[col].info.format = '%.8g'  # for consistent table output
print(sources)  

