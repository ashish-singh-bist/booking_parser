import pymongo
from pymongo import MongoClient
from Config import Config
import datetime
from bson.objectid import ObjectId

class MongoDatabase:

  def __init__(self):
    self.obj_config = Config()
    # Open database connection
    #connection_string = "mongodb://" + self.obj_config.mongo_host + ":" + self.obj_config.mongo_port + "/"
    self.client = MongoClient(self.obj_config.mongo_host, int(self.obj_config.mongo_port), maxPoolSize=2000)
    self.db = self.client[self.obj_config.mongo_database]
    
  def connect (self):
    # Open database connection
    #connection_string = "mongodb://" + self.obj_config.mongo_host + ":" + self.obj_config.mongo_port + "/"
    MongoClient(self.obj_config.mongo_host, int(self.obj_config.mongo_port), maxPoolSize=2000)
    self.db = self.client[self.obj_config.mongo_database] 

  def disconnect (self):    
    self.client.close()

  def recInsert (self,table,data_array):
    timestamp = datetime.datetime.now()
    for idx, item in enumerate(data_array):
        data_array[idx]['created_at'] = timestamp
        data_array[idx]['updated_at'] = timestamp
    collection = self.db[table]
    result = collection.insert_many(data_array)
    return result.inserted_ids  

  def recUpdate (self,table,data_dictionary,where_dictionary,update_ts_flag=True):
    if update_ts_flag:      
      data_dictionary['updated_at'] = datetime.datetime.now()
    collection = self.db[table]
    result = collection.update(where_dictionary,{ '$set': data_dictionary }, upsert=False, multi=False)
    return result

  def recUpdateCustome (self,table,data_dictionary,where_dictionary):
    #timestamp = datetime.datetime.now()
    #data_dictionary['updated_at'] = timestamp
    collection = self.db[table]
    result = collection.update(where_dictionary, data_dictionary, upsert=False, multi=True)
    return result
        
  def recUpdateArrayFilters (self,table,data_dictionary,where_dictionary,arr_filter=None):    
    collection = self.db[table]    
    result = collection.update_many(where_dictionary, data_dictionary, upsert=False, bypass_document_validation=False, collation=None, array_filters=arr_filter, session=None)
    return result

  def recInsertUpdate (self,table,data_dictionary,where_dictionary):
    collection = self.db[table]
    result = collection.update(where_dictionary,{ '$set': data_dictionary }, upsert=True, multi=False)
    return result
  
  def recSelect (self,table,selected_column_dictionary = None,where_dictionary = None,limit=10000,order_by=None,order_type=None):
    collection = self.db[table]
    if order_by and order_type:
      if order_type == "ASC":
        result = collection.find(where_dictionary,selected_column_dictionary).limit(limit).sort([(order_by, pymongo.ASCENDING)])
      else:
        result = collection.find(where_dictionary,selected_column_dictionary).limit(limit).sort([(order_by, pymongo.DESCENDING)])
    else:
      result = collection.find(where_dictionary,selected_column_dictionary).limit(limit)
    return result

  def recSelectById (self,table,id):
    collection = self.db[table]
    result = collection.find_one({"_id" : ObjectId(id)})
    return result

  def getCount (self,table,selected_column_dictionary = None,where_dictionary = None,limit=10000,order_by=None,order_type=None):
    collection = self.db[table]
    if order_by and order_type:
      if order_type == "ASC":
        result = collection.find(where_dictionary,selected_column_dictionary).limit(limit).sort([(order_by, pymongo.ASCENDING)]).count()
      else:
        result = collection.find(where_dictionary,selected_column_dictionary).limit(limit).sort([(order_by, pymongo.DESCENDING)]).count()
    else:
      result = collection.find(where_dictionary,selected_column_dictionary).limit(limit).count()
    return result