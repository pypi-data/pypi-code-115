from .errors import NoSuchItemError


class BaseApi:
    def __init__(self, api_client):
        self.api_client = api_client

    def get(self, id):
        path = f'{self.list_path}/{id}'
        data = self.api_client.get(path, auth=self.auth).get('docs')

        if not data:
            raise NoSuchItemError(f'Item with id {id} not found')

        return self.model.build(data[0], self.api_client)

    def list(self, limit=None, offset=None, page=None, sort=None, filters=[]):
        params = {}
        if limit:
            params.update(limit=limit)

        if offset:
            params.update(offset=offset)

        if page:
            params.update(page=page)

        if sort:
            direction = 'desc' if sort.startswith('-') else 'asc'
            field = sort.lstrip('-')
            params.update(sort=f'{field}:{direction}')

        data = self.api_client.get(self.list_path, params, filters, auth=self.auth)

        return Result(
            [self.model.build(obj, self.api_client) for obj in data['docs']],
            total=data.get('total'),
            limit=data.get('limit'),
            offset=data.get('offset'),
            page=data.get('page'),
            pages=data.get('pages'),
        )


class BaseModel:
    @classmethod
    def build(cls, data, api_client):
        obj = cls()
        for api_attr, attr in cls.attributes_map.items():
            setattr(obj, attr, data.get(api_attr))

        obj.api_client = api_client

        return obj


class Result:
    def __init__(self, items, total=None, limit=None, offset=None, page=None, pages=None):
        self._items = items
        self.total = total
        self.limit = limit
        self.offset = offset
        self.page = page
        self.pages = pages

    def __getitem__(self, item):
        return self._items[item]

    def __len__(self):
        return len(self._items)

    def __repr__(self):
        items_repr = ', '.join([str(x) for x in self._items[:5]])
        if len(self._items) > 5:
            items_repr += '...'

        return f'<Result: [{items_repr}]>'
