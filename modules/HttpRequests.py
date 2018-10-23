import requests
class HttpRequests:

  def __init__(self):
    self.session = requests.session()

  def requestGet(self,url,tries=1,proxyDict={},return_error_page=0):
    for i in range(0,tries):
        #print("\nTry:"+str(i))
        try:
          self.response = self.session.get(url,proxies=proxyDict)
        except Exception as e:
          print("\nException raised for url:"+url+",Error:"+str(e))
        else:
          html = self.response.text
          if self.response.status_code == 200:
            #return html.decode('utf-8')
            return html
          elif html and return_error_page:
            return html
    return ""

  def requestPost(self,url,params={}):
    try:
      self.response = self.session.post(url,data=params)
    except Exception as e:
      print("\nException raised for url:"+url+",Error:"+str(e))
    else:
      if self.response.status_code == 200:
        return self.response.text
    return ""

  def getPage(self,method,url,params={}):
    html = ""
    if method=="GET":
        tries = 1
        return_error_page = 0
        proxy_ip = {}
        if 'tries' in params.keys():
            tries = params['tries']
        if 'proxy_ip' in params.keys():
            proxy_ip = params['proxy_ip']

        if 'headers' in params.keys():
            for key in params['headers']:
                self.session.headers.update( { key: params['headers'][key] } )
        if 'return_error_page' in params.keys():
          return_error_page = params['return_error_page']
        html = self.requestGet(url,tries,proxy_ip,return_error_page)
    else:
        html = self.requestPost(url,params['post_params'])
    return html

  def getCurrentUrl(self):
      return self.response.url