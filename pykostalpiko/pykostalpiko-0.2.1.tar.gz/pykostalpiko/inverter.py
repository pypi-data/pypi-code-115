import asyncio
from typing import Any, Optional
import requests
from pykostalpiko.dxs.entries import DxsEntries
from pykostalpiko.constants import API_ENDPOINT


class Inverter:
    def __init__(self, ip: str, username: Optional[str] = None, password: Optional[str] = None):
        self._ip = ip
        self._data = {}

    def get(self, entry: DxsEntries) -> Any:
        if (self._data is None):
            raise NoDataFetched('No data fetched yet')

        try:
            return self._data[entry.name]
        except Exception:
            raise NoDataForEntry(f'No data found for {entry.name}')

    async def async_fetch(self, *entries: DxsEntries) -> dict:
        # Spread the entries into groups of 10 to avoid too many dxsEntries
        entries_paged = [entries[i:i + 10] for i in range(0, len(entries), 10)]

        for req in asyncio.as_completed([self.async_request(*entries) for entries in entries_paged]):
            # Wait for the request to complete
            res = await req

            # Combine existing data with newly fetched data
            self._data = {**self._data, **res}

        return self._data

    async def async_request(self, *entries: DxsEntries) -> dict:
        # Check amount of requested entries
        if (len(entries) == 0):
            raise Exception('No entries specified')
        elif (len(entries) > 10):
            raise Exception('Too many entries specified')

        # Preapre URL and parameters
        url = f'http://{self._ip}{API_ENDPOINT}?'
        for entry in entries:
            url += f'dxsEntries={entry.value}&'

        # Request the data
        try:
            r = requests.get(url)
        except Exception:
            raise ConnectionError('Could not fetch data')

        # Format and return the data
        json = r.json()
        return self.__format_response(json)

    async def async_fetch_all(self) -> dict:
        return await self.async_fetch(*DxsEntries.__members__.values())

    def __format_response(self, jsn) -> dict:
        new = {}
        entries = jsn['dxsEntries']

        for entry in entries:
            new[DxsEntries(entry['dxsId']).name] = entry['value']

        return new


class NoDataFetched(Exception):
    pass


class NoDataForEntry(Exception):
    pass
