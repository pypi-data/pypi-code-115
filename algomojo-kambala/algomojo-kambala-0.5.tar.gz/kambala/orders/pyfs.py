import json
import requests

class api:
  def __init__(self,apikey,apisecret,broker,version="1.0"):
     self.apikey=apikey 
     self.apisecret=apisecret
     self.burl = "https://" + broker + 'api.algomojo.com/' + str(version) + '/'
  def place_order(self,client_id,exchange,ticker,qty,action,ordertype,product,prc="0",dscqty="0",trigprice="0",amo="NO",stgname="Test Strategy"):
    apikey=self.apikey
    apisecret=self.apisecret
    data = {
            "api_key":apikey,
            "api_secret":apisecret,
            "data":{
                    "strg_name":stgname,
                    "uid":client_id,
                    "actid":client_id,
                    "tsym":ticker,
                    "exch":exchange,
                    "trantype":action,
                    "ret":"DAY",
                    "prctyp":ordertype,
                    "qty":qty,
                    "dscqty":str(dscqty),
                    "MktPro":"NA",
                    "prc":str(prc),
                    "trgprc":str(trigprice),
                    "prd":product,
                    "AMO":amo,
                    "ordersource":"API",
                   }
            } 
    url = self.burl + "PlaceOrder"   
    response = requests.post(url,json.dumps(data), headers={'Content-Type': 'application/json'})
    print(response)
    jsonValue = response.json()
    print(jsonValue)


  def place_multi_order(self, order_list):
    l =order_list
    for i in range(len(l)):
      l[i]["exch"]=l[i]["exchange"]
      l[i]["tsym"]=str(l[i]["ticker"])
      l[i]["qty"]=str(l[i]["qty"])
      l[i]["prd"]=l[i]["product"]
      l[i]["prc"]= str(l[i]["price"])
      l[i]["trantype"]=l[i]["action"]
      l[i]["prctyp"]=l[i]["ordertype"]
      l[i]["dscqty"]=l[i]["discqty"]
      l[i]["trgprc"]=l[i]["trigprc"]
      l[i]["AMO"]= "NO" 
      l[i]["ordersource"]="API"
      l[i]["remarks"]=""
      l[i]["strg_name"]="stgname"
      l[i]["ret"]="DAY"
      l[i]["MktPro"]="NA"
      l[i]["user_apikey"]=l[i]["user_apikey"]
      l[i]["api_secret"]=l[i]["api_secret"]
      l[i]["uid"]=l[i]["uid"]
      l[i]["actid"]=l[i]["uid"]
      l[i]["order_refno"]="1"
    
             
        
    data = {
              "api_key": self.apikey,
              "api_secret": self.apisecret,
              "data":
                {
                   "orders": l
                }
            }
    print(data)     
    url = self.burl + "PlaceMultiOrder"        
    response = requests.post(url, data=json.dumps(data), headers={'Content-Type': 'application/json'})
    print(response)
    jsonValue = response.json()
    print(jsonValue)          
                

  def place_option_order(self,client_id,spot,expiry,action,optiontype,ordertype,qty,strike,price="0",product='C',trigprice='0',offset='1',stgname="Test Strategy"):
    apikey=self.apikey
    apisecret=self.apisecret
    data = {
             "api_key":apikey,
             "api_secret":apisecret,
             "data":{ 
                     "strg_name":stgname,
                     "uid":client_id,
                     "spot_sym":spot,
                     "expiry_dt":expiry,
                     "Ttranstype":action,
                     "opt_type":optiontype,
                     "prctyp":ordertype,
                     "qty": qty,
                     "Price":str(price),
                     "TrigPrice":str(trigprice),
                     "Pcode":product,
                     "strike_int":str(strike),
                     "offset":offset
                     
                    }
           }
    url = self.burl + "PlaceFOOptionsOrder"     
    response = requests.post(url,json.dumps(data), headers= {'Content-Type': 'application/json'})
    jsonValue = response.json()
    print(jsonValue)
    return  jsonValue
  def modify_order(self,client_id,orderno,exchange="0",ticker="0",ordertype="0",qty="0",prc="0",trigprice="0",ret="DAY"):
    apikey=self.apikey
    apisecret=self.apisecret
    data = {
            "api_key":apikey,
            "api_secret":apisecret,
            "data":{
                    "strg_name": "Test Strategy", 
                    "uid":client_id,
                    "tsym":str(ticker),
                    "exch":str(exchange),
                    "prctyp":str(ordertype),
                    "qty ":str(qty),
                    "ret":ret,
		                "norenordno":orderno,
		                "prc":str(prc),
		                "trgprc":str(trigprice)
                  }
             }
    url = self.burl + "ModifyOrder"           
    response = requests.post(url,json.dumps(data), headers= {'Content-Type': 'application/json'})
    print(response)
    jsonValue = response.json()
    print(jsonValue)
    return  jsonValue         

  def cancel_order(self,client_id,orderno):
    apikey=self.apikey
    apisecret=self.apisecret
    data = {
            "api_key":apikey,
            "api_secret":apisecret,
            "data":{
                    "uid":client_id,
                    "norenordno":orderno,
                   }
             }
    url = self.burl +"CancelOrder"          
    response = requests.post(url,json.dumps(data), headers= {'Content-Type': 'application/json'})
    print(response)
    jsonValue = response.json()
    print(jsonValue)
    return  jsonValue        
              
  def user_details(self,client_id):
    apikey=self.apikey
    apisecret=self.apisecret
    data = {
            "api_key":apikey,
            "api_secret":apisecret,
            "data":{
                    "uid":client_id,
                    
                   }
             }
    url = self.burl +"UserDetails"          
    response = requests.post(url,json.dumps(data), headers= {'Content-Type': 'application/json'})
    print(response)
    jsonValue = response.json()
    print(jsonValue)
    return  jsonValue                  

  def limits(self,client_id):
    apikey=self.apikey
    apisecret=self.apisecret
    data = {
            "api_key":apikey,
            "api_secret":apisecret,
            "data":{
                    "uid":client_id,
                    "actid":client_id
                    
                   }
             }
    url = self.burl +"Limits"         
    response = requests.post(url,json.dumps(data), headers= {'Content-Type': 'application/json'})
    print(response)
    jsonValue = response.json()
    print(jsonValue)
    return  jsonValue 

  def holdings(self,client_id,product):
    apikey=self.apikey
    apisecret=self.apisecret
    data = {
            "api_key":apikey,
            "api_secret":apisecret,
            "data":{
                    "uid":client_id,
                    "actid":client_id,
                    "prd":product,
                    
                   }
             }
    url = self.burl +"Holdings"         
    response = requests.post(url,json.dumps(data), headers= {'Content-Type': 'application/json'})
    print(response)
    jsonValue = response.json()
    print(jsonValue)
    return  jsonValue  

  def order_book(self,client_id):
    apikey=self.apikey
    apisecret=self.apisecret
    data = {
            "api_key":apikey,
            "api_secret":apisecret,
            "data":{
                    "uid":client_id,
                    "actid":client_id
                    
                   }
             }
    url = self.burl +"OrderBook"         
    response = requests.post(url,json.dumps(data), headers= {'Content-Type': 'application/json'})
    print(response)
    jsonValue = response.json()
    print(jsonValue)
    return  jsonValue       

  def Single_hist(self,client_id,orderno):
    apikey=self.apikey
    apisecret=self.apisecret
    data = {
            "api_key":apikey,
            "api_secret":apisecret,
            "data":{
                    "uid":client_id,
                    "actid":client_id,
                    "norenordno":orderno
                    
                   }
             }
    url = self.burl +"SingleOrdHist"         
    response = requests.post(url,json.dumps(data), headers= {'Content-Type': 'application/json'})
    print(response)
    jsonValue = response.json()
    print(jsonValue)
    return  jsonValue  

  def position_book(self,client_id):
    apikey=self.apikey
    apisecret=self.apisecret
    data = {
            "api_key":apikey,
            "api_secret":apisecret,
            "data":{
                    "uid":client_id,
                    "actid":client_id,
                    
                    
                   }
             }
    url = self.burl +"PositionBook"         
    response = requests.post(url,json.dumps(data), headers= {'Content-Type': 'application/json'})
    print(response)
    jsonValue = response.json()
    print(jsonValue)
    return  jsonValue             
                              
 
  def trade_book(self,client_id):
    apikey=self.apikey
    apisecret=self.apisecret
    data = {
            "api_key":apikey,
            "api_secret":apisecret,
            "data":{
                    "uid":client_id,
                    "actid":client_id,
                    
                    
                   }
             }
    url = self.burl +"TradeBook"         
    response = requests.post(url,json.dumps(data), headers= {'Content-Type': 'application/json'})
    print(response)
    jsonValue = response.json()
    print(jsonValue)
    return  jsonValue                                         

  def get_quotes(self,client_id,exchange,token):
    apikey=self.apikey
    apisecret=self.apisecret
    data = {
            "api_key":apikey,
            "api_secret":apisecret,
            "data":{
                    "uid":client_id,
                    "actid":client_id,
                    "exch":exchange,
                    "token":token
                    
                    }
             }
    url = self.burl +"GetQuotes"         
    response = requests.post(url,json.dumps(data), headers= {'Content-Type': 'application/json'})
    print(response)
    jsonValue = response.json()
    print(jsonValue)
    return  jsonValue 









