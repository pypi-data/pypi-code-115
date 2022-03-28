import asyncio
import json
import sys

from pykostalpiko.dxs.entries import DxsEntries
from pykostalpiko.inverter import Inverter


async def async_main() -> None:
    inv = Inverter(ip=sys.argv[1])
    values = await inv.async_fetch_all()
    print(json.dumps(values, indent=4))

if __name__ == "__main__":
    asyncio.run(async_main())
