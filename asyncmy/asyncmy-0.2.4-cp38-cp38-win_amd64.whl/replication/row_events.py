import datetime
import decimal
import struct

from asyncmy.charset import charset_by_name
from asyncmy.constants.FIELD_TYPE import (
    BIT,
    BLOB,
    DATE,
    DATETIME,
    DOUBLE,
    ENUM,
    FLOAT,
    GEOMETRY,
    INT24,
    JSON,
    LONG,
    LONGLONG,
    NEWDECIMAL,
    SET,
    SHORT,
    STRING,
    TIME,
    TIMESTAMP,
    TINY,
    VARCHAR,
    YEAR,
)

from .bitmap import bit_count, bit_get
from .column import Column
from .constants import (
    DATETIME2,
    DELETE_ROWS_EVENT_V2,
    TIME2,
    TIMESTAMP2,
    UPDATE_ROWS_EVENT_V2,
    WRITE_ROWS_EVENT_V2,
)
from .errors import TableMetadataUnavailableError
from .events import BinLogEvent
from .table import Table
from .utils import byte2int


class RowsEvent(BinLogEvent):
    def __init__(self, from_packet, event_size, table_map, ctl_connection, **kwargs):
        super(RowsEvent, self).__init__(
            from_packet, event_size, table_map, ctl_connection, **kwargs
        )
        self._rows = None
        self._only_tables = kwargs["only_tables"]
        self._ignored_tables = kwargs["ignored_tables"]
        self._only_schemas = kwargs["only_schemas"]
        self._ignored_schemas = kwargs["ignored_schemas"]

        # Header
        self.table_id = self._read_table_id()

        # Additional information
        try:
            self.primary_key = table_map[self.table_id].data["primary_key"]
            self.schema = self.table_map[self.table_id].schema
            self.table = self.table_map[self.table_id].table
        except KeyError:  # If we have filter the corresponding TableMap Event
            self._processed = False
            return
        schema_table = f"{self.schema}.{self.table}"

        if self._only_tables is not None and schema_table not in self._only_tables:
            self._processed = False
            return
        elif self._ignored_tables is not None and schema_table in self._ignored_tables:
            self._processed = False
            return

        if self._only_schemas is not None and self.schema not in self._only_schemas:
            self._processed = False
            return
        elif self._ignored_schemas is not None and self.schema in self._ignored_schemas:
            self._processed = False
            return

        # Event V2
        if (
            self.event_type == WRITE_ROWS_EVENT_V2
            or self.event_type == DELETE_ROWS_EVENT_V2
            or self.event_type == UPDATE_ROWS_EVENT_V2
        ):
            self.flags, self.extra_data_length = struct.unpack("<HH", self.packet.read(4))
            self.extra_data = self.packet.read(self.extra_data_length / 8)
        else:
            self.flags = struct.unpack("<H", self.packet.read(2))[0]

        # Body
        self.number_of_columns = self.packet.read_length_coded_binary()
        self.columns = self.table_map[self.table_id].columns

        if len(self.columns) == 0:  # could not read the table metadata, probably already dropped
            self.complete = False
            if self._fail_on_table_metadata_unavailable:
                raise TableMetadataUnavailableError(self.table)

    @staticmethod
    def _is_null(null_bitmap, position):
        bit = null_bitmap[int(position / 8)]
        if type(bit) is str:
            bit = ord(bit)
        return bit & (1 << (position % 8))

    def _read_column_data(self, cols_bitmap):
        """Use for WRITE, UPDATE and DELETE events.
        Return an array of column data
        """
        values = {}

        # null bitmap length = (bits set in 'columns-present-bitmap'+7)/8
        # See http://dev.mysql.com/doc/internals/en/rows-event.html
        null_bitmap = self.packet.read((bit_count(cols_bitmap) + 7) / 8)

        null_bitmap_index = 0
        nb_columns = len(self.columns)
        for i in range(0, nb_columns):
            column = self.columns[i]
            name = self.table_map[self.table_id].columns[i].name
            unsigned = self.table_map[self.table_id].columns[i].unsigned

            if bit_get(cols_bitmap, i) == 0:
                values[name] = None
                continue

            if self._is_null(null_bitmap, null_bitmap_index):
                values[name] = None
            elif column.type == TINY:
                if unsigned:
                    values[name] = struct.unpack("<B", self.packet.read(1))[0]
                else:
                    values[name] = struct.unpack("<b", self.packet.read(1))[0]
            elif column.type == SHORT:
                if unsigned:
                    values[name] = struct.unpack("<H", self.packet.read(2))[0]
                else:
                    values[name] = struct.unpack("<h", self.packet.read(2))[0]
            elif column.type == LONG:
                if unsigned:
                    values[name] = struct.unpack("<I", self.packet.read(4))[0]
                else:
                    values[name] = struct.unpack("<i", self.packet.read(4))[0]
            elif column.type == INT24:
                if unsigned:
                    values[name] = self.packet.read_uint24()
                else:
                    values[name] = self.packet.read_int24()
            elif column.type == FLOAT:
                values[name] = struct.unpack("<f", self.packet.read(4))[0]
            elif column.type == DOUBLE:
                values[name] = struct.unpack("<d", self.packet.read(8))[0]
            elif column.type == VARCHAR or column.type == STRING:
                if column.max_length > 255:
                    values[name] = self.__read_string(2, column)
                else:
                    values[name] = self.__read_string(1, column)
            elif column.type == NEWDECIMAL:
                values[name] = self.__read_new_decimal(column)
            elif column.type == BLOB:
                values[name] = self.__read_string(column.length_size, column)
            elif column.type == DATETIME:
                values[name] = self.__read_datetime()
            elif column.type == TIME:
                values[name] = self.__read_time()
            elif column.type == DATE:
                values[name] = self.__read_date()
            elif column.type == TIMESTAMP:
                values[name] = datetime.datetime.fromtimestamp(self.packet.read_uint32())

            # For new date format:
            elif column.type == DATETIME2:
                values[name] = self.__read_datetime2(column)
            elif column.type == TIME2:
                values[name] = self.__read_time2(column)
            elif column.type == TIMESTAMP2:
                values[name] = self.__add_fsp_to_time(
                    datetime.datetime.fromtimestamp(self.packet.read_int_be_by_size(4)),
                    column,
                )
            elif column.type == LONGLONG:
                if unsigned:
                    values[name] = self.packet.read_uint64()
                else:
                    values[name] = self.packet.read_int64()
            elif column.type == YEAR:
                values[name] = self.packet.read_uint8() + 1900
            elif column.type == ENUM:
                values[name] = column.enum_values[self.packet.read_uint_by_size(column.size)]
            elif column.type == SET:
                # We read set columns as a bitmap telling us which options
                # are enabled
                bit_mask = self.packet.read_uint_by_size(column.size)
                values[name] = (
                    set(val for idx, val in enumerate(column.set_values) if bit_mask & 2 ** idx)
                    or None
                )

            elif column.type == BIT:
                values[name] = self.__read_bit(column)
            elif column.type == GEOMETRY:
                values[name] = self.packet.read_length_coded_pascal_string(column.length_size)
            elif column.type == JSON:
                values[name] = self.packet.read_binary_json(column.length_size)
            else:
                raise NotImplementedError("Unknown MySQL column type: %d" % (column.type))

            null_bitmap_index += 1

        return values

    def __add_fsp_to_time(self, time, column):
        """Read and add the fractional part of time
        For more details about new date format:
        http://dev.mysql.com/doc/internals/en/date-and-time-data-type-representation.html
        """
        microsecond = self.__read_fsp(column)
        if microsecond > 0:
            time = time.replace(microsecond=microsecond)
        return time

    def __read_fsp(self, column):
        read = 0
        if column.fsp == 1 or column.fsp == 2:
            read = 1
        elif column.fsp == 3 or column.fsp == 4:
            read = 2
        elif column.fsp == 5 or column.fsp == 6:
            read = 3
        if read > 0:
            microsecond = self.packet.read_int_be_by_size(read)
            if column.fsp % 2:
                microsecond = int(microsecond / 10)
            return microsecond * (10 ** (6 - column.fsp))
        return 0

    @staticmethod
    def charset_to_encoding(name):
        charset = charset_by_name(name)
        return charset.encoding if charset else name

    def __read_string(self, size, column):
        string = self.packet.read_length_coded_pascal_string(size)
        if column.character_set_name is not None:
            encoding = self.charset_to_encoding(column.character_set_name)
            string = string.decode(encoding)
        return string

    def __read_bit(self, column):
        """Read MySQL BIT type"""
        resp = ""
        for byte in range(0, column.bytes):
            current_byte = ""
            data = self.packet.read_uint8()
            if byte == 0:
                if column.bytes == 1:
                    end = column.bits
                else:
                    end = column.bits % 8
                    if end == 0:
                        end = 8
            else:
                end = 8
            for bit in range(0, end):
                if data & (1 << bit):
                    current_byte += "1"
                else:
                    current_byte += "0"
            resp += current_byte[::-1]
        return resp

    def __read_time(self):
        time = self.packet.read_uint24()
        date = datetime.timedelta(
            hours=int(time / 10000),
            minutes=int((time % 10000) / 100),
            seconds=int(time % 100),
        )
        return date

    def __read_time2(self, column):
        """TIME encoding for nonfractional part:

         1 bit sign    (1= non-negative, 0= negative)
         1 bit unused  (reserved for future extensions)
        10 bits hour   (0-838)
         6 bits minute (0-59)
         6 bits second (0-59)
        ---------------------
        24 bits = 3 bytes
        """
        data = self.packet.read_int_be_by_size(3)

        sign = 1 if self._read_binary_slice(data, 0, 1, 24) else -1
        if sign == -1:
            # negative integers are stored as 2's compliment
            # hence take 2's compliment again to get the right value.
            data = ~data + 1

        t = datetime.timedelta(
            hours=sign * self._read_binary_slice(data, 2, 10, 24),
            minutes=self._read_binary_slice(data, 12, 6, 24),
            seconds=self._read_binary_slice(data, 18, 6, 24),
            microseconds=self.__read_fsp(column),
        )
        return t

    def __read_date(self):
        time = self.packet.read_uint24()
        if time == 0:  # nasty mysql 0000-00-00 dates
            return None

        year = (time & ((1 << 15) - 1) << 9) >> 9
        month = (time & ((1 << 4) - 1) << 5) >> 5
        day = time & ((1 << 5) - 1)
        if year == 0 or month == 0 or day == 0:
            return None

        date = datetime.date(year=year, month=month, day=day)
        return date

    def __read_datetime(self):
        value = self.packet.read_uint64()
        if value == 0:  # nasty mysql 0000-00-00 dates
            return None

        date = value / 1000000
        time = int(value % 1000000)

        year = int(date / 10000)
        month = int((date % 10000) / 100)
        day = int(date % 100)
        if year == 0 or month == 0 or day == 0:
            return None

        date = datetime.datetime(
            year=year,
            month=month,
            day=day,
            hour=int(time / 10000),
            minute=int((time % 10000) / 100),
            second=int(time % 100),
        )
        return date

    def __read_datetime2(self, column):
        """DATETIME

        1 bit  sign           (1= non-negative, 0= negative)
        17 bits year*13+month  (year 0-9999, month 0-12)
         5 bits day            (0-31)
         5 bits hour           (0-23)
         6 bits minute         (0-59)
         6 bits second         (0-59)
        ---------------------------
        40 bits = 5 bytes
        """
        data = self.packet.read_int_be_by_size(5)
        year_month = self._read_binary_slice(data, 1, 17, 40)
        try:
            t = datetime.datetime(
                year=int(year_month / 13),
                month=year_month % 13,
                day=self._read_binary_slice(data, 18, 5, 40),
                hour=self._read_binary_slice(data, 23, 5, 40),
                minute=self._read_binary_slice(data, 28, 6, 40),
                second=self._read_binary_slice(data, 34, 6, 40),
            )
        except ValueError:
            self.__read_fsp(column)
            return None
        return self.__add_fsp_to_time(t, column)

    def __read_new_decimal(self, column):
        """Read MySQL's new decimal format introduced in MySQL 5"""

        # This project was a great source of inspiration for
        # understanding this storage format.
        # https://github.com/jeremycole/mysql_binlog

        digits_per_integer = 9
        compressed_bytes = [0, 1, 1, 2, 2, 3, 3, 4, 4, 4]
        integral = column.precision - column.decimals
        uncomp_integral = int(integral / digits_per_integer)
        uncomp_fractional = int(column.decimals / digits_per_integer)
        comp_integral = integral - (uncomp_integral * digits_per_integer)
        comp_fractional = column.decimals - (uncomp_fractional * digits_per_integer)

        # Support negative
        # The sign is encoded in the high bit of the the byte
        # But this bit can also be used in the value
        value = self.packet.read_uint8()
        if value & 0x80 != 0:
            res = ""
            mask = 0
        else:
            mask = -1
            res = "-"
        self.packet.unread(struct.pack("<B", value ^ 0x80))

        size = compressed_bytes[comp_integral]
        if size > 0:
            value = self.packet.read_int_be_by_size(size) ^ mask
            res += str(value)

        for i in range(0, uncomp_integral):
            value = struct.unpack(">i", self.packet.read(4))[0] ^ mask
            res += "%09d" % value

        res += "."

        for i in range(0, uncomp_fractional):
            value = struct.unpack(">i", self.packet.read(4))[0] ^ mask
            res += "%09d" % value

        size = compressed_bytes[comp_fractional]
        if size > 0:
            value = self.packet.read_int_be_by_size(size) ^ mask
            res += "%0*d" % (comp_fractional, value)

        return decimal.Decimal(res)

    @staticmethod
    def _read_binary_slice(binary, start, size, data_length):
        """
        Read a part of binary data and extract a number
        binary: the data
        start: From which bit (1 to X)
        size: How many bits should be read
        data_length: data size
        """
        binary = binary >> data_length - (start + size)
        mask = (1 << size) - 1
        return binary & mask

    def _fetch_rows(self):
        self._rows = []

        if not self.complete:
            return

        while self.packet.read_bytes < self.event_size:
            self._rows.append(self._fetch_one_row())

    @property
    def rows(self):
        if self._rows is None:
            self._fetch_rows()
        return self._rows


