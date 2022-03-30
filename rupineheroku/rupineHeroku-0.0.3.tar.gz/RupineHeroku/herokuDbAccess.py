import psycopg2

def connect(user,pw,host,Port,database):
    heroku_db_url = "postgres://{}:{}@{}:{}/{}".format(user,pw,host,Port,database)
    connection =  psycopg2.connect(heroku_db_url, sslmode='require')
    return connection

def fetchDataInDatabase(sql, connection):
    cursor = connection.cursor()
    cursor.execute(sql)
    result = cursor.fetchall()
    return result

def insertDataIntoDatabase(sql, connection):    
    cursor = connection.cursor()
    cursor.execute(sql)
    connection.commit()
    cursor.close()