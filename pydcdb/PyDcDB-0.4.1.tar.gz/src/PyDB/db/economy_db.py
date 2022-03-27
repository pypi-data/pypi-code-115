import aiosqlite
from aiosqlite.core import Connection
from collections import namedtuple
from .errors import RecordNotFound


class EconomyDB:
    def __init__(self) -> None:
        self.CollectionTuple = namedtuple("User", ['id', 'wallet', 'bank'])

    async def connection(self) -> Connection:
        return await aiosqlite.connect('economy.db')

    async def execsql(self, query: str, entities: tuple=None) -> None:
        conn = await self.connection()
        async with conn.cursor() as cur:
            if not entities:
                await cur.execute(query)
            else:
                await cur.execute(query, entities)
            await conn.commit()
            

    async def init_db(self) -> None:
        return await self.execsql('CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, wallet INTEGER, bank INTEGER)')
    
    async def read_data(self, user_id: int) -> tuple:
        conn = await self.connection()
        async with conn.cursor() as cur:
            res = await cur.execute('SELECT id, wallet, bank FROM users where id = ?', (user_id,))
            result = await res.fetchone()
            if not result:
                return None
            return self.CollectionTuple(result[0], result[1], result[2])
        
    async def create_account(self, user_id: int, wallet: int, bank: int) -> tuple:
        res = await self.read_data(user_id)
        if not res:
            await self.execsql("INSERT INTO users(id, wallet, bank) VALUES(?, ?, ?)", (user_id,wallet,bank,))
            return self.CollectionTuple(user_id, wallet, bank)
        return self.CollectionTuple(res[0], res[1], res[2])
    
    async def update_account(self, user_id: int, *, wallet: int=None, bank: int=None) -> bool:
        user_data = await self.read_data(user_id)
        if not user_data: raise RecordNotFound
        if wallet and not bank:
            await self.execsql("UPDATE users SET wallet = ? WHERE id = ?",(wallet,user_id,))
            return True
        elif bank and not wallet:
            await self.execsql("UPDATE users SET bank = ? WHERE id = ?",(bank,user_id,))
            return True
        elif wallet and bank:
            await self.execsql("UPDATE users SET wallet = ? , bank = ? WHERE id = ?",(wallet,bank,user_id,))
            return True
        return False
