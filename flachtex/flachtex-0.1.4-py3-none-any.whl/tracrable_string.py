class OriginOfRange:
    def __init__(self, begin, end, origin, offset: int = 0):
        self.origin = origin
        self.begin = begin
        self.end = end
        self.offset = offset

    def __len__(self):
        return self.end - self.begin

    def cut_front(self, n: int):
        """
        All indices <n shall be cut off.
        :param n: New first position
        :return: Modified OriginOfRange corresponding to new beginning. If this origin is
        no longer contained, return None.
        """
        if self.end <= n:
            return None
        if self.begin <= n < self.end:
            offset_ = self.offset + (n - self.begin)
        else:
            offset_ = self.offset
        return OriginOfRange(max(0, self.begin - n), self.end - n, self.origin, offset_)

    def cut_back(self, n: int):
        """
        All indices >=n shall be cut off.
        :param n: New end index
        :return: Modified OriginOFRange corresponding to shortend string. If this origin is
        no longer contained, return None.
        """
        if self.begin >= n:
            return None
        return OriginOfRange(self.begin, min(self.end, n), self.origin, self.offset)

    def slice(self, begin, end):
        # cutting of the back does not change the indices and should be done first.
        shortened = self.cut_back(end)
        if shortened:
            return shortened.cut_front(begin)
        return shortened

    def __lt__(self, other):
        return self.begin < other.begin

    def get_offset(self, i):
        if i not in self:
            raise ValueError("Index is not within this origin range.")
        return self.offset + (i - self.begin)

    def __contains__(self, item):
        return self.begin <= item < self.end

    def move(self, n):
        return OriginOfRange(self.begin + n, self.end + n, self.origin, self.offset)


class TraceableString:
    def __init__(self, content: str, origin, offset: int = 0):
        self.content = content
        self.origins = [OriginOfRange(0, len(content), origin, offset)]

    def __len__(self):
        return len(self.content)

    def __str__(self):
        return self.content

    def _normalize_slice(self, s: slice):
        start = s.start if s.start is not None else 0
        start = start if start >= 0 else len(self) - start
        stop = s.stop if s.stop is not None else len(self)
        stop = stop if stop >= 0 else len(self) - stop
        if stop > len(self):
            raise IndexError()
        if s.step is not None and s.step != 1:
            raise NotImplementedError("Slicing with steps is not supported.")
        return start, stop

    def __getitem__(self, item):
        if isinstance(item, slice):
            content = self.content[item]
            start, stop = self._normalize_slice(item)
            origins = (o.slice(start, stop) for o in self.origins)
            origins = [o for o in origins if o is not None]
            ts = TraceableString(content, None)
            ts.origins = origins
            return ts
        return self.content[item]

    def get_origin(self, i):
        if i >= len(self):
            raise IndexError()
        for o in self.origins:
            if i in o:
                return o.origin, o.get_offset(i)

    def to_json(self):
        return {
            "content": self.content,
            "origins": [{"begin": o.begin,
                         "end": o.end,
                         "origin": str(o.origin),
                         "offset": o.offset}
                        for o in self.origins]
        }

    def __add__(self, other):
        ts = TraceableString(self.content + other.content, None)
        ts.origins = self.origins + [o.move(len(self)) for o in other.origins]
        return ts
