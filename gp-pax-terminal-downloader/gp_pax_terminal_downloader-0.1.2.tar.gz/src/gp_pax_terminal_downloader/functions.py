import calendar;
import time;
from mysql_helper import execute_select_for_results, execute as mysql_execute,  get_mysql_connection

def generate_file_name(prefix="pax_terminals_details"):
  return f"{prefix}_{calendar.timegm(time.gmtime())}.csv"

def insert_file_download_task(filename, db):
  if db is None: return
  time.strftime('%Y-%m-%d %H:%M:%S')
  mycursor = db.cursor()
  sql = "INSERT INTO FILE_DOWNLOAD_TASK (filename) VALUES (%s)"
  val = (filename,)
  mycursor.execute(sql, val)
  result = db.commit()
  ##print(mycursor.rowcount, "record inserted.")
  return mycursor

def update_file_download_task(filename, db, status=None, finished_at=None):
  if db is None: return  
  mycursor = db.cursor()
  sql = "UPDATE FILE_DOWNLOAD_TASK set status = %s, finished_at = %s where filename = %s"
  val = (status,finished_at,filename)
  mycursor.execute(sql, val)
  result = db.commit()
  ##print(mycursor.rowcount, "record inserted.")
  return mycursor

def get_download_tasks_from_db():
    # Get Mysql Connection
    connection = get_mysql_connection(host="51.210.248.205",user="powerbi",password="powerbi",database="powerbi_gp")
    #print(connection)
    # Get All Terminals in database
    tasks = execute_select_for_results("select * from FILE_DOWNLOAD_TASK order by started_at desc",connection)
    return tasks