from typing import AsyncGenerator, Any

from marilyn_api.api import AsyncApi


PER_PAGE = 100


class AsyncClient:
    def __init__(self, api_root: str, headers: dict = None, settings: dict = None):
        """

        :param api_root: Example 'https://app2.mymarilyn.ru'
        :param headers: Dict headers
        :param settings: Arguments from aiohttp.client.ClientSession._request
        """
        self.api = AsyncApi(api_root=api_root, headers=headers, settings=settings)

    async def iter_statistics_detailed(
        self, body: dict = None, *, params: dict = None, headers: dict = None
    ) -> AsyncGenerator[dict, Any]:
        body = body or {}
        body['per_page'] = body.get('per_page', PER_PAGE)
        body['page'] = body.get('page', 1)
        while True:
            response, data = await self.api.call_endpoint(
                "/api/statistics/detailed", "POST", params=params, headers=headers, json=body
            )
            yield data

            if body['page'] * body['per_page'] >= data['items_total']:
                break

            body['page'] += 1

    async def iter_project_placements(
        self, project_id: int, *, params: dict = None, headers: dict = None
    ) -> AsyncGenerator[dict, Any]:
        params = params or {}
        params['per_page'] = params.get('per_page', PER_PAGE)
        params['page'] = params.get('page', 1)
        while True:
            response, data = await self.api.call_endpoint(
                f"/api/projects/{project_id}/placements", "GET", params=params, headers=headers
            )
            yield data

            if params['page'] * params['per_page'] >= data['items_total']:
                break

            params['page'] += 1
