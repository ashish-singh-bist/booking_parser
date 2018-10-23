from bs4 import BeautifulSoup
import codecs
import re

class Helper:
  def getContainerData(self,html,tag,attr_name,attr_value):
    soup = BeautifulSoup(html,"lxml")
    container_arr = soup.findAll( tag , { attr_name : attr_value } )
    return container_arr;

  def getContainerHtml(self,html,tag,attr_name,attr_value):
    soup = BeautifulSoup(html,"lxml")
    container_arr = soup.findAll( tag , { attr_name : attr_value } )
    temp_html = ''
    for temp_item in container_arr:
        temp_html += str(temp_item)
    return temp_html

  def getContainerText(self,html,tag,attr_name,attr_value):
    soup = BeautifulSoup(html,"lxml")
    container_arr = soup.findAll( tag , { attr_name : attr_value } )
    if len(container_arr):
      return container_arr[0].text
    else:
      return ""
  
  def getHtmlByTag(self,html,tag):
    soup = BeautifulSoup(html,"lxml")
    tag_arr = soup.findAll( tag )
    return tag_arr;

  def getAttributeValue(self,html,tag,attr):
    soup = BeautifulSoup(html,"lxml")
    tag_arr = soup.findAll( tag )
    if tag_arr:
      attr_val = tag_arr[0].get(attr)
      if attr_val:
        return attr_val
    return ""
       
  def getMd5(self,str):
    import hashlib
    return hashlib.md5(str.encode()).hexdigest()    
  
  def removeHtml(self,html):
    html = re.sub(r'<!--.*?-->', '', html,flags=re.S|re.M)
    html = re.sub(r'<script[^>]*>.*?<\/script>', '', html,flags=re.S|re.M)
    html = re.sub(r'<style[^>]*>.*?<\/style>', '', html,flags=re.S|re.M)
    html = re.sub(r'<.*?>', '', html,flags=re.S|re.M)        
    html = re.sub(r'\s+', ' ', html,flags=re.S|re.M)
    html = re.sub(r'(^\s+|\s+$)', '', html)
    return html

  def getContentAfterRegexMatch (self,content,index):
    return content[index:len(content)]

  def writeFile(self,filename,content):
    file = open(filename,"a") 
    file.write(content) 
    file.close()
    return 1

  def writeFileUTF(self,filename,content):
    file = codecs.open(filename,"a","utf-8") 
    file.write(content) 
    file.close()
    return 1

  def writeFileNew(self,filename,content):
    file = open(filename, "w")
    file.write(content) 
    file.close()
    return 1

  def writeFileNewUTF(self,filename,content):
    file = codecs.open(filename, "w","utf-8")
    file.write(content) 
    file.close()
    return 1
    
  def readFile(self,filename):
    file = open(filename, "r")
    content = file.read()
    file.close()
    return content

  def readFileUTF(self,filename):
    file = codecs.open(filename, "r")
    content = file.read()
    file.close()
    return content

  def readFileLines(self,filename):
    file = open(filename, "r") 
    content = file.readlines()
    file.close()
    return content
  def readDirectory(self,dirname):
    import os
    list = os.listdir(dirname)
    return list
  def isFileExists(self,file_path):
    import os
    if os.path.exists(file_path):
        return 1
    return 0
  def currentTime(self,with_time=0):
    from datetime import datetime
    if with_time:
      return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
      return datetime.now().strftime('%Y-%m-%d') 