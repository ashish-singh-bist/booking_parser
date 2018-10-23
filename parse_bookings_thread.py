
#!/usr/bin/python
# -*- coding: utf-8 -*- 
import os
import time
import sys, getopt
import re
import json
import datetime
import hashlib
from datetime import timedelta, date
import threading
import multiprocessing
from multiprocessing import cpu_count
from multiprocessing.dummy import Pool
from bson.objectid import ObjectId
#####################
processoutput = os.popen("ps -A -L -F").read()
cur_script = os.path.basename(__file__)
res = re.findall(cur_script,processoutput)
#print(str(res))
if len(res)>2:
    print ("EXITING BECAUSE ALREADY RUNNING.\n\n")
    exit(0)
#####################

sys.path.append("modules")
sys.path.append("scripts")
sys.path.append("/usr/local/lib/python3.5/dist-packages")
from Master import Master
from Booking import Booking
obj_master = Master()
html_dir_path = obj_master.obj_config.html_dir_path


def getDateTimeObject(date_str):
  datetime_object = datetime.datetime.strptime(date_str, '%Y-%m-%d')
  return datetime_object

def checkRoomEquipmentChanged(dict_room_equip_db_json,dict_parsed_room_equip_json):
  dict_room_equip_db = json.loads(dict_room_equip_db_json)
  dict_parsed_room_equip = json.loads(dict_parsed_room_equip_json)
  #we check the key is equal or not. it not matched it means date is updated
  if not len(dict_room_equip_db) == len(dict_parsed_room_equip):
    return 1  
  for key in dict_parsed_room_equip:
    if not key in dict_room_equip_db:
      return 1
  return 0

def checkHotelInfoChanged(dict_hotel_info_db,dict_parsed_hotel_info):
  #traverse the hotel info dictonary one by one and check with other dictonary(which is parsed currently)
  for key in dict_parsed_hotel_info:
    #if key not matched return 1(something got changed)
    if not key in dict_hotel_info_db:
      return 1
    else:      
      ######################
      #for hotel info we match only some selected keys
      if key in 'hotel_name hotel_category hotel_stars booking_rating location':
        #if the above value are changed return 1
        if not dict_hotel_info_db[key] == dict_parsed_hotel_info[key]:
          return 1
      #if key is hotel equipment check each key      
      elif key == 'hotel_equipments':
        dict_hotel_equip_db = json.loads(dict_hotel_info_db[key])
        dict_hotel_equip_parsed = json.loads(dict_parsed_hotel_info[key])
        if not len(dict_hotel_equip_parsed) == len(dict_hotel_equip_db):
            return 1
        #traversing the hotel equipment dictonary
        for key_equip in dict_hotel_equip_db:          
          if not key_equip in dict_hotel_equip_parsed:
            return 1
          else:
            #in hotel equipment inner keys also present
            #checking the inner keys are same or not
            dict_temp_1 = dict_hotel_equip_db[key_equip]
            dict_temp_2 = dict_hotel_equip_parsed[key_equip]
            if not len(dict_temp_1) == len(dict_temp_2):
              return 1
            for key_temp in dict_temp_1:
              if not key_temp in dict_temp_2:
                return 1  
  return 0

