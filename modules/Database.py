#!/usr/bin/python
import MySQLdb
import psycopg2
from Config import Config
class Database:

  def __init__(self):
    self.obj_config = Config()
    # Open database connection
    self.db = MySQLdb.connect(self.obj_config.host,self.obj_config.user,self.obj_config.password,self.obj_config.database)
    self.db.set_character_set(self.obj_config.charset)
    self.cursor = self.db.cursor(MySQLdb.cursors.DictCursor)
    self.cursor.execute('SET NAMES ' + self.obj_config.charset + ';')
    self.cursor.execute('SET CHARACTER SET ' + self.obj_config.charset + ';')
    self.cursor.execute('SET character_set_connection=' + self.obj_config.charset + ';')
    #self.db = psycopg2.connect(database=obj_config.database, user=obj_config.user, password=obj_config.password, host=obj_config.host, port=obj_config.port)

  def disconnect (self):
    self.db.close()

  def recInsert (self,table,records):
    #conn = self.initDB()
    arr_values = []
    db_value=") VALUES ("  
    sql_qry=""

    for key in records :
      if ( records[key] != '' ):
        if isinstance(records[key],dict) and 'func' in records[key].keys():
            if sql_qry:
              sql_qry+=",`"+key+"`"
              db_value+=","+records[key]['func']
            else :
              sql_qry+=key+"`"
              db_value+=records[key]['func']
        else:
            if sql_qry:
              sql_qry+=",`"+key+"`"
              db_value+=",%s"        
            else :
              sql_qry+=key+"`"
              db_value+="%s"            
            arr_values.append(records[key])
      
    
    sql_qry+=db_value+')'
    sql_qry="INSERT INTO "+table+"(`"+sql_qry
    print(sql_qry)
    self.cursor.execute(sql_qry,arr_values)
    self.db.commit()
    #self.db.close()
    #cursor.fetchall()
    #return $dbh->last_insert_id(undef,undef,$table,undef);
  
  def recSelect (self,table,where_dictionary,limit="",order_by="",order_type=""):
    #cursor = self.db.cursor(MySQLdb.cursors.DictCursor)
    
    sql_qry="SELECT * FROM "+table
    if where_dictionary:
        sql_qry += " WHERE "
    arr_values = []
    for key in where_dictionary:    
      if len(arr_values) > 0:      
        sql_qry+=" AND "+key+" = %s ";
      else:
        sql_qry+=key+" = %s ";        
      arr_values.append(where_dictionary[key])
    if order_by != '':    
      sql_qry+=" ORDER BY `"+order_by+"`"
      if order_type != '':      
        sql_qry+= " "+order_type+" "
    if limit != '':    
      sql_qry+=" LIMIT "+str(limit)
    #print sql_qry
    self.cursor.execute(sql_qry,arr_values)
    result = self.cursor.fetchall()
    return result

  def recCustomQuery (self,sql_qry):
    #cursor = self.db.cursor(MySQLdb.cursors.DictCursor)
    
    #print sql_qry
    self.cursor.execute(sql_qry)
    result = self.cursor.fetchall()
    return result

  def recGetCount (self,table,where_dictionary):
    #cursor = self.db.cursor(MySQLdb.cursors.DictCursor)
    
    sql_qry="SELECT COUNT(*) as cnt FROM "+table+" WHERE "
    arr_values = []
    for key in where_dictionary:    
      if len(arr_values) > 0:      
        sql_qry+=" AND "+key+" = %s ";
      else:
        sql_qry+=key+" = %s ";        
      arr_values.append(where_dictionary[key])
    self.cursor.execute(sql_qry,arr_values)
    result = self.cursor.fetchall()
    return result[0]['cnt']

  def recUpdate (self,table,records,where_dictionary):
    #cursor = self.db.cursor(MySQLdb.cursors.DictCursor)
    arr_values = []
    
    rec_value_count = 0
    sql_qry = "";
    
    for key in records :
      if isinstance(records[key],dict) and 'func' in records[key].keys() :
        if sql_qry:
            sql_qry+=",`"+key+"`="+ records[key]['func']
        else:      
            sql_qry+="`"+key+"`="+ records[key]['func']          
      else:
          if sql_qry:
            sql_qry+=",`"+key+"` = %s"    
          else:      
            sql_qry+=key+" = %s"        
          arr_values.append(records[key])    
      rec_value_count += 1
    if ( rec_value_count == 0 ) :
      return 1;    
    for key in where_dictionary:  
      if((rec_value_count- len(records))>0):      
        sql_qry+=" AND `"+key+"` = %s "    
      else:      
        sql_qry+=" WHERE `"+key+"` = %s "          
      arr_values.append(where_dictionary[key])
      rec_value_count += 1

    sql_qry = "UPDATE " + table + " SET " + sql_qry
    #print sql_qry  
    self.cursor.execute(sql_qry,arr_values)  
    self.db.commit()
    #conn.close()
  def recInsertUpdate(self,table,records,where_dictionary):
      rec_count = self.recGetCount(table,where_dictionary)
      if rec_count:
        self.recUpdate(table,records,where_dictionary)
      else:
        self.recInsert(table,records)
    
  
  def recDelete (self,table,where_dictionary):
    arr_values = []
    sql_qry = "DELETE FROM "+table;
    for key in where_dictionary:
        if len(arr_values)>0:
            sql_qry += " AND " + key + "=%s"
        else:
            sql_qry += " WHERE " + key + "=%s"
        arr_values.append(where_dictionary[key])
    
    self.cursor.execute(sql_qry,arr_values)
    self.db.commit()
  
  def getCurrentTs (self):
    self.cursor.execute( "SELECT NOW( ) AS current_ts" )
    result = self.cursor.fetchall()
    return result[0]['current_ts']