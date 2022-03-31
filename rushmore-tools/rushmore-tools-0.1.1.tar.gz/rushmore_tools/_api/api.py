"""API functions and related classes for RushmoreExtractor."""

import logging
from typing import Any, Dict, List, Optional, TypedDict, Union

import requests

logger = logging.getLogger(__name__)


class RushmoreResponse(TypedDict):
    """Type class for Rushmore Response."""

    TotalWells: Optional[int]
    TotalPages: Optional[int]
    PageInfo: Optional[Dict[str, Any]]
    Data: Optional[List[Any]]


class RushmoreReport:
    """Basic class for adding reports as subclasses to RushmoreExtractor."""

    def __init__(self, report_name: str, api_key: str, page_size: Optional[int] = 1000):
        self.api_key = api_key
        self.report_name = report_name
        self._page_size = page_size

    @property
    def page_size(self):
        """For making page_size an editable property."""
        return self._page_size

    @page_size.setter
    def page_size(self, value):
        if value > 0 and isinstance(value, int):
            self._page_size = value
        elif not isinstance(value, int):
            raise TypeError("Incorrect type. Specify a positive integer for page size.")
        else:
            raise ValueError(
                "Incorrect value. Specify a positive integer for page size."
            )

    def get(
        self,
        data_filter: Optional[str] = None,
        full_response: Optional[bool] = True,
        max_pages: Optional[int] = None,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Retrieves all raw data from relevant Rushmore Review.

        Args:
            data_filter: Filtering string according to API specification.
            full_response: Pass True to retrieve full response from Rushmore.
              False retrieves only the well data list component.
            max_pages: Optional argument to reduce number of pages retrieved
              from Rushmore, for testing purposes.

        Returns:
            List of dicts where each dict describes an entry in the Rushmore
            Review.

        """

        return get_data(
            api_key=self.api_key,
            report_name=self.report_name,
            full_response=full_response,
            page_size=self.page_size,
            data_filter=data_filter,
            max_pages=max_pages,
        )


def get_data_page(
    api_key: str,
    report_name: str,
    page_size: int,
    api_version: Optional[str] = "0.1",
    page: Optional[int] = 1,
    data_filter: Optional[str] = None,
) -> RushmoreResponse:
    """Queries data from Rushmore.

    Args:
        page_size: Number of rows requested per page.
        page: The page number that is requested.
        data_filter: Custom filters for what data to include.

    Returns:
        One page of data from Rushmore as a JSON serializable
        dictionary with keys according to the standard API payload.
    """
    # Rushmore API uses X-API-key authorization.
    header = {"X-API-key": api_key}
    base_url = (
        f"https://data-api.rushmorereviews.com/v{api_version}/wells/{report_name}"
    )
    url = f"{base_url}?page={page}&pageSize={page_size}"
    if data_filter:
        url = f"{url}&filter={data_filter}"

    response = requests.get(
        url=url,
        headers=header,
    )

    # Checks for non-2xx responses
    response.raise_for_status()

    return response.json()


def _check_response(response: Dict[str, Any]) -> None:
    """Simple check for overflow error in response.

    Args:
        response: Rushmore API response.

    Raises:
        ValueError if page size causes response to overflow.
    """
    logger.debug("Checking response for error messages.")
    try:
        response["fault"]
    except KeyError:
        pass
    else:
        error: str = response["fault"]["faultstring"]
        if error == "Body buffer overflow":
            raise ValueError("Response too large. Reduce page size.")
        raise Exception(f"Error was thrown: {error}.")
    try:
        response["error"]
    except KeyError:
        pass
    else:
        error: str = response["error_description"]
        raise Exception(f"Error was thrown: {error}.")


def get_data(
    api_key: str,
    report_name: str,
    full_response: Optional[bool] = True,
    page_size: Optional[int] = 1000,
    data_filter: Optional[str] = None,
    max_pages: Optional[int] = None,
) -> Union[RushmoreResponse, List[Dict[str, Any]]]:
    """Queries all data from Rushmore.

    For the instantiated performance review, iterates through all
    available pages to query an unfiltered list of rows.

    TODO: Look into improving looping logic.

    Args:
        data_filter: Submit a well-formed filter string according to the Rushmore
            API specification. This filter will be passed to the API.

    Returns:
        A list of dicts that each describe a well in the provided
        performance review.

    Raises:
        ValueError if page size exceeds maximum allowable.
        Exception for other API errors.
    """
    output: Optional[RushmoreResponse] = None
    page = 1
    while True:
        logger.info(f"Fetching page {page} from {report_name.upper()}")
        response = get_data_page(
            api_key=api_key,
            report_name=report_name,
            page_size=page_size,
            page=page,
            data_filter=data_filter,
        )

        # Response checker catches error / failure responses
        _check_response(response)

        logger.info(f"Fetched {len(response['Data'])} rows.")
        if output:
            output["Data"].extend(  # pylint: disable=unsubscriptable-object
                response["Data"]
            )
        else:
            output = response

        # Determine number of pages to fetch.
        # TODO: Revise logic if lightweight API calls are available.
        if not max_pages:
            num_pages = response["TotalPages"]
        else:
            num_pages = min(max_pages, response["TotalPages"])

        if num_pages > page:
            page += 1
        else:
            logger.info(f"Extraction complete. {len(output['Data']):,} rows fetched.")
            if full_response:
                return output
            return output["Data"]