def parseAndSaveData(temp_dict):  
  obj_booking = Booking() 
  url = temp_dict['url']
  ##############
  redis_key_url_md5 = obj_booking.obj_helper.getMd5(url)
  redis_valule_url = obj_booking.obj_redis_cache.getKeyValue(redis_key_url_md5)
  if redis_valule_url:
    print("This url already scraped. skipping...")
    return {'status':1,'logs':[],'redis_key_url_md5':redis_key_url_md5}
  ##############
  prop_url = temp_dict['property_url']
  #temp_file = temp_dict['temp_file']
  checkin_date = temp_dict['checkin_date']
  checkout_date = temp_dict['checkout_date']
  temp_prop_id = temp_dict['temp_prop_id']
  length_stay = temp_dict['length_stay']
  number_of_guests = temp_dict['number_of_guests']  
  print( "\nParsing start:"+str(datetime.datetime.now()) )
  result = obj_booking.parseProductDetails(url,checkin_date,checkout_date)  
  print( "\nParsing End:"+str(datetime.datetime.now()) )  
  obj_booking.obj_helper.writeFile( "test.txt" , "\n"+url )
  #############
  if 'is_success' in result and result['is_success']==0:
    #it means parsing failed return 
    return {'status':3,'logs':result['arr_logs']}
  #############
  if 'hotel_info' in result:
    print( "hotel info extracted......" )
    hotel_id = None
    if 'hotel_id' in result['hotel_info'] and result['hotel_info']['hotel_id']:
      hotel_id = result['hotel_info']['hotel_id']         
    ###################
    if hotel_id:
      redis_hotel_id = obj_booking.obj_redis_cache.getKeyValue(temp_prop_id)
      #only for inserting below data in 'property_urls' table. if net inserted yet
      if not redis_hotel_id:
        temp_dict_hotel = {}
        temp_dict_hotel['hotel_id'] = hotel_id
        if 'hotel_name' in result['hotel_info'] and result['hotel_info']['hotel_name']:
          temp_dict_hotel['hotel_name'] = result['hotel_info']['hotel_name']
        if 'city' in result['hotel_info'] and result['hotel_info']['city']:
          temp_dict_hotel['city'] = result['hotel_info']['city']
        if 'country' in result['hotel_info'] and result['hotel_info']['country']:
          temp_dict_hotel['country'] = result['hotel_info']['country']
        obj_booking.obj_mongo_db.recUpdate( 'property_urls' , temp_dict_hotel , { '_id':ObjectId(temp_prop_id) } , 0  )
        #set redis cache when hotel_id and other data is inserted in property_urls
        obj_booking.obj_redis_cache.setKeyValue(temp_prop_id,hotel_id)
    else:
      error_str = "could not get hotel_id for url"+url
      result['arr_logs'].append(error_str)
      #could not get hotel_id return       
      return {'status':3,'logs':result['arr_logs']}
    ###################
    result['hotel_info']['prop_url'] = prop_url
    redis_key_hotel_info = str(datetime.datetime.now().date())+"-"+str(hotel_id)
    hotel_info_redis_value = obj_booking.obj_redis_cache.getKeyValue(redis_key_hotel_info)
    #we insert/update the hotel info once in a day.
    #the redis key is mady by current date(current_date+hotel_id) 
    if not hotel_info_redis_value:
      hotel_master_rows = obj_booking.obj_mongo_db.recSelect( 'hotel_master' , None, { 'hotel_id':hotel_id } )    
      if hotel_master_rows.count():
        print( "alredy inserted..." )
        for hotel_master_row in hotel_master_rows:
          #compare the parsed hotel_info with db hotel parsed info. if anything changed then update table
          is_changed = checkHotelInfoChanged(hotel_master_row,result['hotel_info'])
          #if hotel info is changed we update the hotel_master and
          #insert in hotel master history
          if is_changed:
            #########
            result['hotel_info']['updated_at'] = datetime.datetime.now()
            #########
            ret_id = obj_booking.obj_mongo_db.recUpdate( 'hotel_master' , result['hotel_info'] , { 'hotel_id':hotel_id } )
            print( "\nUpdated in hotel_master The return id is"+str(ret_id) )
            #####################
            #insert the old data in history table
            #these keys are not needed in history table            
            del hotel_master_row['_id']
            del hotel_master_row['updated_at']
            del hotel_master_row['created_at']
            ret_id = obj_booking.obj_mongo_db.recInsert( 'history_hotel_master' , [ hotel_master_row ] )
            print( "\nInserted in history_hotel_master The return id is"+str(ret_id) )
            #####################
          break#we keep only one record for one hotel      
      else:
        #result['hotel_info']['prop_id'] = temp_prop_id
        ret_id = obj_booking.obj_mongo_db.recInsert( 'hotel_master' , [ result['hotel_info'] ] )
        print( "\ninserted in hotel_master The return id is"+str(ret_id) )
      obj_booking.obj_redis_cache.setKeyValue(redis_key_hotel_info,1)
    #############################################################
    if 'room_price_details' in result:
      dict_room_price_details = result['room_price_details']
      for dict_price_details in dict_room_price_details['price_details']:        
        for key_room_type in dict_price_details:                  
          dict_room_info = dict_price_details[key_room_type]                  
          if 'price_info' in dict_room_info:
            arr_price_info = dict_room_info['price_info']            
            if 'room_equipment' in dict_room_info and dict_room_info['room_equipment']:
              dict_room_info['hotel_id'] = hotel_id
              dict_room_info['room_type'] = key_room_type
              ###################              
              redis_key_room_detail = str(datetime.datetime.now().date())+"-"+str(hotel_id)+"-"+str(key_room_type)
              room_details_redis_value = obj_booking.obj_redis_cache.getKeyValue(redis_key_room_detail)
              ###################
              #this key not needed in room details table
              del dict_room_info['price_info']
              ###################
              #we check the room details once in a day(hotel_id,key_room_type)
              #the redis key is made by current_date+hotel_id+key_room_type
              #if this redis key is not exist then we decide the room details is inserted/updated
              if not room_details_redis_value:
                room_detail_rows = obj_booking.obj_mongo_db.recSelect( 'room_details' , None, { 'hotel_id':hotel_id,'room_type':key_room_type } )
                #if room equipments are changed then we update the table
                if room_detail_rows.count():
                  for room_detail_row in room_detail_rows:
                    is_changed = None
                    try:
                      is_changed = checkRoomEquipmentChanged(room_detail_row['room_equipment'],dict_room_info['room_equipment'])
                    except Exception as e:
                      result['arr_logs'].append(str(e))                      
                    if is_changed:                      
                      dict_room_details = {}
                      dict_room_details['updated_at'] = datetime.datetime.now()
                      dict_room_details['room_equipment'] = dict_room_info['room_equipment']                      
                      ret_id = obj_booking.obj_mongo_db.recUpdate( 'room_details' , dict_room_details , { 'hotel_id':hotel_id,'room_type':key_room_type } )
                      print( "\nUpdate room_details The return id is"+str(ret_id) )                    
                    break
                else:
                  #no record found for this hotel_id and room type so inserting
                  ret_id = obj_booking.obj_mongo_db.recInsert( 'room_details' , [ dict_room_info ] )
                  print( "\ninserted in room_details The return id is"+str(ret_id) )
                #set redis value for today(as room details inserted today)
                obj_booking.obj_redis_cache.setKeyValue(redis_key_room_detail,1)
            available_only = ""            
            for dict_price_info in arr_price_info:              
              #available_only = dict_price_info['max_persons']
              if 'nr_stays' in dict_price_info and dict_price_info['nr_stays']:
                dict_price_info['available_only'] = dict_price_info['nr_stays']                
              ################
              #craeting these field manully
              dict_price_info['room_type'] = key_room_type
              dict_price_info['number_of_days'] = length_stay
              dict_price_info['number_of_guests'] = number_of_guests
              dict_price_info['hotel_id'] = hotel_id
              checkin_date_obj = getDateTimeObject(checkin_date)
              ################
              choices_str = ""
              if 'mealplan_included_name' in dict_price_info and dict_price_info['mealplan_included_name']:
                choices_str = choices_str + dict_price_info['mealplan_included_name']
              if 'cancellation_type' in dict_price_info and dict_price_info['cancellation_type']:
                choices_str = choices_str + dict_price_info['cancellation_type']
              #########################            
              if 'cancellation_day_diff' in dict_price_info and dict_price_info['cancellation_day_diff']:
                choices_str = choices_str + str(dict_price_info['cancellation_day_diff'])                
              #########################
              if 'max_persons' in dict_price_info and dict_price_info['max_persons']:                
                choices_str = choices_str + str(dict_price_info['max_persons'])
              #########################              
              #set the key in redis cache
              str_to_md5 = str(hotel_id)+"-"+str(key_room_type)+"-"+str(length_stay)+"-"+str(number_of_guests)+"-"+choices_str
              #for now not including price we will add it later...
              if 'raw_price' in dict_price_info and dict_price_info['raw_price']:
                raw_price = dict_price_info['raw_price']                                
                del dict_price_info['raw_price']
                parsed_dt = getDateTimeObject( str(datetime.datetime.now().date()) )                
                #############################
                #first insert/update the data                
                #################
                temp_key_md5 = obj_booking.obj_helper.getMd5(str_to_md5) 
                pk_redis_value = obj_booking.obj_redis_cache.getKeyValue(temp_key_md5)
                if not pk_redis_value:
                  #if record not isnerted
                  #if row is not present init the cal info 
                  ################
                  temp_dict = {}    
                  temp_dict['s'] = []
                  temp_dict['s'].append(parsed_dt)
                  temp_dict['c'] = checkin_date_obj
                  temp_dict['p'] = raw_price
                  dict_price_info['cal_info'] = [temp_dict]
                  ################
                  ret_val = obj_booking.obj_mongo_db.recInsert( 'prices' , [dict_price_info] )                  
                  temp_redis_value = str(ret_val[0])
                  #we have to set the primary_key redis_value. we will do it later
                  obj_booking.obj_redis_cache.setKeyValue(temp_key_md5,temp_redis_value)
                else:
                  #record already inserted..
                  print("populated the keys of cal_info")
                  #############################
                  where_hash = {}
                  where_hash['_id'] = ObjectId(pk_redis_value)                  
                  #if raw_price is same then only push the parsed_dt                  
                  data_info = {}                  
                  data_info['$push'] = {'cal_info.$[elem].s':parsed_dt}
                  #data_info['$set'] = {'updated_at':datetime.datetime.now()}
                  #only push the parsed date if checkin_date and prices are same                  
                  array_filter = [ { "elem.p": { '$eq': raw_price }, "elem.c": { '$eq': checkin_date_obj } } ]
                  ret_val = obj_booking.obj_mongo_db.recUpdateArrayFilters( 'prices' , data_info , where_hash,array_filter )
                  if ret_val.modified_count:
                    #if data successfully updated
                    print("The data is successfully updated....")
                  else:                    
                    #make a new entry inside cal_info                  
                    ret_val = obj_booking.obj_mongo_db.recUpdateCustome( 'prices' , {"$set":{'updated_at':datetime.datetime.now()},'$push': {'cal_info':{'s':[parsed_dt],'c':checkin_date_obj,'p':raw_price}}} , where_hash )                  
                    print(ret_val)
                    #data not updated                                     
                  #########################
  #set redis when the url parsed successfully.we will create the file also later we will all redis key
  obj_booking.obj_redis_cache.setKeyValue(redis_key_url_md5,1)
  obj_master.obj_helper.writeFile( "RedisTempKeys.txt" , redis_key_url_md5+"\n" )
  return {'status':1,'logs':result['arr_logs'],'redis_key_url_md5':redis_key_url_md5}
    

