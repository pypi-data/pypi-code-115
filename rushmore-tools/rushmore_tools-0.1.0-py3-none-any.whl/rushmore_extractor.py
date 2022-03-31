"""Module for extracting data from the IHS Markit Rushmore API.

The module abstracts the operation of extracting data from the API,
allowing for swift retrieval of data from specific performance reviews.
Includes possibility for passing filters to fetch only desired data.

  Typical usage example:
  >>> ex = RushmoreExtractor(${API key})
  >>> # Get all completions
  >>> completions = ex.completions.get()
  >>> # Get all drill wells in Norway
  >>> flt = 'Location.Country eq "Norway"'
  >>> drilling_norway = ex.drilling.get(filter=flt)

"""

import logging

from ._api.api import RushmoreReport

logger = logging.getLogger(__name__)


class RushmoreExtractor:
    """Class used to extract raw data from the Rushmore API.

    Typical usage:
        >>> e = RushmoreExtractor(${API-KEY})
        >>> drilling_data = e.drilling.get()

    Args:
        api_key: The X-API-Key provided to Rushmore participants that
          allows access to the Rushmore API.
    """

    def __init__(
        self,
        api_key: str,
        # TODO: Check if API key can be validated on initialization
    ) -> None:
        self.abandonment = RushmoreReport("APR", api_key)
        self.completion = RushmoreReport("CPR", api_key)
        self.drilling = RushmoreReport("DPR", api_key)
