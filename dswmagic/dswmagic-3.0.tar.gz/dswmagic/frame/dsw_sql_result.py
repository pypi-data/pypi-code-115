#!/usr/bin/env python
# -*- coding: utf-8 -*-


class DswSqlResult(object):
    def __init__(self, data, columns=None, schema=None, index=None, metadata=None):
        if columns is None and schema is None:
            raise ValueError('DswSqlResult Either columns or schema should be provided')

        self._columns = schema.columns
        self._names = [c.name for c in self._columns]
        self._types = [str(c.type) for c in self._columns]

        self._index = index
        self._data = data
        self._metadata = metadata
        self._schema = schema.columns
        self._info = {
            'index': index,
            'data': data,
            'names': self._names,
            'types': self._types,
            'columns': str(self._columns)
        }

    def _ipython_display_(self):
        from IPython.display import display
        bundle = {
            'application/json+dswsqlresult': self._info,
            'text/plain': '<dswmagic.frame.dsw_sql_result.DswSqlResult object>'
        }
        metadata = {
            'application/json': self._metadata
        }
        display(bundle, metadata=metadata, raw=True)
