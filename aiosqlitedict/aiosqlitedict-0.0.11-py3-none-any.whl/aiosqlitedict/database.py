import aiosqlite


class Connect:
    """
    Instantiate a conversion to and from sqlite3 database and python dictionary.
    """

    def __init__(self, database_name: str, id_column: str):
        self.database_name = database_name
        self.id_column = id_column

    async def to_dict(self, table_name, my_id, *column_names: str):
        """
        Convert a sqlite3 table into a python dictionary.
        :param table_name: The name of the database table.
        :type table_name: str

        :param my_id: The id of the row.
        :type my_id: int

        :param column_names: The column name.
        :type column_names: str

        :return: The dictionary.
        :rtype: dict
        """
        async with aiosqlite.connect(self.database_name) as db:
            async with db.cursor() as cursor:

                table_name = table_name.replace("'", "").replace('"', "")
                data = {}
                columns = str(column_names).replace("(", "").replace(
                    ")", "").replace('"', "").replace("'", "")
                columns = columns.replace(
                    columns[-1], "") if columns.endswith(",") else columns
                getID = await cursor.execute(
                    f"SELECT ? FROM ? WHERE {self.id_column} = ?", (columns, table_name, my_id, ))
                values = await getID.fetchone()
                values = list(values)
                for v in range(len(values)):
                    if str(values[v]).startswith("["):
                        values[v] = values[v].replace("[", "").replace(']', "").replace(" ' ", "").\
                            replace(' " ', "").replace(" '", "").replace(' "', "").replace("' ", "").\
                            replace('" ', "").replace("'", "").replace('"', "").replace(",", "|")
                        values[v] = values[v].split("|")
                    else:
                        continue
                for i in range(len(column_names)):
                    data[column_names[i]] = values[i]
                return data

    #  To push data to db

    async def to_sql(self, table_name, my_id, dictionary: dict):
        """
        Convert a python dictionary into a sqlite3 table.
        :param table_name: The name of the database table.
        :type table_name: str

        :param my_id: The id of the row.
        :type my_id: int

        :param dictionary: The dictionary object.
        :type dictionary: dict

        :return: The SQLite3 Table.
        :rtype: sqlite
        """
        async with aiosqlite.connect(self.database_name) as db:
            async with db.cursor() as cursor:
                table_name = table_name.replace("'", "").replace('"', "")
                getUser = await cursor.execute(f"SELECT ? FROM ? WHERE {self.id_column} = ?", (self.id_column, table_name, my_id, ))
                isUserExists = await getUser.fetchone()
                if isUserExists:
                    for key, val in dictionary.items():
                        key = key.replace("'", "").replace('"', "")
                        val = str(val) if str(val).startswith("[") else val
                        await cursor.execute(f"UPDATE ? SET {key} = ? WHERE {self.id_column} = ?", (table_name, val, my_id,))
                else:
                    await cursor.execute(f"INSERT INTO ? ({self.id_column}) VALUES ( ? )", (table_name, my_id, ))
                    for key, val in dictionary.items():
                        key = key.replace("'", "").replace('"', "")
                        val = str(val) if str(val).startswith("[") else val
                        await cursor.execute(f"UPDATE ? SET {key} = ? WHERE {self.id_column} = ?", (table_name, val, my_id,))

            await db.commit()

    async def select(self, table_name, column_name: str, limit=None, order_by=None, ascending=True):
        """
        Select a column from the table.
        :param table_name: The name of the database table.
        :type table_name: str

        :param column_name: The column name.
        :type column_name: str

        :param limit:
        :rtype: int

        :param order_by:
        :rtype: str

        :param ascending:
        :rtype: bool

        :return: The list.
        :rtype: list
        """
        async with aiosqlite.connect(self.database_name) as db:
            async with db.cursor() as cursor:

                table_name = table_name.replace("'", "").replace('"', "")
                column = str(column_name).replace("(", "").replace(
                    ")", "").replace('"', "").replace("'", "")
                column = column.replace(
                    column[-1], "") if column.endswith(",") else column
                if order_by is None:
                    order_by = column
                if limit is not None and order_by is None:
                    getValues = await cursor.execute(f"SELECT ? FROM ? LIMIT ?", (column, table_name, limit,))
                elif limit is None and order_by is not None and ascending is True:
                    getValues = await cursor.execute(f"SELECT ? FROM ? ORDER BY ? ASC", (column, table_name, order_by,))
                elif limit is None and order_by is not None and ascending is not True:
                    getValues = await cursor.execute(f"SELECT ? FROM ? ORDER BY ? DESC", (column, table_name, order_by,))
                elif limit is not None and order_by is not None and ascending is True:
                    getValues = await cursor.execute(f"SELECT ? FROM ? ORDER BY ? ASC LIMIT ?", (column, table_name, order_by, limit,))
                elif limit is not None and order_by is not None and ascending is not True:
                    getValues = await cursor.execute(f"SELECT ? FROM ? ORDER BY ? DESC LIMIT ?", (column, table_name, order_by, limit,))
                values = await getValues.fetchone()
                values = list(values)

                return values
