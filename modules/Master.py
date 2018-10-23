from Helper import Helper
from HttpRequests import HttpRequests
from MongoDatabase import MongoDatabase
from RedisCache import RedisCache
from Config import Config
#from Database import Database
import re
import json

class Master(object):
  def __init__(self):
    self.obj_helper = Helper()
    self.obj_req = HttpRequests()
    self.obj_mongo_db = MongoDatabase()
    self.obj_redis_cache = RedisCache()
    self.obj_config = Config()
    #self.obj_db= Database()
    #self.proxy_list = self.initProxies()
  # def insertDataInDb(self,data_hash,md5_str):
  #   if data_hash:
  #     #self.obj_helper.writeFile("testdata.txt", json.dumps(data_hash) + md5_str + "\n")
  #     if md5_str != '':
  #       if len(data_hash['review_data']['reviews']):
  # #        if review_in_db > 0: # if review already in db than apend review
  # #          data_hash['review_data']['reviews'] = data_hash['review_data']['reviews'] + reviews_json['reviews']

  #         self.obj_db.recUpdate("products_reviews_rating",{ 'is_active' : 1 ,'reviews' : json.dumps(data_hash['review_data'], ensure_ascii=False) , 'review_count' : len(data_hash['review_data']['reviews']),'rating' : data_hash['review_data']['avg_rating'] , 'product_actual_url' : data_hash['product_actual_url'] } , { 'md5_str': md5_str })
  #         print("reviews saved\n")
  #       else:
  #         if data_hash['product_actual_url'] != '':
  #           self.obj_db.recUpdate("products_reviews_rating",{ 'is_active' : 1 ,'product_actual_url' : data_hash['product_actual_url'] } , { 'md5_str': md5_str })
  #           print("product actual url updated\n")
  #     else:
  #         self.obj_db.recUpdate("products_reviews_rating",{ 'is_active' : 0 } , { 'md5_str': md5_str })

  # def initProxies(self):
  #   proxy_rows = self.obj_db.recCustomQuery( "SELECT proxy_ip FROM tbl_proxies WHERE error_count<=4 ORDER BY error_count ASC" )
  #   return proxy_rows

  # def createLog(self,msg,status=0):
  #   dict_temp = {}
  #   dict_temp['log'] = msg
  #   if status:
  #     dict_temp['status'] = status
  #   #self.obj_helper.writeFile( "Logs.txt" , msg+"\n" )   #save log in log file
  #   self.obj_db.recInsert("products_parse_log",dict_temp)  #save log in db

  # def setStatusFail(self,field,id):
  #   self.obj_db.recUpdate("ean_list", { field : '2','update_ts' : {'func' :  'now()' }}, { 'id' : id })

  # def insertProductDetail(self,result_dict):
    
  #   temp_dict = {}
  #   temp_dict['update_ts'] = {'func' :  'now()' }
    
  #   ######################################
  #   #set the status as successfully parsed
  #   if result_dict['source'] == 'amazon':
  #     temp_dict['amazon_status_flag'] = 1
    
  #   if result_dict['source'] == 'upcitemdb':
  #     temp_dict['upcitemdb_status_flag'] = 1
    
  #   if result_dict['source'] == 'cdiscount' or result_dict['source'] == 'Cdiscount':
  #     temp_dict['cdiscount_status_flag'] = 1
  #     temp_dict['status_flag'] = 1
  #   if result_dict['source'] == 'Ebay':
  #     temp_dict['status_flag'] = 1
  #   ######################################
    
  #   #amazon_asin number parsed from "http://www.upcitemdb.com" to parse data from amazon 
  #   if 'amazon_asin' in result_dict.keys():
  #       temp_dict['asin_id'] = result_dict['amazon_asin']
  #       del result_dict['amazon_asin']
  #   final_data_dict = {}
  #   final_data_dict['product_actual_url'] = result_dict['product_actual_url']
  #   final_data_dict['product_details'] = json.dumps( result_dict['product_details'], ensure_ascii=False )
  #   final_data_dict['source'] = result_dict['source']
  #   final_data_dict['images'] = json.dumps( result_dict['images'], ensure_ascii=False )
  #   final_data_dict['ean_ref_id'] = result_dict['ean_ref_id']
  #   final_data_dict['update_ts'] = {'func' :  'now()' }
  #   try:
  #     self.obj_db.recInsertUpdate("ean_products_details", final_data_dict , {'source':result_dict['source'], 'ean_ref_id':result_dict['ean_ref_id'] } )
  #     self.obj_db.recUpdate("ean_list", temp_dict , { 'id' : result_dict['ean_ref_id'] })
  #   except Exception as e:
  #     self.createLog( "Insert Error for ean_ref_id:"+str(result_dict['ean_ref_id'])+",error:"+str(e) )