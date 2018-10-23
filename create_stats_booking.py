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

#####################
processoutput = os.popen("ps -A -L -F").read()
cur_script = os.path.basename(__file__)
res = re.findall(cur_script,processoutput)
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

def getLastDateObject():
  current_date = datetime.datetime.now().date()
  last_date = current_date - timedelta(days=1)  # decrease day one by one
  last_date_object = getDateTimeObject(str(last_date))
  return last_date_object  


if __name__ == '__main__':  
  current_date_obj = getDateTimeObject(str(datetime.datetime.now().date()))  
  dict_stats = {}  
  dict_stats['property_pending'] = 0
  property_url_rows = obj_master.obj_mongo_db.recSelect('property_urls',None,{'parse_interval':{'$gt':0}},1000,'updated_at','ASC')
  for property_url_row in property_url_rows:
    if 'parse_interval' in property_url_row:
      parse_interval = int(property_url_row['parse_interval'])      
      ####################################
      update_date_obj = getDateTimeObject((str(property_url_row['updated_at'].date())))
      curr_date_obj = getDateTimeObject(str(datetime.datetime.now().date()))
      #calculate the day diffrence
      date_diffrence = curr_date_obj - update_date_obj      
      if date_diffrence.days >=  parse_interval:
        dict_stats['property_pending'] = dict_stats['property_pending']+1
  ##########################################
  dict_stats['date'] = current_date_obj
  dict_where = { 'updated_at':{ '$gte': current_date_obj } }
  dict_stats['property_parsed'] = obj_master.obj_mongo_db.getCount('property_urls',None,dict_where)
  dict_stats['hotel_parsed'] = obj_master.obj_mongo_db.getCount('hotel_master',None,dict_where)
  dict_stats['price_parsed'] = obj_master.obj_mongo_db.getCount('prices',None,dict_where)
  dict_stats['room_details_parsed'] = obj_master.obj_mongo_db.getCount('room_details',None,dict_where)  
  
  dict_stats['total_property'] = obj_master.obj_mongo_db.getCount('property_urls')
  dict_stats['active_property'] = obj_master.obj_mongo_db.getCount('property_urls',None,{'parse_interval':{'$gt':0}})

  dict_stats['total_logs'] = obj_master.obj_mongo_db.getCount('logs_booking',None,dict_where)
  print(str(dict_stats))  
  #exit()
  stats_booking_rows = obj_master.obj_mongo_db.recSelect( 'stats_booking' , None , { 'date':current_date_obj } )
  if stats_booking_rows.count():
    dict_stats['updated_at'] = datetime.datetime.now()    
    ret_id = obj_master.obj_mongo_db.recUpdate( 'stats_booking' , dict_stats , { 'date':current_date_obj } )
    print( "\nUpdated in stats table. The return id is"+str(ret_id) )
  else:
    dict_stats['created_at'] = datetime.datetime.now()
    dict_stats['updated_at'] = datetime.datetime.now()
    ret_id = obj_master.obj_mongo_db.recInsert( 'stats_booking' , [dict_stats] )
    print( "\ninserted in stats table. The return id is"+str(ret_id) )
  