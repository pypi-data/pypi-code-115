"""
Recursive Scroll and Scrape module.
"""
from functools import partial
from typing import Callable, Optional

# pylint: disable=too-few-public-methods
from tq_scroll_scrape.scroll_and_scrape import ScrollAndScrape


class RecursiveScrollScrape:
    """
    The RecursiveScrollScrape class manages the scrolling and recursive downloading of pages.
    This class is built on the ScrollScrape class (https://pypi.org/project/tq-scroll-scrape/).

    The typical use case is downloading site pages that are paginated, i.e. starting at the
    root page, getting the next page url, downloading that page, and so on until the
    end is reached.

    The sample app is sample_app.py demonstrates this using Trulia's site.
    """

    def __init__(self, driver_path: str):
        self.scroll_scraper = ScrollAndScrape(driver_path)

    def download(
            self,
            url: str,
            on_after_download: Optional[Callable[[str], None]],
            get_next_url: Callable[[str], Optional[str]],
            sleep_after_scroll_seconds: int = 2,
            **kwargs):
        """
        :param url: The url to download.
        :param on_after_download: An optional callback to execute after the page downloads.
        :param get_next_url: A required callback to execute that returns the url of the next page.
        :param sleep_after_scroll_seconds: The time in seconds to sleep after each scroll event.
        :param kwargs: Additional keyword arguments to the function.
        See https://pypi.org/project/tq-scroll-scrape/ for details.
        """
        self.scroll_scraper.download(
            url,
            partial(self._download_recursive, on_after_download, get_next_url),
            sleep_after_scroll_seconds,
            **kwargs)

    def _download_recursive(
            self,
            on_after_download: Optional[Callable[[str], None]],
            get_next_url: Callable[[str], Optional[str]],
            content: str,
            sleep_after_scroll_seconds: int = 2,
            **kwargs):
        on_after_download(content)
        next_url = get_next_url(content)

        if next_url is None:
            return

        self.scroll_scraper.driver.close()
        self.scroll_scraper.driver.quit()

        self.scroll_scraper.download(
            next_url,
            partial(self._download_recursive, on_after_download, get_next_url),
            sleep_after_scroll_seconds,
            **kwargs)