class DeleteRowsEvent(RowsEvent):
    """This event is trigger when a row in the database is removed

    For each row you have a hash with a single key: values which contain the data of the removed line.
    """

    def __init__(self, from_packet, event_size, table_map, ctl_connection, **kwargs):
        super(DeleteRowsEvent, self).__init__(
            from_packet, event_size, table_map, ctl_connection, **kwargs
        )
        if self._processed:
            self.columns_present_bitmap = self.packet.read((self.number_of_columns + 7) / 8)

    def _fetch_one_row(self):
        return {"values": self._read_column_data(self.columns_present_bitmap)}


class WriteRowsEvent(RowsEvent):
    """This event is triggered when a row in database is added

    For each row you have a hash with a single key: values which contain the data of the new line.
    """

    def __init__(self, from_packet, event_size, table_map, ctl_connection, **kwargs):
        super(WriteRowsEvent, self).__init__(
            from_packet, event_size, table_map, ctl_connection, **kwargs
        )
        if self._processed:
            self.columns_present_bitmap = self.packet.read((self.number_of_columns + 7) / 8)

    def _fetch_one_row(self):
        return {"values": self._read_column_data(self.columns_present_bitmap)}


class UpdateRowsEvent(RowsEvent):
    """This event is triggered when a row in the database is changed

    For each row you got a hash with two keys:
        * before_values
        * after_values

    Depending of your MySQL configuration the hash can contains the full row or only the changes:
    http://dev.mysql.com/doc/refman/5.6/en/replication-options-binary-log.html#sysvar_binlog_row_image
    """

    def __init__(self, from_packet, event_size, table_map, ctl_connection, **kwargs):
        super(UpdateRowsEvent, self).__init__(
            from_packet, event_size, table_map, ctl_connection, **kwargs
        )
        if self._processed:
            # Body
            self.columns_present_bitmap = self.packet.read((self.number_of_columns + 7) / 8)
            self.columns_present_bitmap2 = self.packet.read((self.number_of_columns + 7) / 8)

    def _fetch_one_row(self):
        row = {
            "before_values": self._read_column_data(self.columns_present_bitmap),
            "after_values": self._read_column_data(self.columns_present_bitmap2),
        }

        return row


