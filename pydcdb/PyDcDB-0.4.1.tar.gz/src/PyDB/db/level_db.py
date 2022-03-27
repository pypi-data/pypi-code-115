import aiosqlite
from aiosqlite.core import Connection
from collections import namedtuple
from .errors import RecordNotFound


class LevelDB:
    def __init__(self) -> None:
        self.CollectionTuple = namedtuple("User", ['id', 'xp', 'level'])

    async def connection(self) -> Connection:
        return await aiosqlite.connect('level.db')

    async def execsql(self, query: str, entities: tuple=None) -> None:
        conn = await self.connection()
        async with conn.cursor() as cur:
            if not entities:
                await cur.execute(query)
            else:
                await cur.execute(query, entities)
            await conn.commit()

    async def init_db(self) -> None:
        await self.execsql('CREATE TABLE IF NOT EXISTS ranks(id INTEGER PRIMARY KEY, xp INTEGER, level INTEGER)')
        
    async def read_data(self, user_id: int) -> tuple:
        conn = await self.connection()
        async with conn.cursor() as cur:
            res = await cur.execute('SELECT id, xp, level FROM ranks where id = ?', (user_id,))
            result = await res.fetchone()
            if not result: return None
            return self.CollectionTuple(result[0], result[1], result[2])
    
    async def create_account(self, user_id: int, xp: int, level: int) -> tuple:
            res = await self.read_data(user_id)
            if not res:
                await self.execsql("INSERT INTO ranks(id, xp, level) VALUES(?, ?, ?)", (user_id,xp,level,))
                return self.CollectionTuple(user_id, xp, level)
            return self.CollectionTuple(res[0], res[1], res[2])

    async def update_account(self, user_id: int, *, xp: int=None, level: int=None) -> bool:
        user_data = await self.read_data(user_id)
        if not user_data: raise RecordNotFound
        if xp and not level:
            await self.execsql("UPDATE ranks SET xp = ? WHERE id = ?",(xp,user_id,))
            return True
        elif level and not xp:
            await self.execsql("UPDATE ranks SET level = ? WHERE id = ?",(level,user_id,))
            return True
        elif xp and level:
            await self.execsql("UPDATE ranks SET xp = ? , level = ? WHERE id = ?",(xp,level,user_id,))
            return True
        return False
