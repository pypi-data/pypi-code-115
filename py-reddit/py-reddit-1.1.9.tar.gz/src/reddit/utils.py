import inspect


class AsyncMeta(type):
    async def __call__(self, *args, **kwargs):
        obb = object.__new__(self)
        fn = obb.__init__(*args, **kwargs)
        if inspect.isawaitable(fn):
           await fn
        return obb
