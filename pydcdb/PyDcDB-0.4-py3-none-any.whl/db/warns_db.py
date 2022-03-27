import aiosqlite
from aiosqlite.core import Connection
from collections import namedtuple
from .errors import RecordNotFound


class WarnDB:
    def __init__(self) -> None:
        self.CollectionTuple = namedtuple("User", ['id', 'warns'])

    async def connection(self) -> Connection:
        return await aiosqlite.connect('warns.db')

    async def execsql(self, query: str, entities: tuple=None) -> None:
        conn = await self.connection()
        async with conn.cursor() as cur:
            if not entities:
                await cur.execute(query)
            else:
                await cur.execute(query, entities)
            await conn.commit()

    async def init_db(self) -> None:
        await self.execsql('CREATE TABLE IF NOT EXISTS warnings(id INTEGER PRIMARY KEY, warns INTEGER')

    async def read_data(self, user_id: int) -> tuple:
        conn = await self.connection()
        async with conn.cursor() as cur:
            res = await cur.execute('SELECT id, warns FROM warnings where id = ?', (user_id,))
            result = await res.fetchone()
            if not result: return None
            return self.CollectionTuple(result[0], result[1])
    
    async def create_account(self, user_id: int, warnings: int) -> tuple:
        res = await self.read_data(user_id)
        if not res:
            await self.execsql("INSERT INTO warnings(id, warns) VALUES(?, ?)", (user_id,warnings,))
            return self.CollectionTuple(user_id, warnings)
        return self.CollectionTuple(res[0], res[1])

    async def update_account(self, user_id: int, *, warnings: int=None) -> bool:
        user_data = await self.read_data(user_id)
        if not user_data: raise RecordNotFound
        if warnings:
            await self.execsql("UPDATE warnings SET warns = ? WHERE id = ?",(warnings,user_id,))
            return True
        return False
        