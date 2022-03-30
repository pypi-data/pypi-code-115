import mysql.connector

def get_mysql_connection(host, user,password=None,database=None):
    return mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )

def execute(sql, db):
    if db is None: return None        
    cursor = db.cursor()
    cursor.execute(sql)
    return cursor
    
    
def execute_select_for_results(sql, db):
    if db is None: return []
    cursor = execute(sql, db)
    return cursor.fetchall()    