if __name__ == '__main__':
  max_process = 100
  parsing_interval = 1
  number_of_guests = 2
  scraper_active = 1
  config_id = None
  #we will set it as None later(when it will populated in db)
  str_length_stay = ''
  config_rows = obj_master.obj_mongo_db.recSelect('config')
  #get the important data values from the config table(eg. parsing_interval,scraper_active etc.)
  for config_row in config_rows:
    if 'thread_count' in config_row and config_row['thread_count']:
      max_process = int(config_row['thread_count'])
    if 'parsing_interval' in config_row and config_row['parsing_interval']:
      parsing_interval = int(config_row['parsing_interval'])
    if 'number_of_guests' in config_row and config_row['number_of_guests']:
      number_of_guests = int(config_row['number_of_guests'])
    if 'scraper_active' in config_row and config_row['scraper_active']:
      scraper_active = int(config_row['scraper_active'])
    if '_id' in config_row and config_row['_id']:
      config_id = config_row['_id']
    if 'str_length_stay' in config_row and config_row['str_length_stay']:
      str_length_stay = config_row['str_length_stay']
  
  print( "The thread:"+str(max_process) )
  time.sleep(1)
  if not scraper_active:
    print( "SCRAPER IS NOT ACTVE" )
    sleep(2)
    exit()
  #set the status 'running' when we start parsing of data
  if config_id:
    ret_id = obj_master.obj_mongo_db.recUpdate( 'config' , { 'script_status':'running','started_at':datetime.datetime.now(),'updated_at':datetime.datetime.now() } , { '_id':ObjectId(config_id) } )
  #set the pool max processed
  pool = multiprocessing.Pool(processes=max_process)  
  #fetch all property urls to parsed which parsed before the time intervel date  
  property_url_rows = obj_master.obj_mongo_db.recSelect('property_urls',None,{'parse_interval':{'$gt':0}},100,'updated_at','ASC')
  for property_url_row in property_url_rows:
    temp_prop_id = property_url_row['_id']
    property_url = property_url_row['url']
    if 'parse_interval' in property_url_row:      
      parse_interval = int(property_url_row['parse_interval'])
      date_time_interval = datetime.datetime.now() - timedelta(days=parse_interval)
      print("Time Beforeinterval:"+str(date_time_interval)+"  Last Parsed:"+str(property_url_row['updated_at'])+" Time Interval:"+str(parse_interval))
      update_date_obj = getDateTimeObject((str(property_url_row['updated_at'].date())))
      curr_date_obj = getDateTimeObject(str(datetime.datetime.now().date()))
      #calculate the day diffrence
      date_diffrence = curr_date_obj - update_date_obj
      print( "days:"+str(date_diffrence.days) )      
      if date_diffrence.days >=  parse_interval:
        print("parse this property..")
      else:        
        continue
    #overwrite the value of main config if it exists in property
    if 'number_of_guests' in property_url_row and property_url_row['number_of_guests']:      
      number_of_guests = property_url_row['number_of_guests']
    if 'str_length_stay' in property_url_row and property_url_row['str_length_stay']:
      str_length_stay = property_url_row['str_length_stay']

    str_length_stay = str_length_stay.strip( ' ' )
    arr_temp = str_length_stay.split(',')
    arr_length_stay = []
    for temp_stay in arr_temp:
      if temp_stay:
        try:
          arr_length_stay.append( int(temp_stay) )
        except Exception as e:
          log = str(e)
          ret_id = obj_master.obj_mongo_db.recInsert( 'logs_booking' , [ { 'prop_id':temp_prop_id,'status_code':11,'log':log } ] )    
    if len(arr_length_stay) == 0:
      log = "length_stay is not provided properly for prop_id:" + temp_prop_id
      ret_id = obj_master.obj_mongo_db.recInsert( 'logs_booking' , [ { 'prop_id':temp_prop_id,'status_code':11,'log':log } ] )
      print("Length stays is not provided..exiting..")
      continue    
    script_start_time = datetime.datetime.now()
    obj_master.obj_helper.writeFile( "LogScriptStatus.txt" , "\nStart:"+str(script_start_time) )
    obj_master.obj_helper.writeFile( "LogScriptStatus.txt" , "\nPropUrl:"+str(property_url) )
    #make the date start_date and end date
    start_date = datetime.datetime.now().date()
    end_date = datetime.datetime.now().date() + timedelta(days=365)    
    #################
    total_urls_to_parse = len(arr_length_stay)*365
    #################
    arr_args_dict = []
    #we parse the data of one year.
    while start_date < end_date:        
      checkin_date = str(start_date)
      #loop for length stay eg. [1,2,3,4,5]
      for length_stay in arr_length_stay:
        checkout_date = str( start_date + timedelta(days=length_stay) )  # increase day one by one        
        url = property_url+"?checkin="+str(checkin_date)+"&checkout="+str(checkout_date)+"&selected_currency=EUR"+"&group_adults="+str(number_of_guests)
        arr_args_dict.append({'url':url,'property_url':property_url,'checkin_date':checkin_date,'checkout_date':checkout_date,'temp_prop_id':temp_prop_id,'length_stay':length_stay,'number_of_guests':number_of_guests})
      start_date = start_date + timedelta(days=1)  # increase day one by one        
    result = pool.map_async(parseAndSaveData, [args_dict for args_dict in arr_args_dict])    
    while not result.ready():      
      time.sleep(0.5)
    script_end_time = datetime.datetime.now()    
    arr_pool_result = result.get()
    #after parsing each property we check the status
    if total_urls_to_parse == len(arr_pool_result):
      prop_stats_dict = {}      
      prop_stats_dict['prop_id'] = temp_prop_id
      prop_stats_dict['success_count'] = 0
      prop_stats_dict['fail_count'] = 0
      prop_stats_dict['log_count'] = 0
      prop_stats_dict['run_count'] = 1
      prop_stats_dict['total_urls'] = total_urls_to_parse      
      current_date_obj = getDateTimeObject(str(datetime.datetime.now().date()))
      prop_stats_dict['date'] = current_date_obj
      prop_stats_dict['start_time'] = script_start_time
      prop_stats_dict['end_time'] = datetime.datetime.now()

      arr_urls_redis_key = []
      for pool_result in arr_pool_result:
        if pool_result['status']==1:
          prop_stats_dict['success_count'] = prop_stats_dict['success_count'] + 1
          #collect these keys these needs to be deleted if successfully got
          if 'redis_key_url_md5' in pool_result and pool_result['redis_key_url_md5']:
            arr_urls_redis_key.append(pool_result['redis_key_url_md5'])
        elif pool_result['status']==3:
          prop_stats_dict['fail_count'] = prop_stats_dict['fail_count'] + 1
        if 'logs' in pool_result:
          prop_stats_dict['log_count'] = prop_stats_dict['log_count'] + len(pool_result['logs'])
          for log in pool_result['logs']:
            ret_id = obj_master.obj_mongo_db.recInsert( 'logs_booking' , [ { 'prop_id':temp_prop_id,'status_code':pool_result['status'],'log':log } ] )
      property_urls_stats_rows = obj_master.obj_mongo_db.recSelect('property_urls_stats',None,{'prop_id':ObjectId(temp_prop_id),'date':current_date_obj})
      if property_urls_stats_rows.count():
        #how many time the property runs
        if 'run_count' in property_urls_stats_rows[0] and property_urls_stats_rows[0]['run_count']:
          prop_stats_dict['run_count']  = property_urls_stats_rows[0]['run_count'] + 1
        if 'fail_count' in property_urls_stats_rows[0] and property_urls_stats_rows[0]['fail_count']:
          prop_stats_dict['fail_count'] = prop_stats_dict['fail_count'] + property_urls_stats_rows[0]['fail_count']
        if 'log_count' in property_urls_stats_rows[0] and property_urls_stats_rows[0]['log_count']:
          prop_stats_dict['log_count'] = prop_stats_dict['log_count'] + property_urls_stats_rows[0]['log_count']    
        ret_id = obj_master.obj_mongo_db.recUpdate('property_urls_stats',prop_stats_dict,{'prop_id':ObjectId(temp_prop_id),'date':current_date_obj})
      else:
        ret_id = obj_master.obj_mongo_db.recInsert('property_urls_stats',[prop_stats_dict])      
      #if all urls parsed successfully. then update the update_ts
      if prop_stats_dict['success_count'] == total_urls_to_parse:
        ret_result = obj_master.obj_mongo_db.recUpdate( 'property_urls' , { 'updated_at':datetime.datetime.now() } , { '_id':ObjectId(temp_prop_id) } )
        print( "\nUpdated in property_urls The return id is"+str(ret_result) )
        #######################
        if ret_result['updatedExisting']:
          for urls_redis_key in arr_urls_redis_key:
            obj_master.obj_redis_cache.deleteKeyValue(urls_redis_key)
            obj_master.obj_helper.writeFile( "RedisDeleted.txt" , urls_redis_key+"\n" )
          #unset the redis. which we have created for the urls
          # if obj_master.obj_helper.isFileExists("RedisTempKeys.txt"):
          #     file_content = obj_master.obj_helper.readFile( "RedisTempKeys.txt" )
          #     if file_content:
          #       arr_line = file_content.split('\n')
          #       for line in arr_line:
          #         if line:      
          #           obj_master.obj_redis_cache.deleteKeyValue(line)
          #     #empty this file if successfully parsed..
          #     obj_master.obj_helper.writeFileNew( "RedisTempKeys.txt" , "" )
        #######################
    obj_master.obj_helper.writeFile( "LogScriptStatus.txt" , "\nEnd:"+str(datetime.datetime.now()) )    
    #####################
    script_dir_path = obj_master.obj_config.script_dir_path
    command_str = 'cd '+script_dir_path+'; /usr/bin/python3 create_stats_booking.py > /dev/null 2>/dev/null &'
    temp_returned_value = os.system(command_str)
    if temp_returned_value == 0:
      print( "script run successfully.." )
    else:
      print( "got some error in running script.." )
    #check the scraper status(active/inactive) after parsing each row
    #if it is inactive then exit from the loop
    temp_config_rows = obj_master.obj_mongo_db.recSelect('config',None,{'scraper_active':0})
    if temp_config_rows.count():
      break
    #####################
  if config_id:
    #set the status in config file
    ret_id = obj_master.obj_mongo_db.recUpdate( 'config' , { 'script_status':'end','ended_at':datetime.datetime.now(),'updated_at':datetime.datetime.now() } , { '_id':ObjectId(config_id) } )
  ####################
  returned_value = os.system('cd /var/www/html && /usr/bin/php artisan schedule:run > /dev/null 2>/dev/null &')
  if returned_value == 0:
    print( "script run successfully.." )
  else:
    print( "got some error in running script.." )
  ####################
  exit()

