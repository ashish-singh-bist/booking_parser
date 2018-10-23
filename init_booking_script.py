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
from bson.objectid import ObjectId


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

def getDateTimeObject(date_str):
  datetime_object = datetime.datetime.strptime(date_str, '%Y-%m-%d')
  return datetime_object

if __name__ == '__main__':  
  from Master import Master
  obj_master = Master()  
  run_flag = 0
  redis_value_date = obj_master.obj_redis_cache.getKeyValue('has_inited')  
  if redis_value_date:
    current_date_obj = getDateTimeObject(str(datetime.datetime.now().date()))
    #if redis value is not inited today run it
    if not redis_value_date in str(current_date_obj):
      run_flag = 1      
  else:
    run_flag = 1

  if run_flag:    
    command_str = 'cd '+obj_master.obj_config.script_dir_path+'; /usr/bin/python3 parse_bookings_thread.py > /dev/null 2>/dev/null &'
    print(command_str)
    os.system(command_str)
    time.sleep(4)
    #run the script and set the redis for today
    obj_master.obj_redis_cache.setKeyValue( 'has_inited' , str(datetime.datetime.now().date()) )
  exit()

  