class TableMapEvent(BinLogEvent):
    """This event describes the structure of a table.
    It's sent before a change happens on a table.
    An end user of the lib should have no usage of this
    """

    def __init__(self, from_packet, event_size, table_map, connection, **kwargs):
        super(TableMapEvent, self).__init__(
            from_packet, event_size, table_map, connection, **kwargs
        )
        self._only_tables = kwargs["only_tables"]
        self._ignored_tables = kwargs["ignored_tables"]
        self._only_schemas = kwargs["only_schemas"]
        self._ignored_schemas = kwargs["ignored_schemas"]
        self._freeze_schema = kwargs["freeze_schema"]
        self._table_map = table_map
        # Post-Header
        self.table_id = self._read_table_id()

        if self.table_id in table_map and self._freeze_schema:
            self._processed = False
            return

        self.flags = struct.unpack("<H", self.packet.read(2))[0]

        # Payload
        self.schema_length = byte2int(self.packet.read(1))
        self.schema = self.packet.read(self.schema_length).decode()
        self.packet.advance(1)
        self.table_length = byte2int(self.packet.read(1))
        self.table_name = self.packet.read(self.table_length).decode()
        schema_table = f"{self.schema}.{self.table_name}"
        if self._only_tables is not None and schema_table not in self._only_tables:
            self._processed = False
            return
        elif self._ignored_tables is not None and schema_table in self._ignored_tables:
            self._processed = False
            return

        if self._only_schemas is not None and self.schema not in self._only_schemas:
            self._processed = False
            return
        elif self._ignored_schemas is not None and self.schema in self._ignored_schemas:
            self._processed = False
            return

        self.packet.advance(1)
        self.column_count = self.packet.read_length_coded_binary()
        self.columns = []

    @property
    def table(self):
        return self._table

    async def init(self):
        if self.table_id in self._table_map:
            self.column_schemas = self._table_map[self.table_id].column_schemas
        else:
            self.column_schemas = await (
                await self._connection._get_table_information(self.schema, self.table_name)
            )
        ordinal_pos_loc = 0

        if len(self.column_schemas) != 0:
            # Read columns meta data
            column_types = list(self.packet.read(self.column_count))
            self.packet.read_length_coded_binary()
            for i in range(0, len(column_types)):
                column_type = column_types[i]
                try:
                    column_schema = self.column_schemas[ordinal_pos_loc]

                    # only acknowledge the column definition if the iteration matches with ordinal position of
                    # the column. this helps in maintaining support for restricted columnar access
                    if i != (column_schema["ORDINAL_POSITION"] - 1):
                        # raise IndexError to follow the workflow of dropping columns which are not matching the
                        # underlying table schema
                        raise IndexError

                    ordinal_pos_loc += 1
                except IndexError:
                    # this a dirty hack to prevent row events containing columns which have been dropped prior
                    # to pymysqlreplication start, but replayed from binlog from blowing up the service.
                    # TODO: this does not address the issue if the column other than the last one is dropped
                    column_schema = {
                        "COLUMN_NAME": "__dropped_col_{i}__".format(i=i),
                        "COLLATION_NAME": None,
                        "CHARACTER_SET_NAME": None,
                        "COLUMN_COMMENT": None,
                        "COLUMN_TYPE": "BLOB",  # we don't know what it is, so let's not do anything with it.
                        "COLUMN_KEY": "",
                    }
                col = Column(column_type, column_schema, self.packet)
                self.columns.append(col)

        self._table = Table(
            self.column_schemas,
            self.table_id,
            self.schema,
            self.table_name,
            self.columns,
        )
