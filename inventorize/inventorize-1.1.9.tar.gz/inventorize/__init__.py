
import sklearn
import numpy
import scipy
import pandas
import math
import plotly
import warnings

def ABC(data):
     """Identyfing ABC category based on the pareto rule.A
         category is up to 80%. B category is up 95% and C category is up to 100%.

     Args:
         data ([pandas.Dataframe]): [Data frame of two columns,first column is the item name, 
         second column is the item value/flow/demand.]

     Returns:
         [pandas.Dataframe]: [a dataframe that contains ABC categories 
         with a bar plot of the count of items in each category.]

         """
     def category(x):
         if (x <0.8):
             return('A')
         elif (x< 0.95):
             return('B')
         else:
             return('C')
     data1= pandas.DataFrame(data)
     data1['Percentage']= data1.iloc[:,1]/sum(data1.iloc[:,1])
     data1= data1.sort_values(by='Percentage',ascending=False)
     data1['comulative']= data1.Percentage.cumsum()    
     data1['Category']=data1.comulative.map(category)
     return data1


             

def CriticalRatio(sellingprice,cost,salvage,penality):
   """[returns the critical ratio of a seasonal product]

   Args:
       sellingprice ([float]): [the selling price of the item]
       cost ([float]): [the cost of the item]
       salvage ([float]): [the price of the item at the end of the season,
       if theree is no salvage, zero is inumpyutted]
       penality ([float]): [the penality to be paid foor eevery short item,
       if there is no penality, zero is inumpyuted]

   Returns:
       [float]: [the critical ratio of the item]"""

   a=(sellingprice-cost+penality)/(sellingprice-cost+penality+cost-salvage)
   return a



def CSOE (quantity,demand,standerddeviation,leadtimeinweeks,cost,costSoe,holdingrate):
      
     """
       [Calculating K value that corresponds to the cost per stock out event, how much quantity should be put in stock as a minimum.the function solves for optimum K
      based on the stock out event. It should be noted that the condition(output) should be bigger than 1.
      other wise set K as per management.]

     Args:
      quantity ([int]): [numeric,quantity replinished every cycle.]
      demand ([float]): [numeric,annual Expected  demand of the SKU .]
      standerddeviation ([float]): [numeric,  standard  deviation of the SKU during season.]
      leadtimeinweeks ([int]): [leadtime in weeks of order.]
      cost ([float]): [cost of item.]
      costSoe ([float]): [estimated cost per stockout event.]
      holdingrate ([float]): [holding rate per item per year,
      percentage.]
     Returns:
       [pandas.DataFrame]: [a dataframe that contains calculations 
       of K and the minimum quantity to be put in stock .]

     """
     DL= demand* leadtimeinweeks/52
     sigmadl= standerddeviation *numpy.sqrt(leadtimeinweeks/52)
     holdingcost= holdingrate*cost
     condition=(demand*costSoe)/(holdingcost*quantity*sigmadl*numpy.sqrt(2*numpy.pi))
     k= numpy.sqrt(2*numpy.log(condition))
     s= DL+sigmadl*k
     a= {'demandleadtime':DL,
                     'sigmadl': sigmadl,
                     'condition':condition,
                     'k':k,'min': s}
     return(a)



def dlsigmadl(expected_demand,sd_demand,expected_leadtime,sd_leadtime):
  """
  [calculating leadtime with leadtime 
   variablility as delivery time diffires to long distances and reliability of mode of transport.
   thus demand leadtime and standard deviation 
   during lead time takes into consideration the lead time variability.]

  Args:
      expected_demand ([float]): [expected_demand, numeric,expected daily demand .]
      sd_demand ([float]): [standard deviation of daily demand .]
      expected_leadtime ([float]): [standard deviation of daily demand .]
      sd_leadtime ([float]): [expected leadtime in days.]

  Returns:
      [dict]: [a dataframe that contains calculations of the expected demand lead time and the expected saftey stock during leadtime. It is noted that saftey stock here is
      more than normal due to leadtime variability.]
      
  Examples:
      [dl.sigmadl(expected_demand=100,sd_demand=22,expected_leadtime=12,sd_leadtime=3)]    
      
  """
  DL= expected_demand*expected_leadtime
  sigmadl=numpy.sqrt( (expected_leadtime*(sd_demand)^2)+((expected_demand^2*(sd_leadtime)^2)))
  return({'DL':DL,'sigmadl':sigmadl})


def eoq(annualdemand,orderingcost,purchasecost,holdingrate):
   """
   [economic order quantity.]

   Args:
      annualdemand ([float]): [annualdemand numeric,annual demand of the SKU.]
      orderingcost ([float]): [orderingcost, numeric ordeing cost of the SKU]
      purchasecost ([float]): [numeric, purchase cost per item]
      holdingrate ([float]): [numeric holding rate percentage per item per year.]

   Returns:
     [Dict] :[the eoq,cycle stock time in years and cycle stock time in weeks.]

   Examples:
      [eoq(annualdemand=5000,orderingcost=400,purchasecost=140,holdingrate=0.2)]
   """    
 
   eoq=numpy.sqrt((annualdemand*2*orderingcost)/(purchasecost*holdingrate))
   T_years= eoq/annualdemand
   T_weeks= T_years*52
   return({'EOQ':eoq,'T_years':T_years,'T_weeks':T_weeks})

def eoqsenstivity (quantity,quantityoptimal):
  """
   [the rate of increase of total relevant cost compared to the EOQ.]

   Args:
      quantity ([float]): [quantity numeric,quantity ordered every order cycle.]
      quantityoptimal ([float]): [quantityoptimal , numeric optimal quantity based on EOQ.]

   Returns:
      [float]:[the rate of increase of total relevant cost compared to the EOQ.]

   Examples:
       [eoqsenstivity(quantity=5400,quantityoptimal=6000,na.rm=TRUE)]
  """

  a=(1/2)*((quantity/quantityoptimal)+(quantityoptimal/quantity))
  return a


def EPN_singleperiod(quantity,mean,standerddeviation,p,c,g,b):
   """
  [Calculating expected profit for a newsvendor model.
   based on assumed normal distribution demand.]

   Args:
      quantity ([float]): [numeric,quantity replinished every cycle.]
      mean ([float]): [Expected  demand of the SKU during season.]
      standerddeviation ([type]): [numeric,  standard  deviation of the SKU during season.]
      p ([float]): [numeric,selling price of the SKU]
      c ([float]): [numeric,cost of the SKU]
      g ([float]): [numeric,,salvage or discounted value if sold after season,
      if there is no salvage , zero is placed in the argument.]
      b ([float]): [numeric,
       peanlity cost of not satisfying demand if any, if not,
        zero is placed in the argument.]
   Returns:
       [dict]:[ dict that contains calculations of 
       the expected profit from a newsvendor model based on normal distribution.] 
   Examples:
       [EPN_singleperiod(quantity=40149,mean= 32000,standerddeviation= 11000,p=24,c=10.9,g=7,b=0)]

   """       
   k=(quantity-mean)/standerddeviation
   gk= scipy.stats.norm.pdf(k,0,1)-(k*(1-scipy.stats.norm.cdf(k)))
   eus= gk*standerddeviation
   expectedprofit= (p-g)*mean-(c-g)*quantity-(p-g+b)*eus
   expectedcost=(c-g)*quantity
   expectedshortagecost=(p-g+b)*eus
   expectedrevnue=(p)*mean
   e_sold_fullprice= mean-eus
   sold_discount=quantity-(mean-eus)
   return({'quantity':quantity,
          'demand':mean,
          'sd':standerddeviation,
          'unitshort':eus,
          'shortagecost':expectedshortagecost,
          'cost': expectedcost,
          'revenue':expectedrevnue,
         'profit': expectedprofit,
         'soldatfullprice':e_sold_fullprice,
         'sold_discount':sold_discount})


def EPP_singleperiod(quantity,lambda1,p,c,g,b):
  """[calculating expected profit for a 
  newsvendor model. based on assumed 
  poisson distribution demand.]
                

  Args:
      quantity ([float]): [numeric,quantity to be ordered during season.]
      lambda1 ([float]): [numeric,  mean of the demand based on poisson distribution.]
      p ([float]): [numeric,selling price of the SKU]
      c ([float]): [numeric,cost of the SKU]
      g ([float]): [numeric,,salvage or discounted value if sold after season,if there is no salvage ,
       zero is placed in the argument.]
      b ([float]): [numeric, peanlity cost of not satisfying demand if any,
       if not, zero is placed in the argument.]
   Returns:
      [dict]:[contains calculations of the  expected profit from a newsvendor 
      model based on poisson distribution.] 
   Examples:
      [EPP_singleperiod(quantity=33000,lambda1= 32000,p=24,c=10.9,g=7,b=0)]
                 
  """
  
  

  eus= lambda1-(lambda1* scipy.stats.poisson.cdf(quantity-1,lambda1))-quantity*(1-scipy.stats.poisson.cdf(quantity,lambda1))
  expectedprofit= (p-g+b)*(quantity*scipy.stats.poisson.cdf(quantity-1,lambda1))- (quantity* scipy.stats.poisson.cdf(quantity,lambda1))
  + (p-c+b)*quantity-(b*lambda1)
  expectedunitsold= lambda1*scipy.stats.poisson.cdf(quantity-1,lambda1)+quantity*(1-scipy.stats.poisson.cdf(quantity,lambda1))
  CDF= scipy.stats.poisson.cdf(quantity,lambda1)
  return({'quantity':quantity,
          'lambda':lambda1,
          'lost_sales':eus,
          'expected_sales':expectedunitsold,
          'expectedprofit':expectedprofit,
          'CDF':CDF})

def EUSnorm_singleperiod(quantity,demand,standerddeviation):
  """[Calculating expected unit short 
  based on an assumed normal 
  distribution for a newsvendor model.]


  Args:
      quantity ([float]): [numeric,quantity replinished every cycle.]
      demand ([float]): [annual Expected  demand of the SKU]
      standerddeviation ([float]): [standard  deviation of the SKU during season.]

  Returns:
      [dict]: [ dict that contains Expected unit short,k and g(k).]
  Examples:
      EUSnorm_singleperiod(quantity=35000,demand=32000,standerddeviation=12000)
 """
  k=(quantity-demand)/standerddeviation
  gk= scipy.stats.norm.pdf(k,0,1)-(k*(1-scipy.stats.norm.cdf(k)))
  eus= gk*standerddeviation
  return {'k':k,'gk':gk,'eus':eus}








def Hibrid_normal(demand,mean,sd,leadtime,service_level,Review_period,Min,Max=False,
                             shortage_cost= False,inventory_cost=False,
                             ordering_cost=False):
  """[The Function takes a demand vector, mean of demand ,sd,lead time and 
   requested service level to simulate and inventory system, 
   orders are lost if inventory level is less than requested demand, also ordering is made at
   day t+1, metrics like item fill rate and cycle service level are calculated.
   the order up to level is calculated based on the review period,lead time and normal distribution.
   Inventory is replenished if inventory position is below min or it is time for review period.]

  Args:
      demand ([float]): [demand  A vector of demand in N time periods.]
      mean ([float]): [average demand in N time periods.]
      sd ([float]): [standard deviation in N time periods]
      leadtime ([float]): [lead time from order to arrival]
      service_level ([float]): [cycle service level requested]
      Review_period ([float]): [ the period where the ordering happens.]
      Min ([float]): [min quantity for order up to level]
      Max (bool, optional): [max quantity for order up to level,if FALSE, then calculated automatically.]
      shortage_cost (bool, optional): [shortage cost per unit of sales lost]. Defaults to False.
      inventory_cost (bool, optional): [inventory cost per unit.]. Defaults to False.
      ordering_cost (bool, optional): [ordering cost for every time an order is made.]. Defaults to False.

  Returns:
      [list]: [a list of two date frames, the simulation and the metrics.]

  Examples:
       Hibrid_normal(demand=rpois(80,6),mean=4,sd=0.2,leadtime=5,service_level=0.95,
       Review_period =9,min=30,
       shortage_cost= FALSE,inventory_cost=FALSE,
       ordering_cost=FALSE)
  """
 
  
  L = leadtime
  
           
  
  def Max1():
      if(Max==False):
             Max_order= round((mean *(leadtime+Review_period))+ ((sd*numpy.sqrt(leadtime+Review_period))* scipy.stats.norm.ppf(service_level)))
      else:
             Max_order= Max
      return Max_order
  
  Max_order=Max1()                       
  N = len(demand) 
  saftey_stock= ((sd*numpy.sqrt(leadtime+Review_period))* scipy.stats.norm.ppf(service_level))               
  order = numpy.zeros(N+1)
  I = numpy.zeros(N+1)
  IP = numpy.zeros(N+1)
  sales = numpy.zeros(N+1)
  recieved = numpy.zeros(N+1)
  
  


  order[0]=0
  demand= numpy.append(numpy.array(0),demand)
  
  IP[0] = I[0] = Max_order
  def numpy_rep(x, reps=1, each=False, length=0):
   
    if length > 0:
        reps = numpy.int(numpy.ceil(length / x.size))
    x = numpy.repeat(x, reps)
    if(not each):
        x = x.reshape(-1, reps).T.ravel() 
    if length > 0:
        x = x[0:length]
    return(x)
  
  
  ordering_time= numpy_rep(numpy.repeat([0,1], [Review_period-1,1]),each=False,reps=len(demand))
  ordering_time=numpy.append(numpy.array(0), ordering_time)
  
  def hibrid_fun(t):
      
      if((IP[t-1] <= Min)):
                 a= (Max_order - IP[t-1]) * (IP[t-1] <= Min)
      if not(IP[t-1] <= Min) :
                  a=(Max_order - IP[t-1]) * (ordering_time[t])           
      return a
  
  for t in range(1,L+1):
    sales[t] = min (demand[t], I[t-1])
    I[t] = I[t-1] - sales[t]
    order[t] = hibrid_fun(t)
    IP[t] =  IP[t-1] + order[t] - sales[t]
    
  
  
  for t in range(L+1,N+1):
    sales[t] = min(demand[t], I[t-1] + order[t-L])
    I[t] = I[t-1] + order[t-L] - sales[t]
    order[t] = hibrid_fun(t)
    IP[t] = IP[t-1] + order[t] - sales[t]
    recieved[t]= order[t-L]
  
  
  data=pandas.DataFrame({'period':range(1,N+2),'demand':demand,'sales':sales,'inventory_level':I,'min':int(Min),
                   'inventory_position':IP,'order': order,'max':int(Max_order),
                   'recieved':recieved},index=range(1,N+2))
  
  data['lost_order']= data['demand'] - data['sales']
  
  metrics= {'shortage_cost': sum(data['lost_order'])*shortage_cost,
                       'inventory_cost': sum(data['inventory_level'])*inventory_cost,
                       'average_inventory_level': data['inventory_level'].mean(),
                       'ordering_cost':  len(data['order'][data['order']>0]) *ordering_cost,
                       'total_lost_sales': sum(data['lost_order']),
                       'Item_fill_rate': 1-(sum(data['lost_order'][data['lost_order']>0]))/sum(demand[1:(len(demand)-1)]),
                       'cycle_service_level': 1-(len(data['lost_order'][data['lost_order']>0])/(len(demand)-1)),
                       'saftey_stock':saftey_stock}
  a= [data,metrics]
  return a                
  









def Hibrid_pois(demand,lambda1,leadtime,service_level,Review_period,Min,Max=False,
                             shortage_cost= False,inventory_cost=False,
                             ordering_cost=False):
  """[The Function takes a demand vector, mean of demand ,sd,lead time and 
     requested service level to simulate and inventory system, 
     orders are lost if inventory level is less than requested demand, also ordering is made at
     day t+1, metrics like item fill rate and cycle service level are calculated.
     the order up to level is calculated based on the review period,lead time and normal distribution.
     Inventory is replenished if inventory position is below min or it is time for review period.]

  Args:
      demand ([float]): [A vector of demand in N time periods.]
      lambda1 ([int]): [rate of demand in N time periods.]
      leadtime ([float]): [leadtime from order to dlivery]
      service_level ([float]): [cycle service level requested]
      Review_period ([int]): [the period where the ordering happens.]
      Min ([type]): [min quantity for order up to level]
      Max (bool, optional): [min quantity for order up to level,if FALSE, then calculated automatically.]. Defaults to False.
      shortage_cost (bool, optional): [shortage cost per unit of sales lost]. Defaults to False.
      inventory_cost (bool, optional): [inventory cost per unit]. Defaults to False.
      ordering_cost (bool, optional): [ordering cost for every time an order is made]. Defaults to False.

  Returns:
      [list]: [a list of two date frames, the simulation and the metrics.]

  Examples:
        [Hibrid_pois(demand,lambda1=4,service_level=0.65,
           Review_period =9,Min=30,Max=50,
          shortage_cost= False,inventory_cost=False,ordering_cost=False)]

  
"""

 
  L = leadtime
  
           
  
  def Max1():
      if(Max==False):
             Max_order=  scipy.stats.poisson.ppf(service_level,lambda1)*(leadtime+Review_period)
      else:
             Max_order= Max
      return Max_order
  
  Max_order=Max1()                       
  N = len(demand) 
  saftey_stock= Max_order- (lambda1*leadtime)             
  order = numpy.zeros(N+1)
  I = numpy.zeros(N+1)
  IP = numpy.zeros(N+1)
  sales = numpy.zeros(N+1)
  recieved = numpy.zeros(N+1)
  
  


  order[0]=0
  demand= numpy.append(numpy.array(0),demand)
  
  IP[0] = I[0] = Max_order
  def numpy_rep(x, reps=1, each=False, length=0):
    """ implementation of functionality of rep() and rep_len() from R

    Attributes:
        x: numpy array, which will be flattened
        reps: int, number of times x should be repeated
        each: logical; should each element be repeated reps times before the next
        length: int, length desired; if >0, overrides reps argument
    """
    if length > 0:
        reps = numpy.int(numpy.ceil(length / x.size))
    x = numpy.repeat(x, reps)
    if(not each):
        x = x.reshape(-1, reps).T.ravel() 
    if length > 0:
        x = x[0:length]
    return(x)
  
  
  ordering_time= numpy_rep(numpy.repeat([0,1], [Review_period-1,1]),each=False,reps=len(demand))
  ordering_time=numpy.append(numpy.array(0), ordering_time)
  
  def hibrid_fun(t):
      
      if((IP[t-1] <= Min)):
                 a= (Max_order - IP[t-1]) * (IP[t-1] <= Min)
      if not(IP[t-1] <= Min) :
                  a=(Max_order - IP[t-1]) * (ordering_time[t])           
      return a
  
  for t in range(1,L+1):
    sales[t] = min (demand[t], I[t-1])
    I[t] = I[t-1] - sales[t]
    order[t] = hibrid_fun(t)
    IP[t] =  IP[t-1] + order[t] - sales[t]
    
  
  
  for t in range(L+1,N+1):
    sales[t] = min(demand[t], I[t-1] + order[t-L])
    I[t] = I[t-1] + order[t-L] - sales[t]
    order[t] = hibrid_fun(t)
    IP[t] = IP[t-1] + order[t] - sales[t]
    recieved[t]= order[t-L]
  
  
  data=pandas.DataFrame({'period':range(1,N+2),'demand':demand,'sales':sales,'inventory_level':I,'min':int(Min),
                   'inventory_position':IP,'order': order,'max':int(Max_order),
                   'recieved':recieved},index=range(1,N+2))
  
  data['lost_order']= data['demand'] - data['sales']
  
  metrics= {'shortage_cost': sum(data['lost_order'])*shortage_cost,
                       'inventory_cost': sum(data['inventory_level'])*inventory_cost,
                       'average_inventory_level': data['inventory_level'].mean(),
                       'ordering_cost':  len(data['order'][data['order']>0]) *ordering_cost,
                       'total_lost_sales': sum(data['lost_order']),
                       'Item_fill_rate': 1-(sum(data['lost_order'][data['lost_order']>0]))/sum(demand[1:(len(demand)-1)]),
                       'cycle_service_level': 1-(len(data['lost_order'][data['lost_order']>0])/(len(demand)-1)),
                       'saftey_stock':saftey_stock}
  a= [data,metrics]
  return a                
  







      
  

def inventorymetricsCIS (CIS,demand,standerddeviation,quantity,leadtime,cost,holdingrate):
  """[calculating inventory metrics based on cost per item short.

     after cost per item short is explicitly  calculated, item fill rate, cost per stock out event and cycle service level
     are implicitly calculated.]

  Args:
      CIS ([float]): [CIS numeric,cost per item short determined by management]
      demand ([float]): [demand numeric,annual demand of the SKU.
      standerddeviation ([float]): [numeric, annual standard  deviation]
      quantity ([float]): [numeric,quantity replinished every cycle.]
      leadtime ([float]): [leadtime, numeric,leadtime in weeks
      cost ([float]): [cost, numeric cost of the SKU]
      holdingrate ([float]): [holdingrate ,numeric, holding rate per item/year]

  Returns:
     [dict] :[ dict that contains demand leadtime,sigmadl(standard deviation in leadtime),saftey factor k determined
      based on cost per itemshort,unit normal loss function,expected units to be short,cycle service level, fill rate,implied cost
      per stockout event, saftey stock and suggested reorder point.] 

  Examples:
      [inventorymetricsCIS(CIS= 90, demand= 35000,standerddeviation=9000,
       quantity= 9000,leadtime=3 ,cost=90,holdingrate=0.15)]

    
      """       

  DL= demand* (leadtime/52)
  sigmadl= standerddeviation *numpy.sqrt(leadtime/52)
  holdingcost= holdingrate*cost
  condition= (quantity*holdingcost)/(demand*CIS)
  Xpro=1-condition
  k= scipy.stats.norm.ppf(Xpro)
  csl=scipy.stats.norm.cdf(k)
  gk= scipy.stats.norm.pdf(k,0,1)-(k*(1-scipy.stats.norm.cdf(k)))
  eus= gk*sigmadl
  safteystock= sigmadl*k
  reorder_point= DL+sigmadl*k
  CSOE= math.exp(k**2/2)*(holdingcost*quantity*sigmadl*numpy.sqrt(2*numpy.pi))*(1/demand)
  fillrate= 1- (eus/quantity)
  return({'DL': DL,'sigmadl':sigmadl,'k':k,'gk':gk,'eus':eus,'csl':csl,'fillrate':fillrate,
                    'CIS':CIS,'CSOE':CSOE,'safteystock':safteystock,'reorder_point':reorder_point})







def inventorymetricsCSL (csl,demand,standerddeviation,quantity,leadtime,cost,holdingrate):
  """[cycle service level is the desired no of times demand is compleltey fulfiiled from cycle stock,after cycle service level  
    is explicitly  calculated, cost per item short, cost per stock out event and item fill rate
      are implicitly calculated.]

  Args:
      csl ([float]): [csl numeric,required times of demand that is fullfilled from cycle stock]
      demand ([type]): [demand numeric,annual demand of the SKU.]
      standerddeviation ([type]): [standerddeviation numeric, annual standard  deviation]
      quantity ([type]): [numeric,quantity replinished every cycle.]
      leadtime ([type]): [leadtime, numeric,leadtime in weeks]
      cost ([type]): [numeric,cost of the SKU.]
      holdingrate ([type]): [holding rate per item per year.]
  Returns:
     [dict] :[ based on item fillrate provided, unit normal loss function, expected units to be short, cycle service level, fill rate,implied cost
               per stockout event, saftey stock and suggested reorder point.] 

  Examples:
      [inventorymetricsCSL(csl=0.95,demand=20000,standerddeviation=1200,
       quantity=4500,leadtime=3,cost=100,holdingrate=0.15)
        ]
    """
 
   
  DL= demand* leadtime/52
  sigmadl= standerddeviation *numpy.sqrt(leadtime/52)
  holdingcost= holdingrate*cost
  k= scipy.stats.norm.ppf(csl)
  gk= scipy.stats.norm.pdf(k,0,1)-(k*(1-scipy.stats.norm.cdf(k)))
  eus= gk*sigmadl
  fillrate= 1- (eus/quantity)
  CIS= (quantity*holdingcost)/(demand*(1-csl))
  CSOE= math.exp(k**2/2)*(holdingcost*quantity*sigmadl*numpy.sqrt(2*numpy.pi))*(1/demand)
  safteystock= k*sigmadl
  reorder_point= k*sigmadl+DL
  return({'DL':DL,'sigmadl':sigmadl,'k':k,'gk':gk,'eus':eus,'csl':csl,'fillrate':fillrate,
                      'CIS':CIS,'CSOE':CSOE,'safteystock':safteystock,'reorder_point':reorder_point})
  









def linear_elasticity (prices,Sales,present_price,cost_of_product):
  """[This function is helpful to determine if your product is elastic or not based on a linear price response function. 
     if product demand is
    not linear to price, try using the single product optimization function instead. The price elasticity of demand
    which is often shortened to demand elasticity
    is defined to be the percentage change in quantity demanded, q, divided by the percentage change in price, p.   When |E| > 1, we say the good is price elastic.In this case, % change Q > % change P, and so, for a 1 % 
     change in price, there is a greater than 1 %
     change in quantity demanded.In this case, management should decrease price to have a higher revenue.
    When |E| < 1, we say the good is price inelastic.In this case, % change Q < % change P, and so, 
   for a 1 % change in price, there is a less than 1 % change
   in quantity demanded.In this case, management should increase price to have a higher revenue.
    When |E|  1, we say the good is price unit elastic.In this case, % change Q  % change P , 
   and so, for a 1% change in price,
   there is also an 1% change in quantity demanded.
   This is the optimal price which means it maximizes revenue.]

  Args:
      prices ([float): [Vector of sales against each price.]
      Sales ([float]): [Vector of sales against each price.]
      present_price ([float]): [numeric,  present price of the product .]
      cost_of_product ([float]): [cost of the product, if the product/service has no cost ,then cost is set to zero.]
  Returns:
  [dict]: [the elasticity at the present price , the price for optimum revenue and thee price for optimum cost.]     

  Examples:
  [linear_elasticity(prices,Sales,present_price,cost_of_product)]

 """
  """    """  
  data=pandas.DataFrame({'price':prices,'Sales': Sales})
  X =data[['price']].values
  y =data[['Sales']].values

  lm_model=sklearn.linear_model.LinearRegression().fit(X,y)
  intercept =lm_model.intercept_[0]
  derv_p =lm_model.coef_
  
  Elasticity1 = ((-1 *present_price)/(intercept+present_price*derv_p))*derv_p

  optimum_profit=(-derv_p*cost_of_product+ intercept)/(2*-derv_p)
  optimum_revenue =intercept/(2*-derv_p)
  simulation_data=pandas.DataFrame({'prices': range(int(min(prices)),int(max(optimum_profit,optimum_revenue)*1.3))})
  simulation_data['Sales']=lm_model.predict(simulation_data[['prices']])
  simulation_data['revenue']=simulation_data['Sales']*simulation_data['prices']
  simulation_data['profit'] =(simulation_data['prices']*simulation_data['Sales'] )  -(simulation_data.Sales*cost_of_product)

  
  data_final={'Elasticity':Elasticity1,'optimum_price_profit':optimum_profit,
                       'optimum_price_revenue':optimum_revenue}
  return data_final





def MPN_singleperiod (mean,standerddeviation,p,c,g,b):
   """[calculating expected profit for a newsvendor model. based on assumed normal distribution demand.]

   Args:
      mean ([float]): [numeric,Expected  demand of the SKU during season.]
      standerddeviation ([type]): [numeric,  standard  deviation of the SKU during season]
      p ([float]): [numeric,selling price of the SKU]
      c ([float]): [ numeric,cost of the SKU]
      g ([float]): [salvage or discounted value if sold after season,if there is no salvage , zero is placed in the argument.]
      b ([float]): [peanlity cost of not satisfying demand if any, if not, zero is placed in the argument.]
  Examples:
       [MPN_singleperiod(mean= 32000,standerddeviation= 11000,p=24,c=10.9,g=7,b=0)]
  Returns:
  [dict]: [contains calculations of the maximum expected profit from a newsvendor model based on normal distribution.]
       
  """

  
   quantity= scipy.stats.norm.ppf((p-c+b)/(p-c+b+c-g),mean,standerddeviation)
   k= (quantity-mean)/standerddeviation
   gk= scipy.stats.norm.pdf(k,0,1)-(k*(1-scipy.stats.norm.cdf(k)))
   eus= gk*standerddeviation
   expectedprofit= (p-g)*mean-(c-g)*quantity-(p-g+b)*eus
   expectedcost=(c-g)*quantity
   expectedshortagecost=(p-g+b)*eus
   expectedrevnue=(p)*mean
   e_sold_fullprice= mean-eus
   sold_discount=quantity-(mean-eus)
   return({'quantity':quantity,
          'demand':mean,
          'sd':standerddeviation,
          'unitshort':eus,
          'shortagecost':expectedshortagecost,
          'cost': expectedcost,
          'revenue':expectedrevnue,
         'profit': expectedprofit,
         'soldatfullprice':e_sold_fullprice,
         'sold_discount':sold_discount})









def MPP_singleperiod(lambda1,p,c,g,b):
  """[calculating expected profit for a newsvendor model. based on assumed poisson distribution demand based on the critical ratio.]

  Args:
      lambda1 ([int]): [lambda1 numeric,  mean of the demand based on poisson distribution.]
      p ([float]): [numeric,selling price of the SKU]
      c ([float]): [numeric,cost of the SKU]
      g ([float]): [numeric,,salvage or discounted value if sold after season,if there is no salvage , zero is placed in the argument.]
      b ([float]): [numeric, peanlity cost of not satisfying demand if any, if not, zero is placed in the argument.]
  Returns:
      [dict]:[contains calculations of the maximum expected profit from a newsvendor model based on poisson distribution.]
  Examples:
      [ MPP_singleperiod(lambda1= 32000,p=24,c=10.9,g=7,b=0,na.rm=TRUE)]     
  """

  """   """
  CR= (p-c+b)/(p-c+b+c-g)
  quantity= scipy.stats.poisson.ppf(CR,lambda1)
  eus= lambda1-(lambda1*scipy.stats.poisson.cdf(quantity-1,lambda1))-quantity*(1-scipy.stats.poisson.cdf(quantity,lambda1))
  expectedprofit= (p-g+b)*(quantity*scipy.stats.poisson.cdf(quantity-1,lambda1))- (quantity*scipy.stats.poisson.cdf(quantity,lambda1))
  + (p-c+b)*quantity-(b*lambda1)
  expectedunitsold= lambda1*scipy.stats.poisson.cdf(quantity-1,lambda1)+quantity*(1-scipy.stats.poisson.cdf(quantity,lambda1))
  CDF= CR
  return({'quantity':quantity,'lambda1':lambda1,'lost_sales':eus,
                    'expected_sales':expectedunitsold,'expectedprofit':expectedprofit,'CDF':CDF})

def Multi_Competing_optimization(X,y,n_variables,initial_products_cost):
  """[Calculating the optimum price based on consumer choice model for products that competes with each other.]

  Args:
      X ([pandas.DataFrame]): [a data frame of product prices at every event.]
      y ([array]): [integer vector with choices of a customer at each event , for example if the competing products are only three ,
       the possible choices are NA,1,2,3. NA being a consumer did not buy any thing at this event and he chose to walk away.]
      n_variables ([int]): [Number of products competing with each other.]
      initial_products_cost ([float]): [a vector of current costs for each product,for example if we have three products ,
      it could be c(1.8,2.5,3.9).orif there is no costs , it would be [0,0,0]]

  Returns:
      [dict]: [the product names which are names of X,the intrinsic utility value,the current cost and the scipy.optimized price for each product]
  Examples:
      [Multi_Competing_optimization(X= pandas.DataFrame({'Chedar_Cheese':numpy.random.uniform(10,15,100),
       'Mozarella':numpy.random.uniform(8,10,100),'Parmesan':numpy.random.uniform(9,12,100)}),y= numpy.array([1,2,3,1,2]*20),n_variables =3,initial_products_cost =[8,6,7])]
  """

 
  data=X.copy()
  data['y']=y
  prices= numpy.array(X.max())
  costs =initial_products_cost
  initial_value= numpy.nanmean(X.values)
  n_variables=n_variables
  variables= numpy.repeat(initial_value,n_variables)

  def multi_revenue_function(X,y,initial_value,n_variables):

   initial_value=initial_value
   n_variables=n_variables
   variables= numpy.repeat(initial_value,n_variables)



   y=numpy.array(data["y"])

   def f (variables):


       summed=pandas.DataFrame(numpy.zeros((len(data),len(X.columns))))


       for i in range(0,len(summed)):
           for j in range(0,len(variables)):
            summed.iloc[i,j]=numpy.exp(variables[j]-X.iloc[i,j])
        

       summed['sum']= summed.sum(axis=1)

       def log_fun(x):
         if (sum(numpy.isnan(y))== 0):
             a=numpy.log(summed['sum'])
         else :
             a=numpy.log(1+summed['sum'])
         return a
       data['loglikebottom']= log_fun(y)


       def offset_func(variables,data,rows,x):
           if(numpy.isnan(x)):
             a= 0
           else:
             a= variables[x-1]-data.iloc[rows,x-1]
  
           return a
  

       data['dummy']='NA'
       for i in range(0,len(data)):
         data['dummy'][i]= offset_func(variables,data,i,y[i])

  


       objective_function= sum(data['dummy'])-sum(data['loglikebottom'])
       return -(objective_function)
   bnds = ((0,X.values.max()*2),)*n_variables

   Y= scipy.optimize.minimize(f, variables, method= 'L-BFGS-B', tol=1e-6,bounds=bnds)
   return(Y)



  p=multi_revenue_function(X,y,initial_value,n_variables)
  values=p.x

  def f1(prices):
      
       r= prices-costs
       v= numpy.exp(values-prices)
       prob= v/(1+sum(v))
       profit= prob*r

       total_profit= sum(profit)
       return(-total_profit)

  prices1=numpy.array(X.mean())
  bnds = ((0,X.values.max()*2),)*n_variables

  y2=  scipy.optimize.minimize(f1, prices1, method= 'L-BFGS-B', tol=1e-6,bounds=bnds)
  final_data=pandas.DataFrame({'Product_name':X.columns,'utitliy_of_product':values,'scipy.optimized_prices':y2.x,'cost':costs})

  return final_data










def Periodic_review_normal(demand,mean,sd,leadtime,service_level,Review_period,Max=False,
                             shortage_cost= False,inventory_cost=False,
                             ordering_cost=False):
  """[The Function takes a demand vector, mean of demand ,sd,lead time and requested service level to simulate and inventory system, 
  orders are lost if inventory level is less than requested demand, also ordering is made atday t+1,
   metrics like item fill rate and cycle service level are calculated.
   the order up to level is calculated based on the review period,lead time and normal distribution .]

  Args:
      demand ([float]): [A vector of demand in N time periods.]
      mean ([float]): [average demand in N time periods.]
      sd ([float]): [standard deviation in N time periods.]
      leadtime ([float]): [lead time from order to arrival]
      service_level ([float]): [cycle service level requested]
      Review_period ([float]): [the period where the ordering happens.]
      Max (bool, optional): [Max is calculated automatically if set to default]. Defaults to False. if False, Max is set automatically.
      shortage_cost (bool, optional): [description]. Defaults to False.
      inventory_cost (bool, optional): [description]. Defaults to False.
      ordering_cost (bool, optional): [description]. Defaults to False.
  Returns:
  [list]: [a data frame of simulation and  dict that has the inventory metrics]
  Examples:
  ['Periodic_review_normal(demand=round(numpy.random.uniform(10,20,300)),mean=6,sd=0.2,leadtime=5,service_level=0.95,
   Review_period =9,Max=False,shortage_cost= FALSE,inventory_cost=FALSE,ordering_cost=FALSE)]
   
   """
 
  
  L = leadtime
  warnings.simplefilter('once', UserWarning)
  warnings.warn(' This function is deprecated, Kindly use periodic_policy() instead or periodic_policy_dynamic() for forecasting ')
  
           
  
  def Max1():
      if(Max==False):
             Max_order= round((mean *(leadtime+Review_period))+ ((sd*numpy.sqrt(leadtime+Review_period))* scipy.stats.norm.ppf(service_level)))
      else:
             Max_order= Max
      return Max_order
  
  Max_order=Max1()                       
  N = len(demand) 
  saftey_stock= ((sd*numpy.sqrt(leadtime+Review_period))* scipy.stats.norm.ppf(service_level))               
  order = numpy.zeros(N+1)
  I = numpy.zeros(N+1)
  IP = numpy.zeros(N+1)
  sales = numpy.zeros(N+1)
  recieved = numpy.zeros(N+1)
  
  


  order[0]=0
  demand= numpy.append(numpy.array(0),demand)
  
  IP[0] = I[0] = Max_order
  def numpy_rep(x, reps=1, each=False, length=0):
    
    if length > 0:
        reps = numpy.int(numpy.ceil(length / x.size))
    x = numpy.repeat(x, reps)
    if(not each):
        x = x.reshape(-1, reps).T.ravel() 
    if length > 0:
        x = x[0:length]
    return(x)
  
  
  ordering_time= numpy_rep(numpy.repeat([0,1], [Review_period-1,1]),each=False,reps=len(demand))
  ordering_time=numpy.append(numpy.array(0), ordering_time)
  
  for t in range(1,L+1):
    sales[t] = min (demand[t], I[t-1])
    I[t] = I[t-1] - sales[t]
    order[t] = (Max_order- IP[t-1]) * (ordering_time[t])
    IP[t] =  IP[t-1] + order[t] - sales[t]
    
  
  
  for t in range(L+1,N+1):
    sales[t] = min(demand[t], I[t-1] + order[t-L])
    I[t] = I[t-1] + order[t-L] - sales[t]
    order[t] = (Max_order- IP[t-1]) * (ordering_time[t])
    IP[t] = IP[t-1] + order[t] - sales[t]
    recieved[t]= order[t-L]
  
  
  data=pandas.DataFrame({'period':range(1,N+2),'demand':demand,'sales':sales,'inventory_level':I,
                   'inventory_position':IP,'order': order,'max':int(Max_order),
                   'recieved':recieved},index=range(1,N+2))
  
  data['lost_order']= data['demand'] - data['sales']
  
  metrics= {'shortage_cost': sum(data['lost_order'])*shortage_cost,
                       'inventory_cost': sum(data['inventory_level'])*inventory_cost,
                       'average_inventory_level': data['inventory_level'].mean(),
                       'ordering_cost':  len(data['order'][data['order']>0]) *ordering_cost,
                       'total_lost_sales': sum(data['lost_order']),
                       'Item_fill_rate': 1-(sum(data['lost_order'][data['lost_order']>0]))/sum(demand[1:(len(demand)-1)]),
                       'cycle_service_level': 1-(len(data['lost_order'][data['lost_order']>0])/(len(demand)-1)),
                       'saftey_stock':saftey_stock}
  a= [data,metrics]
  return a                
  






def Periodic_review_pois(demand,lambda1,leadtime,service_level,Review_period,Max=False,
                             shortage_cost= False,inventory_cost=False,
                             ordering_cost=False):
  """[The Function takes a demand vector, mean of demand ,sd,lead time and 
      requested service level to simulate and inventory system, 
      orders are lost if inventory level is less than requested demand, also ordering is made at
      day t+1, metrics like item fill rate and cycle service level are calculated.
      the order up to level is calculated based on the review period,lead time and Poisson distribution .]

  Args:
      demand ([float]): [demand of the product over n time periods ]
      lambda1 ([float]): [mean of demand]
      leadtime ([int]): [ N periods from order to delivery]
      service_level ([float]): [cycle service level set]
      Review_period ([float]): [how often the order occures]
      Max (bool, optional): [Max is calculated automatically if set to default]. Defaults to False.
      shortage_cost (bool, optional): [description]. Defaults to False.
      inventory_cost (bool, optional): [description]. Defaults to False.
      ordering_cost (bool, optional): [description]. Defaults to False.

   Returns:
   [list]: [a data frame of simulation and  dict that has the inventory metrics]
   Examples:
   ['Periodic_review_pois(demand=round(numpy.random.uniform(10,20,300)),mean=6,sd=0.2,leadtime=5,service_level=0.95,
   Review_period =9,Max=False,shortage_cost= FALSE,inventory_cost=FALSE,ordering_cost=FALSE)]
"""


  
  L = leadtime
  warnings.simplefilter('once', UserWarning)
  warnings.warn(' This function is deprecated, Kindly use periodic_policy() instead or periodic_policy_dynamic() for forecasting ')
           
  
  def Max1():
      if(Max==False):
             Max_order=  scipy.stats.poisson.ppf(service_level,lambda1)*(leadtime+Review_period)
      else:
             Max_order= Max
      return Max_order
  
  Max_order=Max1()                       
  N = len(demand) 
  saftey_stock= Max_order- (lambda1*leadtime)      
  order = numpy.zeros(N+1)
  I = numpy.zeros(N+1)
  IP = numpy.zeros(N+1)
  sales = numpy.zeros(N+1)
  recieved = numpy.zeros(N+1)
  
  


  order[0]=0
  demand= numpy.append(numpy.array(0),demand)
  
  IP[0] = I[0] = Max_order
  def numpy_rep(x, reps=1, each=False, length=0):
    
    if length > 0:
        reps = numpy.int(numpy.ceil(length / x.size))
    x = numpy.repeat(x, reps)
    if(not each):
        x = x.reshape(-1, reps).T.ravel() 
    if length > 0:
        x = x[0:length]
    return(x)
  
  
  ordering_time= numpy_rep(numpy.repeat([0,1], [Review_period-1,1]),each=False,reps=len(demand))
  ordering_time=numpy.append(numpy.array(0), ordering_time)
  
  for t in range(1,L+1):
    sales[t] = min (demand[t], I[t-1])
    I[t] = I[t-1] - sales[t]
    order[t] = (Max_order- IP[t-1]) * (ordering_time[t])
    IP[t] =  IP[t-1] + order[t] - sales[t]
    
  
  
  for t in range(L+1,N+1):
    sales[t] = min(demand[t], I[t-1] + order[t-L])
    I[t] = I[t-1] + order[t-L] - sales[t]
    order[t] = (Max_order- IP[t-1]) * (ordering_time[t])
    IP[t] = IP[t-1] + order[t] - sales[t]
    recieved[t]= order[t-L]
  
  
  data=pandas.DataFrame({'period':range(1,N+2),'demand':demand,'sales':sales,'inventory_level':I,
                   'inventory_position':IP,'order': order,'max':int(Max_order),
                   'recieved':recieved},index=range(1,N+2))
  
  data['lost_order']= data['demand'] - data['sales']
  
  metrics= {'shortage_cost': sum(data['lost_order'])*shortage_cost,
                       'inventory_cost': sum(data['inventory_level'])*inventory_cost,
                       'average_inventory_level': data['inventory_level'].mean(),
                       'ordering_cost':  len(data['order'][data['order']>0]) *ordering_cost,
                       'total_lost_sales': sum(data['lost_order']),
                       'Item_fill_rate': 1-(sum(data['lost_order'][data['lost_order']>0]))/sum(demand[1:(len(demand)-1)]),
                       'cycle_service_level': 1-(len(data['lost_order'][data['lost_order']>0])/(len(demand)-1)),
                       'saftey_stock':saftey_stock}
  a= [data,metrics]
  return a                
  
def productmix_storelevel(SKUs,sales,revenue,storeofsku):
    """[Identyfing ABC category based on the pareto rule for both demand and selling price,a mix of nine categories are produced.
       Identyfing ABC category based on the pareto rule.A category is up to 80%. B category is up 95% and C category is up to 100%.
       in this fuction the data is splitted by store and a product mix is made on each store individually.]

    Args:
      SKUs ([array]): [charachter, a vector of SKU names.]
      sales ([array]): [a vector of items sold per sku, should be the same number of rows as SKUs.]
      revenue ([array]): [a vector of total revenue  per sku, should be the same number of rows as SKUs.]
      storeofsku ([array]): [vector, which store the SKU is sold at.should be the same number of rows as SKUs.]

    Returns:
      [pandas.DataFrame]: [a dataframe that contains ABC categories by store with a bar plot of the count of items in each category.]
    Examples:
      [ productmix_storelevel(SKUs= numpy.array(range(1,1001)),sales = ales= numpy.random.uniform(1,10000,1000),
      revenue=numpy.random.uniform(1,80000,1000),storeofsku = storeofsku= numpy.array([1,2,3,4,5]).repeat(200)))]
      
    """

  
    def productmix(store):
    


        store['sales_mix']= store['sales']/sum(store['sales'])
        store=store.sort_values(by='sales',ascending= False)
        store['comulative_sales']=store['sales_mix'].cumsum()
        store
        store= store.sort_values(by='revenue',ascending= False)
        store['revenue_mix']= store['revenue']/sum(store['revenue'])
        store['comulative_revenue']= store['revenue_mix'].cumsum()

        ### for abc sales
        def category(x):
                        if (x <0.8):
                          return('A')
                        elif (x< 0.95):
                          return('B')
                        else:
                          return('C')

      

        store['sales_category']= store['comulative_sales'].map(category)
        store['revenue_category']= store['comulative_revenue'].map(category)
        store['product_mix']= store['sales_category']+'_'+store['revenue_category']
        return store


    productdata= pandas.DataFrame({'sku':SKUs,'sales':sales,'revenue':revenue,'storeofsku':storeofsku})
  
    def unique(data_list):
            unique_list= []
            for x in data_list:
                
                if x not in unique_list:
                    
                    unique_list.append(x)
            return unique_list
  
    stores= unique(storeofsku)
    df= pandas.DataFrame({})
    for i in stores:
          store= productdata[ productdata['storeofsku']== i]
          store1= productmix(store)
          df=pandas.concat([df,store1],axis=0)
    return df





def productmix(skus,sales,revenue):
        """[Identyfing ABC category based on the pareto rule for both demand and selling price,a mix of nine categories are produced.
        Identyfing ABC category based on the pareto rule.A category is up to 80%. B category is up 95% and C category is up to 100%.
         ]

        Args:
        SKUs ([array]): [charachter, a vector of SKU names.]
        sales ([array]): [a vector of items sold per sku, should be the same number of rows as SKUs.]
        revenue ([array]): [a vector of total revenue  per sku, should be the same number of rows as SKUs.]
        

        Returns:
        [pandas.DataFrame]: [a dataframe that contains ABC categories by sales and rvenue]
        Examples:
        [ productmix(SKUs= numpy.array(range(1,1001)),sales = ales= numpy.random.uniform(1,10000,1000),
        revenue=numpy.random.uniform(1,80000,1000))]
      
        """
        store= pandas.DataFrame({'skus':skus,'sales':sales,'revenue':revenue})


        store['sales_mix']= store['sales']/sum(store['sales'])
        store=store.sort_values(by='sales',ascending= False)
        store['comulative_sales']=store['sales_mix'].cumsum()
        store
        store= store.sort_values(by='revenue',ascending= False)
        store['revenue_mix']= store['revenue']/sum(store['revenue'])
        store['comulative_revenue']= store['revenue_mix'].cumsum()

        ### for abc sales
        def category(x):
                        if (x <0.8):
                          return('A')
                        elif (x< 0.95):
                          return('B')
                        else:
                          return('C')

      

        store['sales_category']= store['comulative_sales'].map(category)
        store['revenue_category']= store['comulative_revenue'].map(category)
        store['product_mix']= store['sales_category']+'_'+store['revenue_category']
        return store







def reorderpoint_leadtime_variability(dailydemand,dailystandarddeviation,leadtimein_days,sd_leadtime_days,csl):
  """[Calculating re-order point  based on  demand variability and lead time variability in an assumed normal distribution.
       cycle service level is provided to calculate saftey stock accordingly.]

  Args:
      dailydemand ([float]): [dailydemand numeric,daily Expected  demand of the SKU .]
      dailystandarddeviation ([float]): [ailystandarddeviation numeric,  standard  deviation of daily demand of the SKU .]
      leadtimein_days ([float]): [leadtime in days of order.]
      sd_leadtime_days ([float]): [standard deviation of leadtime in days of order.]
      csl ([float]): [cycle service level requested]
  Returns:
    [dict]: [contains demand lead time,sigmadl,safteyfactor and re_order point.]
  Examples:
      reorderpoint_leadtime_variability(dailydemand=50,dailystandarddeviation=5,
      leadtimein_days=6,sd_leadtime_days=2,csl=0.90)
  """
  """   """
  DL= dailydemand*leadtimein_days
  sigmadl=numpy.sqrt( (leadtimein_days*(dailystandarddeviation)**2)+((dailydemand**2*(sd_leadtime_days)^2)))
  safteyfactor= scipy.stats.norm.ppf(csl)
  safteystock=safteyfactor*sigmadl
  quantityinstock= DL+safteystock
  allpar= {"demandleadtime": DL,"sigmadl":sigmadl,"safteyfactor":safteyfactor,"reorder_point":quantityinstock}
  return(allpar)
  







def reorderpoint(dailydemand,dailystandarddeviation,leadtimein_days,csl):
  """[Calculating re-order point  based on  demand variability  in an assumed normal distribution.
       cycle service level is provided to calculate saftey stock accordingly.]

  Args:
      dailydemand ([float]): [dailydemand numeric,daily Expected  demand of the SKU .]
      dailystandarddeviation ([float]): [ailystandarddeviation numeric,  standard  deviation of daily demand of the SKU .]
      leadtimein_days ([float]): [leadtime in days of order.]
      csl ([float]): [cycle service level requested]
  Returns:
    [dict]: [contains demand lead time,sigmadl,safteyfactor and re_order point.]
  Examples:
      reorderpoint_leadtime_variability(dailydemand=50,dailystandarddeviation=5,
      leadtimein_days=6,csl=0.90)
  """      

  DL= dailydemand*leadtimein_days
  sigmadl=dailystandarddeviation*numpy.sqrt(leadtimein_days)
  safteyfactor= scipy.stats.norm.ppf(csl)
  safteystock=safteyfactor*sigmadl
  quantityinstock= DL+safteystock
  allpar= {"demandleadtime": DL,"sigmadl":sigmadl,"safteyfactor":safteyfactor,"reorder_point":quantityinstock}
  return(allpar)







def  saftey_stock_normal (annualdemand,annualstandarddeviation,leadtimeinweeks,csl):
  """[Calculating saftey stock  based on  the cycle service level in   an assumed normal distribution.]

  Args:
      annualdemand ([float]): [annualdemand numeric,annual Expected  demand of the SKU.]
      annualstandarddeviation ([float]): [numeric,  standard  deviation of the SKU during season.]
      leadtimeinweeks ([float]): [leadtimeinweeks  leadtime in weeks or order.]
      csl ([float]): [csl  cycle service level requested]
  Returns:
  [dict]:[contains calculations of saftey stock based on a normal distribution.]

  Examples:
       [saftey_stock_normal(annualdemand=8000,annualstandarddeviation=600,
         leadtimeinweeks=4,csl=0.95)]
  """
  """  """
  demandleadtime= annualdemand *leadtimeinweeks/52
  sigmadl= annualstandarddeviation* numpy.sqrt(leadtimeinweeks/52)
  safteyfactor= scipy.stats.norm.ppf(csl)
  safteystock=safteyfactor*sigmadl
  quantityinstock= demandleadtime+safteystock
  allpar= {"demandleadtime": demandleadtime,"sigmadl":sigmadl,
  "safteyfactor":safteyfactor,"cyclestock+safteystock":quantityinstock}
  return(allpar)
  

def safteystock_CIS_normal(quantity,demand,standerddeviation,leadtimeinweeks,cost,Citemshort,holdingrate):
  """[Calculating K value that reduces cost 
  per item short inventory metric based on an assumed scipy.stats.normal distribution.]

  Args:
      quantity ([float]): [numeric,quantity replinished every cycle.]
      demand ([float]): [numeric,annual Expected  demand of the SKU .]
      standerddeviation ([float]): [numeric,  standard  deviation of the SKU during season.]
      leadtimeinweeks ([float]): [leadtime in weeks or order.]
      cost ([float]): [numeric,cost of the SKU]
      Citemshort ([float]): [numeric, peanlity cost of not satisfying demand if any, if not, zero is placed in the argument.]
      holdingrate ([float]): [numeric,,holding charge per item per year.]
   Returns:
   [dict]: [contains calculations of K the cost per item short metric noting that condition must me less than 1.]
   Examples:
   [safteystock_CIS_normal(quantity=3000,demand=50000,standerddeviation=4000,
                       leadtimeinweeks=4,cost=90,Citemshort=15,holdingrate=0.15)]
   """


  """  """
  DL= demand* leadtimeinweeks/52
  sigmadl= standerddeviation *numpy.sqrt(leadtimeinweeks/52)
  holdingcost= holdingrate*cost
  condition= (quantity*holdingcost)/(demand*Citemshort)
  Xpro=1-condition
  k= scipy.stats.norm.ppf(Xpro)
  gk= scipy.stats.norm.pdf(k,0,1)-(k*(1-scipy.stats.norm.cdf(k)))
  eus= gk*sigmadl
  safteystock= sigmadl*k
  s= DL+sigmadl*k
  return({'DL':DL,'sigmadl':sigmadl,'condition':condition,'k':k,'gk':gk,'eus':eus,'safteystock':safteystock,
          'min':s,'Cycleservicelevel':Xpro})


def safteystock_CSL_normal(rate,quantity,demand,standerddeviation,leadtimeinweeks):
  Dl= demand * (leadtimeinweeks/52)
  sigmadL=standerddeviation*numpy.sqrt(leadtimeinweeks/52)
  k=scipy.stats.norm.ppf(rate)
  gk= scipy.stats.norm.pdf(k,0,1)-(k*(1-scipy.stats.norm.cdf(k)))
  eus= gk*sigmadL
  fillrate= 1- (eus/quantity)
  safteystock= sigmadL*k
  s= Dl+sigmadL*k
  return({'k':k,'gk':gk,'Dl':Dl,'sigmadL':sigmadL,'eus':eus,'min': s,
                     'safteystock':safteystock,'fillrate':fillrate,'cycleservicelevel':rate})


def inventorymetricsIFR(fillrate,demand,standerddeviation,quantity,leadtime,cost,holdingrate):
  """[diffirent inventory metrics based on item fill rate]

  Args:
      fillrate ([float]): [item fill rate is the percentage of demand that is fullfilled directly from the cycle stock,after item fill rate is explicitly calculated,
       cost per item short, cost per stock out event and cycle service level are implicitly calculated.]
      demand ([float]): [numeric,annual demand of the SKU.]
      standerddeviation ([float]): [numeric, annual standard  deviation]
      quantity ([float]): [numeric,quantity replinished every cycle.]
      leadtime ([float]): [numeric,leadtime in weeks]
      cost ([float]): [cost of the sku ]
      holdingrate ([float]): [numeric, holding rate per item/year]

  Returns:
      [dict]: [dict that contains demand leadtime, sigmadl(standard deviation in leadtime), saftey factor k determined
      based on item fillrate provided, unit normal loss function expected units to be short,cycle service level, fill rate,implied cost 
      per stockout event, saftey stock and suggested reorder point.]
  Examples:
   [inventorymetricsIFR(fillrate= 0.90, demand= 35000,standerddeviation=9000,
    quantity= 5000,leadtime=3 ,cost=50,holdingrate=0.15)]
  """
  """  """
  DL= demand* leadtime/52
  sigmadl= standerddeviation *numpy.sqrt(leadtime/52)
  holdingcost= holdingrate*cost
  gk= (quantity/sigmadl)*(1-fillrate)
  def f (k):
          a=(scipy.stats.norm.pdf(k,0,1)-(k*(1-scipy.stats.norm.cdf(k)))-gk)
          return a
  k=scipy.optimize.root(f, [0.1, 1]).x[0]
  eus= gk*sigmadl
  csl=scipy.stats.norm.cdf(k)
  CIS= (quantity*holdingcost)/(demand*(1-csl))
  CSOE= math.exp(k**2/2)*(holdingcost*quantity*sigmadl*numpy.sqrt(2*numpy.pi))*(1/demand)
  safteystock= k*sigmadl
  reorder_point= k*sigmadl+DL
  return({'DL':DL,'sigmadl':sigmadl,'k':k,'gk':gk,'eus':eus,'csl':csl,'fillrate':fillrate,
                    'CIS':CIS,'CSOE':CSOE,'safteystock':safteystock,'reorder_point':reorder_point})

def sim_base_normal(demand,mean,sd,leadtime,service_level,Base=False,ordering_delay=False,
                             shortage_cost=False,inventory_cost=False,
                             ordering_cost=False):
  """[the Function takes a demand vector, mean of demand ,sd,lead time and requested service level to simulate and inventory system, 
      orders are lost if inventory level is less than requested demand, also ordering is made at
      day t+1, metrics like item fill rate and cycle service level are calculated based on a 
      normal distribution.]

  Args:
      demand ([float]): [A vector of demand in N time periods.]
      mean ([float]): [average demand in N time periods.]
      sd ([float]): [standard deviation in N time periods.]
      leadtime ([float]): [lead time from order to arrival]
      service_level ([float]): [cycle service level requested]
      Base (bool, optional): [Set to False for automatic calculation,else manual inumpyut of base.]. Defaults to False.
      ordering_delay (bool, optional): [logical,Default is FALSE,if TRUE, orders are delayed one period.]. Defaults to False.
      shortage_cost (bool, optional): [shortage cost per unit of sales lost]. Defaults to False.
      inventory_cost (bool, optional): [inventory cost per unit.]. Defaults to False.
      ordering_cost (bool, optional): [ordering cost for every time an order is made.]. Defaults to False.

  Returns:
      [list]: [a data frame of the simulation and  dict of the metrics]

  Examples:
   sim_base_normal(demand=numpy.random.uniform(2,60,230),mean=24,sd=0.2,leadtime=5,service_level=0.95,Base = 50,
   shortage_cost= 1,inventory_cost=1,ordering_cost=1,ordering_delay=FALSE)

   """
  """  """ 
  warnings.simplefilter('once', UserWarning)
  warnings.warn(' This function is deprecated, Kindly use sim_base_stock_policy() instead or sim_base_stock_policy() for forecasting ')
  L = leadtime

  min_order= round((mean *leadtime)+ ((sd*numpy.sqrt(leadtime))* scipy.stats.norm.ppf(service_level)))
  saftey_stock= ((sd*numpy.sqrt(leadtime))*scipy.stats.norm.ppf(service_level))                        
  
  def base1():
      if(Base==False):
             Base1=round(min_order,0)
      else:
             Base1= Base
      return Base1
  Base= base1()  
  N = len(demand) 
  
  order = numpy.zeros(N+1)
  I = numpy.zeros(N+1)
  IP = numpy.zeros(N+1)
  sales = numpy.zeros(N+1)
  recieved = numpy.zeros(N+1)
  
  IP[0] = I[0] = Base
  order[0]=0
  demand= numpy.append(numpy.array(0),demand)
  for t in range(1,L+1):
    sales[t] = min (demand[t], I[t-1])
    I[t] = I[t-1] - sales[t]
    order[t] = sales[t-ordering_delay]
    IP[t] =  IP[t-1] + order[t] - sales[t]
    
  
  
  for t in range(L+1,N+1):
    sales[t] = min(demand[t], I[t-1] + order[t-L])
    I[t] = I[t-1] + order[t-L] - sales[t]
    order[t] = sales[t-ordering_delay]
    IP[t] = IP[t-1] + order[t] - sales[t]
    recieved[t]= order[t-L]
  
  
  data=pandas.DataFrame({'period':range(1,N+2),'demand':demand,'sales':sales,'inventory_level':I,
                   'inventory_position':IP,'Base':int(Base),'order': order,
                   'recieved':recieved},index=range(1,N+2))
  
  data['lost_order']= data['demand'] - data['sales']
  
  metrics= {'shortage_cost': sum(data['lost_order'])*shortage_cost,
                       'inventory_cost': sum(data['inventory_level'])*inventory_cost,
                       'average_inventory_level': data['inventory_level'].mean(),
                       'ordering_cost':  len(data['order'][data['order']>0]) *ordering_cost,
                       'total_lost_sales': sum(data['lost_order']),
                       'Item_fill_rate': 1-(sum(data['lost_order'][data['lost_order']>0]))/sum(demand[1:(len(demand)-1)]),
                       'cycle_service_level': 1-(len(data['lost_order'][data['lost_order']>0])/(len(demand)-1)),
                       'saftey_stock':saftey_stock}
  a= [data,metrics]
  return a                
  

def sim_base_pois(demand,lambda1, leadtime,service_level,Base=False,
                           shortage_cost= False,inventory_cost=False,ordering_delay=False,
                           ordering_cost=False):
  """[the Function takes a demand vector, mean of demand ,sd,lead time and requested service level to simulate and inventory system, 
      orders are lost if inventory level is less than requested demand, also ordering is made at
      day t+1, metrics like item fill rate and cycle service level are calculated based on a 
     poisson distribution.]

  Args:
      demand ([float]): [A vector of demand in N time periods.]
      lambda1 ([float]): [average demand in N time periods.]
      leadtime ([float]): [lead time from order to arrival]
      service_level ([float]): [cycle service level requested]
      Base (bool, optional): [Set to False for automatic calculation,else manual inumpyut of base.]. Defaults to False.
      ordering_delay (bool, optional): [logical,Default is FALSE,if TRUE, orders are delayed one period.]. Defaults to False.
      shortage_cost (bool, optional): [shortage cost per unit of sales lost]. Defaults to False.
      inventory_cost (bool, optional): [inventory cost per unit.]. Defaults to False.
      ordering_cost (bool, optional): [ordering cost for every time an order is made.]. Defaults to False.

  Returns:
      [list]: [a data frame of the simulation and  dict of the metrics]

  Examples:
   sim_base_pois(demand=numpy.random.uniform(2,60,230),lambda1=24,leadtime=5,service_level=0.95,Base = 50,
   shortage_cost= 1,inventory_cost=1,ordering_cost=1,ordering_delay=FALSE)

  """
  
  L = leadtime

  min_order= scipy.stats.poisson.ppf(service_level,lambda1)*leadtime
  saftey_stock= min_order- (lambda1*leadtime)                
  
  def base1():
      if(Base==False):
             Base1=round(min_order,0)
      else:
             Base1= Base
      return Base1
  Base= base1()  
  N = len(demand) 
  warnings.simplefilter('once', UserWarning)
  warnings.warn(' This function is deprecated, Kindly use sim_base_stock_policy() instead or sim_base_stock_policy() for forecasting ')
  order = numpy.zeros(N+1)
  I = numpy.zeros(N+1)
  IP = numpy.zeros(N+1)
  sales = numpy.zeros(N+1)
  recieved = numpy.zeros(N+1)
  
  IP[0] = I[0] = Base
  order[0]=0
  demand= numpy.append(numpy.array(0),demand)
  for t in range(1,L+1):
    sales[t] = min (demand[t], I[t-1])
    I[t] = I[t-1] - sales[t]
    order[t] = sales[t-ordering_delay]
    IP[t] =  IP[t-1] + order[t] - sales[t]
    
  
  
  for t in range(L+1,N+1):
    sales[t] = min(demand[t], I[t-1] + order[t-L])
    I[t] = I[t-1] + order[t-L] - sales[t]
    order[t] = sales[t-ordering_delay]
    IP[t] = IP[t-1] + order[t] - sales[t]
    recieved[t]= order[t-L]
  
  
  data=pandas.DataFrame({'period':range(1,N+2),'demand':demand,'sales':sales,'inventory_level':I,
                   'inventory_position':IP,'Base':int(Base),'order': order,
                   'recieved':recieved},index= range(1,N+2))
  
  data['lost_order']= data['demand'] - data['sales']
  
  metrics= {'shortage_cost': sum(data['lost_order'])*shortage_cost,
                       'inventory_cost': sum(data['inventory_level'])*inventory_cost,
                       'average_inventory_level': data['inventory_level'].mean(),
                       'ordering_cost':  len(data['order'][data['order']>0]) *ordering_cost,
                       'total_lost_sales': sum(data['lost_order']),
                       'Item_fill_rate': 1-(sum(data['lost_order'][data['lost_order']>0]))/sum(demand[1:(len(demand)-1)]),
                       'cycle_service_level': 1-(len(data['lost_order'][data['lost_order']>0])/(len(demand)-1)),
                       'saftey_stock':saftey_stock}
  a= [data,metrics]
  return a                
  


def sim_min_Q_normal(demand,mean,sd,leadtime,service_level,Quantity,Min=False,
                        shortage_cost= False,inventory_cost=False,
                        ordering_cost=False):
  """[The Function takes a demand vector, mean of demand ,sd,lead time and requested service level to simulate and inventory system, 
      orders are lost if inventory level is less than requested demand, also ordering is made at
      day t+1, metrics like item fill rate and cycle service level are calculated. the min is calculated based on a normal distribution.]

  Args:
      demand ([float]): [A vector of demand in N time periods.]
      mean ([float]): [average demand in N time periods.]
      sd ([float]): [standard deviation in N time periods.]
      leadtime ([float]): [lead time from order to arrival]
      service_level ([float]): [cycle service level requested]
      Quantity ([float]): [Fixed order quantity to be ordered at min]
      Min (int, optional): [if False, calculated based on mean, standard deviation and leadtime]. Defaults to False.
      shortage_cost (bool, optional): [shortage cost per unit of sales lost]. Defaults to False.
      inventory_cost (bool, optional): [inventory cost per unit.]. Defaults to False.
      ordering_cost (bool, optional): [ordering cost for every time an order is made.]. Defaults to False.

  Returns:
     [list]:[a list of two date frames, the simulation and the metrics.]
  Examples:
     [sim_min_Q_normal(round(demand=no.random.uniform(2,40,300)),mean=15,sd=3,leadtime,service_level,Quantity=40,Min=50,
                        shortage_cost= False,inventory_cost=False,
                        ordering_cost=False)]

  """
  """   """


  L = leadtime
  Q =Quantity
  def Min1():
      if(Min==False):
            min_order= round((mean *leadtime)+ ((sd*numpy.sqrt(leadtime))* scipy.stats.norm.ppf(service_level)))
      else:
             min_order= Min
      return min_order
  
  min_order=Min1()
  saftey_stock= ((sd* numpy.sqrt(leadtime))* scipy.stats.norm.ppf(service_level))                        
  warnings.simplefilter('once', UserWarning)
  warnings.warn(' This function is deprecated, Kindly use sim_Q_max() instead or sim_min_Q_dynamic() for forecasting ')
  
  
  N = len(demand) 
  
  order = numpy.zeros(N+1)
  I = numpy.zeros(N+1)
  IP = numpy.zeros(N+1)
  sales = numpy.zeros(N+1)
  recieved = numpy.zeros(N+1)
  
  IP[0] = I[0] = min_order
  order[0]=0
  demand= numpy.append(numpy.array(0),demand)
  for t in range(1,L+1):
    sales[t] = min (demand[t], I[t-1])
    I[t] = I[t-1] - sales[t]
    order[t] = Q * (IP[t-1] <= min_order)
    IP[t] =  IP[t-1] + order[t] - sales[t]
    
  
  
  for t in range(L+1,N+1):
    sales[t] = min(demand[t], I[t-1] + order[t-L])
    I[t] = I[t-1] + order[t-L] - sales[t]
    order[t] = Q * (IP[t-1] <= min_order)
    IP[t] = IP[t-1] + order[t] - sales[t]
    recieved[t]= order[t-L]
  
  
  data=pandas.DataFrame({'period':range(1,N+2),'demand':demand,'sales':sales,'inventory_level':I,
                   'inventory_position':IP,'min':int(min_order),'order': order,
                   'recieved':recieved},index=range(1,N+2))
  
  data['lost_order']= data['demand'] - data['sales']
  
  metrics= {'shortage_cost': sum(data['lost_order'])*shortage_cost,
                       'inventory_cost': sum(data['inventory_level'])*inventory_cost,
                       'average_inventory_level': data['inventory_level'].mean(),
                       'ordering_cost':  len(data['order'][data['order']>0]) *ordering_cost,
                       'total_lost_sales': sum(data['lost_order']),
                       'Item_fill_rate': 1-(sum(data['lost_order'][data['lost_order']>0]))/sum(demand[1:(len(demand)-1)]),
                       'cycle_service_level': 1-(len(data['lost_order'][data['lost_order']>0])/(len(demand)-1)),
                       'saftey_stock':saftey_stock}
  a= [data,metrics]
  return a                
  
def sim_min_Q_pois(demand,lambda1,leadtime,service_level,Quantity,Min=False,
                        shortage_cost= False,inventory_cost=False,
                        ordering_cost=False):
  """[The Function takes a demand vector, mean of demand ,sd,lead time and requested service level to simulate and inventory system, 
      orders are lost if inventory level is less than requested demand, also ordering is made at
      day t+1, metrics like item fill rate and cycle service level are calculated. the min is calculated based on a poisson distribution.]

  Args:
      demand ([float]): [A vector of demand in N time periods.]
      
      lambda1 ([float]): [mean of demand.]
      leadtime ([float]): [lead time from order to arrival]
      service_level ([float]): [cycle service level requested]
      Quantity ([float]): [Fixed order quantity to be ordered at min]
      Min (int, optional): [if False, calculated based on mean, standard deviation and leadtime]. Defaults to False.
      shortage_cost (bool, optional): [shortage cost per unit of sales lost]. Defaults to False.
      inventory_cost (bool, optional): [inventory cost per unit.]. Defaults to False.
      ordering_cost (bool, optional): [ordering cost for every time an order is made.]. Defaults to False.

  Returns:
     [list]:[a list of two date frames, the simulation and the metrics.]
  Examples:
     [sim_min_Q_pois(round(demand=no.random.uniform(2,40,300)),lambda1=15,leadtime,service_level,Quantity=40,Min=50,
                        shortage_cost= False,inventory_cost=False,
                        ordering_cost=False)]

  """


  L = leadtime
  Q =Quantity
  
  
  def Min1():
      if(Min==False):
             min_order= scipy.stats.poisson.ppf(service_level,lambda1)*leadtime
      else:
             min_order= Min
      return min_order
  
  min_order=Min1()
  saftey_stock= min_order- (lambda1*leadtime)                

  warnings.simplefilter('once', UserWarning)
  warnings.warn(' This function is deprecated, Kindly use sim_min_Q() instead or sim_min_Q_dynamic() for forecasting ')
  
  N = len(demand) 
  
  order = numpy.zeros(N+1)
  I = numpy.zeros(N+1)
  IP = numpy.zeros(N+1)
  sales = numpy.zeros(N+1)
  recieved = numpy.zeros(N+1)
  
  IP[0] = I[0] = min_order
  order[0]=0
  demand= numpy.append(numpy.array(0),demand)
  for t in range(1,L+1):
    sales[t] = min (demand[t], I[t-1])
    I[t] = I[t-1] - sales[t]
    order[t] = Q * (IP[t-1] <= min_order)
    IP[t] =  IP[t-1] + order[t] - sales[t]
    
  
  
  for t in range(L+1,N+1):
    sales[t] = min(demand[t], I[t-1] + order[t-L])
    I[t] = I[t-1] + order[t-L] - sales[t]
    order[t] = Q * (IP[t-1] <= min_order)
    IP[t] = IP[t-1] + order[t] - sales[t]
    recieved[t]= order[t-L]
  
  
  data=pandas.DataFrame({'period':range(1,N+2),'demand':demand,'sales':sales,'inventory_level':I,
                   'inventory_position':IP,'min':int(min_order),'order': order,
                   'recieved':recieved},index=range(1,N+2))
  
  data['lost_order']= data['demand'] - data['sales']
  
  metrics= {'shortage_cost': sum(data['lost_order'])*shortage_cost,
                       'inventory_cost': sum(data['inventory_level'])*inventory_cost,
                       'average_inventory_level': data['inventory_level'].mean(),
                       'ordering_cost':  len(data['order'][data['order']>0]) *ordering_cost,
                       'total_lost_sales': sum(data['lost_order']),
                       'Item_fill_rate': 1-(sum(data['lost_order'][data['lost_order']>0]))/sum(demand[1:(len(demand)-1)]),
                       'cycle_service_level': 1-(len(data['lost_order'][data['lost_order']>0])/(len(demand)-1)),
                       'saftey_stock':saftey_stock}
  a= [data,metrics]
  return a                
  


def sim_min_max_normal (demand,mean,sd,leadtime,service_level,Max,Min=False,
                        shortage_cost= False,inventory_cost=False,
                        ordering_cost=False):
  """[The Function takes a demand vector, mean of demand ,sd,lead time and requested service level to simulate and inventory system, 
      orders are lost if inventory level is less than requested demand, also ordering is made at
      day t+1, metrics like item fill rate and cycle service level are calculated. the min is calculated based on a normal distribution.]

   Args:
      demand ([float]): [demand in N time periods]
      mean ([float]): [average demand in N time periods.]
      sd ([float]): [standard deviation in N time periods.]
      leadtime ([float]): [lead time from order to arrival]
      service_level ([float]): [cycle service level requested]
      Max ([float]): [Max quantity for order up to level]
      Min (bool, optional): [Min is calculated auttomatically if set to False]. Defaults to False.
      shortage_cost (bool, optional): [shortage cost per unit of sales lost]. Defaults to False.
      inventory_cost (bool, optional): [inventory cost per unit.]. Defaults to False.
      ordering_cost (bool, optional): [ordering cost for every time an order is made.]. Defaults to False.
   Returns:
      [list]: [a list of two, the simulation and the metrics.]

   Examples:
      [sim_min_max_normal(demand=numpy.random.uniform(2,20,200),mean=10,sd=0.2,leadtime=5,service_level=0.95,Max=90,
       shortage_cost= False,inventory_cost=False,ordering_cost=False,Min=50)]

  """                          

  L = leadtime

  def Min1():
      if(Min==False):
            min_order= round((mean *leadtime)+ ((sd*numpy.sqrt(leadtime))* scipy.stats.norm.ppf(service_level)))
      else:
             min_order= Min
      return min_order
  
  min_order=Min1()
  saftey_stock= ((sd* numpy.sqrt(leadtime))* scipy.stats.norm.ppf(service_level))                        

  
  
  N = len(demand) 
  
  order = numpy.zeros(N+1)
  I = numpy.zeros(N+1)
  IP = numpy.zeros(N+1)
  sales = numpy.zeros(N+1)
  recieved = numpy.zeros(N+1)
  
  IP[0] = I[0] = min_order
  order[0]=0
  demand= numpy.append(numpy.array(0),demand)
  for t in range(1,L+1):
    sales[t] = min (demand[t], I[t-1])
    I[t] = I[t-1] - sales[t]
    order[t] = (Max- IP[t-1]) * (IP[t-1] <= min_order)
    IP[t] =  IP[t-1] + order[t] - sales[t]
    
  
  
  for t in range(L+1,N+1):
    sales[t] = min(demand[t], I[t-1] + order[t-L])
    I[t] = I[t-1] + order[t-L] - sales[t]
    order[t] = (Max- IP[t-1]) * (IP[t-1] <= min_order)
    IP[t] = IP[t-1] + order[t] - sales[t]
    recieved[t]= order[t-L]
  
  
  data=pandas.DataFrame({'period':range(1,N+2),'demand':demand,'sales':sales,'inventory_level':I,
                   'inventory_position':IP,'min':int(min_order),'order': order,'max':int(Max),
                   'recieved':recieved},index= range(1,N+2))
  
  data['lost_order']= data['demand'] - data['sales']
  
  metrics= {'shortage_cost': sum(data['lost_order'])*shortage_cost,
                       'inventory_cost': sum(data['inventory_level'])*inventory_cost,
                       'average_inventory_level': data['inventory_level'].mean(),
                       'ordering_cost':  len(data['order'][data['order']>0]) *ordering_cost,
                       'total_lost_sales': sum(data['lost_order']),
                       'Item_fill_rate': 1-(sum(data['lost_order'][data['lost_order']>0]))/sum(demand[1:(len(demand)-1)]),
                       'cycle_service_level': 1-(len(data['lost_order'][data['lost_order']>0])/(len(demand)-1)),
                       'saftey_stock':saftey_stock}
  
  warnings.simplefilter('once', UserWarning)
  warnings.warn(' This function is deprecated, Kindly use sim_min_max() instead or sim_min_max_dynamic() for forecasting ')
  
  a= [data,metrics]
  return a                
  

def sim_min_max_pois (demand,lambda1,leadtime,service_level,Max,Min=False,
                        shortage_cost= False,inventory_cost=False,
                        ordering_cost=False):
  """[The Function takes a demand vector, mean of demand ,sd,lead time and requested service level to simulate and inventory system, 
      orders are lost if inventory level is less than requested demand, also ordering is made at
      day t+1, metrics like item fill rate and cycle service level are calculated. the min is calculated based on a poisson distribution.]

  Args:
      demand ([float]): [demand in N time period]
      lambda1 ([float]) : [mean of the demand in N time periods]
      leadtime ([float]): [lead time from order to arrival]
      service_level ([float]): [cycle service level requested]
      Max ([float]): [Max quantity for order up to level]
      Min (bool, optional): [Min is calculated auttomatically if set to False]. Defaults to False.
      shortage_cost (bool, optional): [shortage cost per unit of sales lost]. Defaults to False.
      inventory_cost (bool, optional): [inventory cost per unit.]. Defaults to False.
      ordering_cost (bool, optional): [ordering cost for every time an order is made.]. Defaults to False.
  Returns:
      [list]: [a list of two, the simulation and the metrics.]

  Examples:
      [sim_min_max_pois(demand=numpy.random.uniform(2,20,200),mean=10,sd=0.2,leadtime=5,service_level=0.95,Max=90,
       shortage_cost= False,inventory_cost=False,ordering_cost=False,Min=50)]

      """       


  L = leadtime

             
  
  def Min1():
      if(Min==False):
             min_order= scipy.stats.poisson.ppf(service_level,lambda1)*leadtime
      else:
             min_order= Min
      return min_order
  
  min_order=Min1()                       
  saftey_stock= min_order- (lambda1*leadtime)    
  
  
  N = len(demand) 
  
  order = numpy.zeros(N+1)
  I = numpy.zeros(N+1)
  IP = numpy.zeros(N+1)
  sales = numpy.zeros(N+1)
  recieved = numpy.zeros(N+1)
  
  IP[0] = I[0] = min_order
  order[0]=0
  demand= numpy.append(numpy.array(0),demand)
  for t in range(1,L+1):
    sales[t] = min (demand[t], I[t-1])
    I[t] = I[t-1] - sales[t]
    order[t] = (Max- IP[t-1]) * (IP[t-1] <= min_order)
    IP[t] =  IP[t-1] + order[t] - sales[t]
    
  
  
  for t in range(L+1,N+1):
    sales[t] = min(demand[t], I[t-1] + order[t-L])
    I[t] = I[t-1] + order[t-L] - sales[t]
    order[t] = (Max- IP[t-1]) * (IP[t-1] <= min_order)
    IP[t] = IP[t-1] + order[t] - sales[t]
    recieved[t]= order[t-L]
  
  
  data=pandas.DataFrame({'period':range(1,N+2),'demand':demand,'sales':sales,'inventory_level':I,
                   'inventory_position':IP,'min':int(min_order),'order': order,'max':int(Max),
                   'recieved':recieved},index= range(1,N+2))
  
  data['lost_order']= data['demand'] - data['sales']
  
  metrics= {'shortage_cost': sum(data['lost_order'])*shortage_cost,
                       'inventory_cost': sum(data['inventory_level'])*inventory_cost,
                       'average_inventory_level': data['inventory_level'].mean(),
                       'ordering_cost':  len(data['order'][data['order']>0]) *ordering_cost,
                       'total_lost_sales': sum(data['lost_order']),
                       'Item_fill_rate': 1-(sum(data['lost_order'][data['lost_order']>0]))/sum(demand[1:(len(demand)-1)]),
                       'cycle_service_level': 1-(len(data['lost_order'][data['lost_order']>0])/(len(demand)-1)),
                       'saftey_stock':saftey_stock}
  warnings.simplefilter('once', UserWarning)
  warnings.warn(' This function is deprecated, Kindly use sim_min_max() instead or sim_min_max_dynamic() for forecasting ')
  a= [data,metrics]
  return a                
  


def total_logistics_cost(quantity,expected_annual_demand,sd_annual_demand,expected_leadtimeindays,sd_leadtime,costperunit,transportcost,
                               holdingrate,ordering_cost,csl):
  """[calculating total logistics cost based on a normal distribution.]

  Args:
      quantity ([float]): [quantity ordered every cycle.]
      expected_annual_demand ([float]): [numeric,  expected annual demand of the SKU.]
      sd_annual_demand ([float]): [annual standard deviation of the SKU.]
      expected_leadtimeindays ([float]): [expected lead time in days.]
      sd_leadtime ([float]): [expected standard deviation of lead time in days.]
      costperunit ([float]): [purchase cost of the SKU]
      transportcost ([float]): [transport cost of the SKU]
      holdingrate ([float]): [holding rate of the SKU]
      ordering_cost ([float]): [ordering cost per order placed]
      csl ([float]): [cycle service level desired]
  Returns:
  [dict]:[ dict  that contains calculations of the total logistics cost in detail.]
  Examples:
    [total.logistics.cost(quantity=32,expected_annual_demand=1550,
      sd_annual_demand=110,expected_leadtimeindays=64,sd_leadtime=8,
      costperunit=107,transportcost=22,holdingrate=0.15,ordering_cost=500,csl=0.95)]
"""

  """"""
  quantity
  purchase_cost= expected_annual_demand*costperunit
  transport_cost= expected_annual_demand*transportcost
  landed_cost= purchase_cost+transport_cost
  ordering_cost= (expected_annual_demand/quantity)*ordering_cost
  holding_cost= (costperunit+transportcost)*holdingrate
  cyclestock_cost= holding_cost*(quantity/2)
  dl=expected_annual_demand*expected_leadtimeindays/365
  sigmadl=numpy.sqrt( (expected_leadtimeindays*(sd_annual_demand*numpy.sqrt(1/365))**2)+(((expected_annual_demand/365)**2*(sd_leadtime)**2)))

  saftey_stock= scipy.stats.norm.ppf(csl)*sigmadl
  saftey_stock_cost= saftey_stock*holding_cost
  total_cost= purchase_cost+transport_cost+ordering_cost+cyclestock_cost+saftey_stock_cost
  lcostperitem=(total_cost/expected_annual_demand)
  return{'quantity':quantity,
                    'leadtime':expected_leadtimeindays,
                    'purchase_cost':purchase_cost,
                    'transport_cost':transport_cost,
                    'landed_cost':landed_cost,
                    'ordering_cost':ordering_cost,
                    'cyclestock_cost':cyclestock_cost,
                    'dl':dl,
                    'sigmadl':sigmadl,
                    'saftey_stock':saftey_stock,
                    'saftey_stock_cost':saftey_stock_cost,
                    'total_cost':total_cost,
                    'costperunit':lcostperitem}

def TQpractical(annualdemand,orderingcost,purchasecost,holdingrate):
  """[Identyfing Practical ordering quantity based on the economic order quantity.it is assumed that practical
       order quantity will be always withing 6 % of the economic order quantity in terms od total relevant cost.]

  Args:
      annualdemand ([float]): [numeric annual demand of the SKU.]
      orderingcost ([float]): [numeric  ordering cost of the SKU.]
      purchasecost ([float]): [numeric purchase cost of the SKU.]
      holdingrate ([float]): [numeric holding rate of the SKU.]

  Returns:
  [dict]: [ dict that contains the economic order quantity and the practical order quantity, Tstar (optimum)and Tpractical
    which is always away from the optimum up to 6%. ]
  Examples:
  [TQpractical(annualdemand=1000,orderingcost=100,purchasecost=72,holdingrate=0.25)]
    
  """
  Tsyears= numpy.sqrt((2*orderingcost)/(annualdemand*holdingrate*purchasecost))
  Tstarweeks= numpy.sqrt((2*orderingcost)/(annualdemand*holdingrate*purchasecost))*52
  Qstar=Tsyears*annualdemand
  Tpractical= 2**round(numpy.log(Tstarweeks/numpy.sqrt(2))/numpy.log(2))
  Qpractical= Tpractical/52*annualdemand
  Tpracticalweeks=Tpractical

  return({'Ts':Tsyears,'Tstarweeks':Tstarweeks,'Qstar':Qstar,
                    'Tpractical':Tpractical,'Tpracticalweeks':Tpracticalweeks,'Qpractical':Qpractical})




def sim_min_Q(demand, leadtime, service_level,Quantity,distribution= 'normal',mean = False, sd=False,
                       shortage_cost = False, inventory_cost = False, 
                       ordering_cost = False,initial_inventory_level = False,
                       Min= False,recalculate=False,recalculate_windows=False,plot=False):
  """[Simulating a Min,Q policy or also called S,Q policy,  .
     The Function takes a demand vector, mean of demand ,sd,lead time and requested service level to simulate an inventory system, 
     orders are lost if inventory level is less than requested demand, also ordering is made at
     day t+1, metrics like item fill rate and cycle service level are calculated. 
     the min is calculated based on a normal distribution or a poisson distribution, also min can be set manually.
     Q (fixed quantity) is ordered whenever inventory position reaches min]

   Args:
      demand ([float]): [demand in N time periods]
      leadtime ([float]): [lead time from order to arrival]
      service_level ([float]): [cycle service level requested]
      Quantity ([float]): Fixed order quantity to be ordered at min.
      distribution ([str]) :distribution  to calculate safety stock based on demand distribution, current choices are 'normal' or 'poisson'
      mean ([float]): [average demand in N time periods.]
      sd ([float]): [standard deviation in N time periods.]
      shortage_cost (bool, optional): [shortage cost per unit of sales lost]. Defaults to False.
      inventory_cost (bool, optional): [inventory cost per unit.]. Defaults to False.
      ordering_cost (bool, optional): [ordering cost for every time an order is made.]. Defaults to False.
      initial_inventory_level ([float]): Default is False and simulation starts with min as inventory level
      min  ([float]):Default is False and min is calculated based on mean,demand and lead time unless set manually
      recalculate  ([float]): the mean and sd is recalculated every X periods from first period to x,default is FALSE .
      recalculate_windows  ([float]): the min  mean and sd windows to recalculate , for exammple if it is set to 4 mean and sd
                           is calculated from t to t-4,,default is FALSE .
      plot  (bool, optional): Default is False, if true a plot is generated
   Returns:
      [list]: [a list of two, the simulation and the metrics.]

   Examples:
      [sim_min_Q(demand=numpy.random.uniform(2,20,200).round(),Quantity=100,
          leadtime=5,service_level=0.95,plot=True)]

  """    
  L = leadtime
  N = len(demand) 
  Q=Quantity
  if( type(recalculate) != bool):
      mean = numpy.zeros(N+1)
      sd= numpy.zeros(N+1)
      minn= numpy.zeros(N+1)
      Min= numpy.zeros(N+1)
      for i in range(len(mean)):
          mean[i]= numpy.mean(demand[0:i])if (numpy.isnan(numpy.mean(demand[0:i]))==False) else demand[0]
          sd[i]= numpy.std(demand[0:i])if (numpy.isnan(numpy.std(demand[0:i]))==False) else 0
          if(distribution== 'normal'):
              minn[i]= round((mean[i] *leadtime)+ ((sd[i]*numpy.sqrt(leadtime))* scipy.stats.norm.ppf(service_level)))
          else :
              minn[i]= scipy.stats.poisson.ppf(service_level,mean[i]*leadtime)
         
      if(type(recalculate_windows) != bool):
          mean[0]= demand[0]
          sd[0]= numpy.std(demand)
          for i in range(1,len(mean)):
              mean[i]= (numpy.mean(demand[max((i- recalculate_windows),0):(i-1)])if 
                        (len(demand[max((i- recalculate_windows),0):(i-1)])>0) else demand[0]) 
              sd[i]= (numpy.std(demand[max((i- recalculate_windows),0):(i-1)])if 
                        (len(demand[max((i- recalculate_windows),0):(i-1)])>0) else sd[0]) 
              if(distribution== 'normal'):
                  minn[i]= round((mean[i] *leadtime)+ ((sd[i]*numpy.sqrt(leadtime))* scipy.stats.norm.ppf(service_level)))
              else :
                  minn[i]= scipy.stats.poisson.ppf(service_level,mean[i]*leadtime)  
      Min[0]= minn[1]  
      for i in range(1,len(Min)):
          Min[i]= Min[i-1] if((i % recalculate) != 0) else minn[i]
  
  def classfication(demand):
      def intervals(x):
          y=numpy.zeros(len(x)+2)
          k=0
          counter=0
          for tmp in range(len(x)):
              if (x[tmp]==0):
                  counter= counter +1
              else :
                  k=k+1
                  y[k]= counter
                  counter =1
          y= y[y>0]
          y[numpy.isnan(y)]=1
          return y
      def demand1(x):
          y= x[x!=0]
          return y
      D = demand1(demand)
      ADI = numpy.mean(intervals(demand))
      CV2 = (numpy.std(D)/numpy.mean(D))**2
      
      if (ADI > 4/3):
          if (CV2 >0.5):
              type1= 'Lumpy'
          else :
              type1= 'Intermittent'
      else  :
          if(CV2 >0.5):
              type1= 'Erratic'
          else:
              type1= 'Smooth'
               
      return type1
  class1= classfication(demand)
   
  if((type(mean)== bool) & (type(recalculate)==bool)):
    mean= numpy.mean(demand)
  elif ((type(mean)!= bool) & (type(recalculate)==bool)):
    mean=mean
  
  
  if((type(sd)== bool) & (type(recalculate)==bool)):
    sd= numpy.std(demand)
  elif ((type(sd)!= bool) & (type(recalculate)== bool)):
    sd =sd
  
  
  if ((type(Min) != bool) & (type(recalculate) == bool)):
    
    Min= Min
    Min =  numpy.repeat(Min,N+1)
    
  elif((distribution== 'normal')& (type(recalculate)== bool)):
    
    Min = round((mean *leadtime)+ ((sd*numpy.sqrt(leadtime))* scipy.stats.norm.ppf(service_level)))
    Min =  numpy.repeat(Min,N+1)
    
  elif ((distribution== 'poisson') & (type(recalculate)== bool)):
    
    Min = scipy.stats.poisson.ppf(service_level,mean[i]*leadtime)
    Min =  numpy.repeat(Min,N+1)
    
  saftey_stock= Min- (mean *leadtime)            

  order = numpy.zeros(N+1)
  I = numpy.zeros(N+1)
  IP = numpy.zeros(N+1)
  sales = numpy.zeros(N+1)
  recieved = numpy.zeros(N+1)
  order[0]=0
  demand= numpy.append(numpy.array(0),demand)

  if(initial_inventory_level==False):
    IP[0] = I[0] =  Min[0]
  else :
    IP[0] = I[0] =  initial_inventory_level


  
  
  for t in range(1,L+1):
    sales[t] = min (demand[t], I[t-1])
    I[t] = I[t-1] - sales[t]
    order[t] = Q * (IP[t-1] <= Min[t])
    IP[t] =  IP[t-1] + order[t] - sales[t]
    
  
  
  for t in range(L+1,N+1):
    sales[t] = min(demand[t], I[t-1] + order[t-L])
    I[t] = I[t-1] + order[t-L] - sales[t]
    order[t] = Q * (IP[t-1] <= Min[t])
    IP[t] = IP[t-1] + order[t] - sales[t]
    recieved[t]= order[t-L]
  
 

  data=pandas.DataFrame({'period':range(1,N+2),'demand':demand,'sales':sales,'inventory_level':I,
                   'inventory_position':IP,'saftey_stock': saftey_stock,'min':Min,'order': order,'Q':Quantity,
                   'recieved':recieved},index= range(1,N+2))
  
  data['lost_order']= data['demand'] - data['sales']
  
  metrics= pandas.DataFrame({'shortage_cost': sum(data['lost_order'])*shortage_cost,
                       'inventory_cost': sum(data['inventory_level'])*inventory_cost,
                       'average_inventory_level': data['inventory_level'].mean(),'total_orders':len(order[order>0]),
                       'total_lost_sales': sum(data['lost_order']),
                       'ordering_cost':  len(data['order'][data['order']>0]) *ordering_cost,'average_ordering_quantity':(order[order>0]).mean(),
                       'ordering_interval': str(round(len(demand)/len(order[order>0]),2))+'_periods',
                       'Item_fill_rate': 1-(sum(data['lost_order'][data['lost_order']>0]))/sum(demand[1:(len(demand)-1)]),
                       'cycle_service_level': 1-(len(data['lost_order'][data['lost_order']>0])/(len(demand)-1)),
                       'saftey_stock':saftey_stock.mean(),'average_sales': sales.mean() },index= [0])
  metrics['average_flow_time(throughput)']= metrics['average_inventory_level']/metrics['average_sales']
  metrics['class']= class1
  
  if(plot== True):
      large_rockwell_template = dict(
       layout=plotly.graph_objects.Layout(title_font=dict(family="Rockwell", size=24))
                                      )
      fig= plotly.graph_objects.Figure()
        
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['inventory_level'],
                                                 mode='markers',marker=dict(color='green'),
                                                 name= 'inventory level'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['order'],
                    line= dict(color= 'grey'),
                    name='order'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['demand'],
                    line= dict(color= 'royalblue'),
                    name='demand'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['sales'],
                    line= dict(color= 'orange'),
                    name='sales'))
      fig.update_layout(title= 'Min Q Policy',
                   xaxis_title='Period',
                   yaxis_title='Demand' ,template=large_rockwell_template)


      fig.show()
      
  
  
  a= [data,metrics]
  return a 



def R_s_S_dynamic(demand,forecast, leadtime, Review_period,service_level,initial_inventory_level=False, Min_to_max=0.6,Min=False,
                               one_step_forecast=True,shortage_cost = False, 
                inventory_cost = False, ordering_cost = False,
                distribution= 'normal', error_metric= 'rmse',metric_windows= False,plot=False):
  """[Simulating a Min Max periodic policy or also called R,s,S policy, R represents the ordering/review period, 
      the Max is dynamically calculated based on a forecast vector. .
  
     The Function takes a demand vector, mean of demand ,a forecast vector and requested service level to simulate an inventory system, 
     orders are lost if inventory level is less than requested demand, also ordering is made at
     day t+1, metrics like item fill rate and cycle service level are calculated. 
     the min is calculated based on a normal distribution or a poisson distribution, also min can be set manually.
     Max - inventory position is ordered whenever inventory position reaches min at the priod of review  ]

   Args:
      demand ([float]): [demand in N time periods]
      forecast ([float]): [the forecast vector of equal n periods to demand.]
      leadtime ([float]): [lead time from order to arrival]
      Review_period ([float]):[the number of periods where every order is allowed to be made.]
      service_level ([float]): [cycle service level requested]
      initial_inventory_level ([float]): [Default is False and simulation starts with min as inventory level]
      Min_to_max ([float]): [the ratio of min to max calculation , default 0.6 but can be changed manually.]
      Min  ([float]):[Default is False and min is calculated based on mean,demand and lead time unless set manually]
      one_step_forecast ([logical]): [Default is true where demand lead time is calcluated as(forecast at period t * leadtime)]
      shortage_cost (bool, optional): [shortage cost per unit of sales lost]. Defaults to False.]
      inventory_cost (bool, optional): [inventory cost per unit.]. Defaults to False.]
      ordering_cost (bool, optional): [ordering cost for every time an order is made. Defaults to False.]
      distribution ([str]) :[distribution  to calculate safety stock based on demand distribution, current choices are 
                             'normal' or 'poisson']
      error_metric ([str]):[metric is currently 'rmse' and 'mae', this calculates the error
                            from period 1 to period t unless metric_windows is set.]
      metric_windows  ([float]): [for exammple if it is set to 4 rmse for t is calculated from t-1 to t-4,default is FALSE]
      plot  (bool, optional): [Default is False, if true a plot is generated]
   Returns:
      [list]: [a list of two, the simulation and the metrics.]

   Examples:
      [R_s_S_dynamic(demand=numpy.random.uniform(2,20,200).round(),
                     forecast=numpy.random.uniform(2,20,200).round(), leadtime=8, Review_period=10, service_level=0.95)]

  """    

  
###########################################################
  
  L = leadtime
  N = len(demand) 
  
  demand=numpy.append(numpy.array(0),demand)
  forecast= numpy.append(numpy.array(0),forecast)

  if (one_step_forecast== True):
       dl=forecast*leadtime
  else :
       dl= numpy.zeros(len(demand))
    
       for i in range(len(demand)):
           dl[i]= sum(forecast[i : min((i+leadtime-1),len(dl))])
  
  metric= numpy.zeros(len(demand))

  if(error_metric == 'rmse'):
      if (type(metric_windows)== bool):
          for i in range(1,len(demand)):
              metric[i]= numpy.sqrt(numpy.mean((demand[1:i-1]- forecast[1:i-1])**2))
  
      else :
          for i in range(1,len(demand)):
              metric[i]= numpy.sqrt(numpy.mean((demand[max((i- metric_windows),0):(i-1)]- forecast[max((i- metric_windows),0):(i-1)])**2))

  if(error_metric == 'mae'):
      if (type(metric_windows)== bool):
          for i in range(1,len(demand)):
              metric[i]= numpy.mean(abs((demand[1:i-1]- forecast[1:i-1])**2))
  
      else :
          for i in range(1,len(demand)):
              metric[i]= numpy.mean(abs((demand[max((i- metric_windows),0):(i-1)]- forecast[max((i- metric_windows),0):(i-1)])**2))

  metric[numpy.isnan(metric)]= numpy.round(metric[numpy.isnan(metric)==False].mean())



  def classfication(demand):
      def intervals(x):
          y=numpy.zeros(len(x)+2)
          k=0
          counter=0
          for tmp in range(len(x)):
              if (x[tmp]==0):
                  counter= counter +1
              else :
                  k=k+1
                  y[k]= counter
                  counter =1
          y= y[y>0]
          y[numpy.isnan(y)]=1
          return y
      def demand1(x):
          y= x[x!=0]
          return y
      D = demand1(demand)
      ADI = numpy.mean(intervals(demand))
      CV2 = (numpy.std(D)/numpy.mean(D))**2
      
      if (ADI > 4/3):
          if (CV2 >0.5):
              type1= 'Lumpy'
          else :
              type1= 'Intermittent'
      else  :
          if(CV2 >0.5):
              type1= 'Erratic'
          else:
              type1= 'Smooth'
               
      return type1
  class1= classfication(demand)
   
  sigmadl= metric* numpy.sqrt(leadtime)
  
  if(distribution== 'normal'):
      saftey_stock= sigmadl *  scipy.stats.norm.ppf(service_level)
  elif(distribution== 'poisson'):
      saftey_stock=  scipy.stats.poisson.ppf(service_level, demand*leadtime) - (demand*leadtime)

  Max= numpy.round(dl+saftey_stock)

  if(type(Min) ==bool):
      Min= numpy.round(Min_to_max *Max)
    
  else :
      Min= numpy.repeat(Min,N+1)
    
  
  Min[numpy.isnan(Min)]= numpy.round(Min[numpy.isnan(Min)==False].mean())
  Max[numpy.isnan(Max)]= numpy.round(Max[numpy.isnan(Max)==False].mean())
  Max[0]= Max.mean().round()

  
  
  
  
  order = numpy.zeros(N+1)
  I = numpy.zeros(N+1)
  IP = numpy.zeros(N+1)
  sales = numpy.zeros(N+1)
  recieved = numpy.zeros(N+1)
  order[0]=0




  
  if(type(initial_inventory_level)==bool):
      IP[0] = I[0] =  Max[0]
  else :
      IP[0] = I[0] =  initial_inventory_level
    
  
  def numpy_rep(x, reps=1, each=False, length=0):
    """ implementation of functionality of rep() and rep_len() from R

    Attributes:
        x: numpy array, which will be flattened
        reps: int, number of times x should be repeated
        each: logical; should each element be repeated reps times before the next
        length: int, length desired; if >0, overrides reps argument
    """
    if length > 0:
        reps = numpy.int(numpy.ceil(length / x.size))
    x = numpy.repeat(x, reps)
    if(not each):
        x = x.reshape(-1, reps).T.ravel() 
    if length > 0:
        x = x[0:length]
    return(x)
  ordering_time= numpy_rep(numpy.repeat([0,1], [Review_period-1,1]),each=False,reps=len(demand))
  ordering_time=numpy.append(numpy.array(0), ordering_time)
  
  def hibrid_fun(t):
      
      if((IP[t-1] <= Min[t])):
                 a= max((Max[t] - IP[t-1]),0) * (IP[t-1] <= Min[t])
      if not(IP[t-1] <= Min[t]) :
                  a=max((Max[t] - IP[t-1]),0) * (ordering_time[t])           
      return a
  for t in range(1,L+1):
    sales[t] = min (demand[t], I[t-1])
    I[t] = I[t-1] - sales[t]
    order[t] = max((Max[t] - IP[t-1]),0) * (IP[t-1] <= Min[t])*ordering_time[t]
    IP[t] =  IP[t-1] + order[t] - sales[t]
    
  
  
  for t in range(L+1,N+1):
    sales[t] = min(demand[t], I[t-1] + order[t-L])
    I[t] = I[t-1] + order[t-L] - sales[t]
    order[t] = max((Max[t] - IP[t-1]),0) * (IP[t-1] <= Min[t])*ordering_time[t]
    IP[t] = IP[t-1] + order[t] - sales[t]
    recieved[t]= order[t-L]
  
  
  data=pandas.DataFrame({'period':range(1,N+2),'demand':demand,'forecast':forecast,'sales':sales,'inventory_level':I,
                   'inventory_position':IP,'saftey_stock': saftey_stock,'min':Min,'order': order,'max':Max,
                   'recieved':recieved},index= range(1,N+2))
  
  data['lost_order']= data['demand'] - data['sales']
  error_mape=abs(demand-forecast)/abs(demand)
  error_mape= error_mape[numpy.isnan(error_mape)==False]
  metrics= pandas.DataFrame({'shortage_cost': sum(data['lost_order'])*shortage_cost,
                       'inventory_cost': sum(data['inventory_level'])*inventory_cost,
                       'average_inventory_level': data['inventory_level'].mean(),'total_orders':len(order[order>0]),
                       'total_lost_sales': sum(data['lost_order']),
                       'ordering_cost':  len(data['order'][data['order']>0]) *ordering_cost,'average_ordering_quantity':(order[order>0]).mean(),
                       'ordering_interval': str(round(len(demand)/len(order[order>0]),2))+'_periods',
                       'Item_fill_rate': 1-(sum(data['lost_order'][data['lost_order']>0]))/sum(demand[1:(len(demand)-1)]),
                       'cycle_service_level': 1-(len(data['lost_order'][data['lost_order']>0])/(len(demand)-1)),
                       'saftey_stock':saftey_stock.mean(),'average_sales': sales.mean() },index= [0])
  metrics['average_flow_time(throughput)']= metrics['average_inventory_level']/metrics['average_sales']
  metrics['class']= class1
  metrics['rmse']= numpy.sqrt(numpy.mean((demand-forecast)**2))
  metrics['mae']= numpy.mean(abs(demand-forecast))
  metrics['me']= numpy.mean(demand-forecast)
  metrics['mape']= numpy.mean(error_mape *100)


  
  if(plot== True):
      large_rockwell_template = dict(
       layout=plotly.graph_objects.Layout(title_font=dict(family="Rockwell", size=24))
                                      )
      fig= plotly.graph_objects.Figure()
        
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['inventory_level'],
                                                 mode='markers',marker=dict(color='green'),
                                                 name= 'inventory level'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['order'],
                    line= dict(color= 'grey'),
                    name='order'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['demand'],
                    line= dict(color= 'royalblue'),
                    name='demand'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['forecast'],
                    line= dict(color= 'green'),
                    name='forecast'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['sales'],
                    line= dict(color= 'orange'),
                    name='sales'))
      fig.update_layout(title= 'R-s-S Dynamic',
                   xaxis_title='Period',
                   yaxis_title='Demand' ,template=large_rockwell_template)


      fig.show()
      
  
  
  a= [data,metrics]
  return a 




def abc_dynamic(product,first_attribute,key_to_split=False,second_attribute=False,A= False,B=False):
    """[abc_dynamic

      Identyfing ABC category based on the pareto rule.
      the function can have flexibility in defining the A,B thresholds. can be done on multiple splits for example
      countries or stores]
   Args:
      product([array]): [Vector that contains the product name.]
      key_to_split ([array]): [logical and by default is False, otherwise a column that has a splitting dimension,
                               for example ; stores or cities]
      first_attribute ([float]): [attribute to do the ABC analysis on, for example sales quantity]
      second_attribute ([optional]):[attribute to do the ABC analysis on .for example profit, the default is False]
      A ([optional]):[changing the default threshold for A category which is 0.8, the default is FALSE]
      B ([optional]):[changing the default threshold for B category which is 0.95, the default is FALSE]

      
   Returns:
      [DataFrame]: [dataframe that contains ABC categories.]

   Examples:
      [abc_dynamic(product= numpy.array(range(1,1001)),first_attribute =  numpy.random.uniform(1,10000,1000),
      second_attribute=False,key_to_split =  False,A= 0.5,B=False)]

  """    
    A=  0.8 if (A== False) else A
    B= 0.95 if (B== False) else B
    
   
    def category(x):
                        if (x < A):
                          return('A')
                        elif (x< B):
                          return('B')
                        else:
                          return('C')
    def unique(data_list):
            unique_list= []
            for x in data_list:
                
                if x not in unique_list:
                    
                    unique_list.append(x)
            return unique_list
    def productmix(data,second_attribute):
    


        data['perc_first_attribute']= data['first_attribute']/sum(data['first_attribute'])
        data=data.sort_values(by='first_attribute',ascending= False)
        data['comu_first_attribute']=data['perc_first_attribute'].cumsum()
        data['category_first']= data.comu_first_attribute.map(category)
        if(type(second_attribute) != bool):
            data=data.sort_values(by='second_attribute',ascending= False)
            data['perc_second_attribute']= data['second_attribute']/sum(data['second_attribute'])
            data['comu_second_attribute']=data['perc_second_attribute'].cumsum()
            data['category_second']= data.comu_second_attribute.map(category)
            data['category_mix']= data['category_first'] + '_'+data['category_second']
       
        return data
  
    if((type(key_to_split) == bool) & (type(second_attribute) ==bool)):
        data= pandas.DataFrame({'product':product,'first_attribute':first_attribute})   
        data['perc']= data['first_attribute']/sum(data['first_attribute'])
        data=data.sort_values(by='first_attribute',ascending= False)
        data['comu']=data['perc'].cumsum()
        data['category']= data.comu.map(category)
        a= data
        return a
    elif ((type(key_to_split) == bool) & (type(second_attribute) !=bool)):
        data= pandas.DataFrame({'product':product,'first_attribute':first_attribute,'second_attribute':second_attribute})   

        data['perc_first_attribute']= data['first_attribute']/sum(data['first_attribute'])
        data=data.sort_values(by='first_attribute',ascending= False)
        data['comu_first_attribute']=data['perc_first_attribute'].cumsum()
        data['category_first']= data.comu_first_attribute.map(category)
        data=data.sort_values(by='second_attribute',ascending= False)
        data['perc_second_attribute']= data['second_attribute']/sum(data['second_attribute'])
        data['comu_second_attribute']=data['perc_second_attribute'].cumsum()
        data['category_second']= data.comu_second_attribute.map(category)
        data['category_mix']= data['category_first'] + '_'+data['category_second']
        a=data
        return a
    elif  ((type(key_to_split) !=bool) & (type(second_attribute) ==bool)):
         data= pandas.DataFrame({'product':product,'key_to_split':key_to_split,'first_attribute':first_attribute})   

         keys= unique(key_to_split)
         df= pandas.DataFrame({})
         for i in keys:
             store= data[data['key_to_split']== i]
             store1= productmix(store,second_attribute)
             df=pandas.concat([df,store1],axis=0)
             a=df
         return a
    else:
         data= pandas.DataFrame({'product':product,'key_to_split':key_to_split,'first_attribute':first_attribute,
                                 'second_attribute':second_attribute})   

         keys= unique(key_to_split)
         df= pandas.DataFrame({})
         for i in keys:
             store= data[data['key_to_split']== i]
             store1= productmix(store,second_attribute)
             df=pandas.concat([df,store1],axis=0)
             a=df
         return a
    return a
    

def hybrid_poicy_dynamic(demand,forecast, leadtime, Review_period,service_level,initial_inventory_level=False, Min_to_max=0.6,Min=False,
                               one_step_forecast=True,shortage_cost = False, 
                inventory_cost = False, ordering_cost = False,
                distribution= 'normal', error_metric= 'rmse',metric_windows= False,plot=False):
  """[hybrid_policy_dynamic

    Simulating a Min Max periodic policy, diffirent from R,s,S because here order is made in case the Inventory position reaches min or the
    ordering period comes 
    the Max is dynamically calculated based on a forecast vector. .

    The Function takes a demand vector, mean of demand ,sd,lead time and requested service level to simulate an inventory system, 
    orders are lost if inventory level is less than requested demand, also ordering is made at
    day t+1, metrics like item fill rate and cycle service level are calculated. 
    the min is calculated based on a normal distribution or a poisson distribution, also min can be set manually.
    Max - inventory position is ordered whenever inventory position reaches min or at the period of review .]

   Args:
      demand ([float]): [demand in N time periods]
      forecast ([float]): [the forecast vector of equal n periods to demand.]
      leadtime ([float]): [lead time from order to arrival]
      Review_period ([float]):[the number of periods where every order is allowed to be made.]
      service_level ([float]): [cycle service level requested]
      initial_inventory_level ([float]): [Default is False and simulation starts with min as inventory level]
      Min_to_max ([float]): [the ratio of min to max calculation , default 0.6 but can be changed manually.]
      Min  ([float]):[Default is False and min is calculated based on mean,demand and lead time unless set manually]
      one_step_forecast ([logical]): [Default is true where demand lead time is calcluated as(forecast at period t * leadtime)]
      distribution ([str]) :[distribution  to calculate safety stock based on demand distribution, current choices are 
                             'normal' or 'poisson']
      shortage_cost (bool, optional): [shortage cost per unit of sales lost]. Defaults to False.]
      inventory_cost (bool, optional): [inventory cost per unit.]. Defaults to False.]
      ordering_cost (bool, optional): [ordering cost for every time an order is made. Defaults to False.]
      error_metric ([str]):[metric is currently 'rmse' and 'mae', this calculates the error
                            from period 1 to period t unless metric_windows is set.]
      metric_windows  ([float]): [for exammple if it is set to 4 rmse for t is calculated from t-1 to t-4,default is FALSE]
      plot  (bool, optional): [Default is False, if true a plot is generated]
   Returns:
      [list]: [a list of two, the simulation and the metrics.]

   Examples:
      [hybrid_poicy_dynamic(demand=numpy.random.uniform(2,20,200).round(),
                     forecast=numpy.random.uniform(2,20,200).round(), 
                     leadtime=8, Review_period=10, service_level=0.95)]

  """    

  
###########################################################
  
  L = leadtime
  N = len(demand) 
  
  demand=numpy.append(numpy.array(0),demand)
  forecast= numpy.append(numpy.array(0),forecast)

  if (one_step_forecast== True):
       dl=forecast*leadtime
  else :
       dl= numpy.zeros(len(demand))
    
       for i in range(len(demand)):
           dl[i]= sum(forecast[i : min((i+leadtime-1),len(dl))])
  
  metric= numpy.zeros(len(demand))

  if(error_metric == 'rmse'):
      if (type(metric_windows)== bool):
          for i in range(1,len(demand)):
              metric[i]= numpy.sqrt(numpy.mean((demand[1:i-1]- forecast[1:i-1])**2))
  
      else :
          for i in range(1,len(demand)):
              metric[i]= numpy.sqrt(numpy.mean((demand[max((i- metric_windows),0):(i-1)]- forecast[max((i- metric_windows),0):(i-1)])**2))

  if(error_metric == 'mae'):
      if (type(metric_windows)== bool):
          for i in range(1,len(demand)):
              metric[i]= numpy.mean(abs((demand[1:i-1]- forecast[1:i-1])**2))
  
      else :
          for i in range(1,len(demand)):
              metric[i]= numpy.mean(abs((demand[max((i- metric_windows),0):(i-1)]- forecast[max((i- metric_windows),0):(i-1)])**2))

  metric[numpy.isnan(metric)]= numpy.round(metric[numpy.isnan(metric)==False].mean())



  def classfication(demand):
      def intervals(x):
          y=numpy.zeros(len(x)+2)
          k=0
          counter=0
          for tmp in range(len(x)):
              if (x[tmp]==0):
                  counter= counter +1
              else :
                  k=k+1
                  y[k]= counter
                  counter =1
          y= y[y>0]
          y[numpy.isnan(y)]=1
          return y
      def demand1(x):
          y= x[x!=0]
          return y
      D = demand1(demand)
      ADI = numpy.mean(intervals(demand))
      CV2 = (numpy.std(D)/numpy.mean(D))**2
      
      if (ADI > 4/3):
          if (CV2 >0.5):
              type1= 'Lumpy'
          else :
              type1= 'Intermittent'
      else  :
          if(CV2 >0.5):
              type1= 'Erratic'
          else:
              type1= 'Smooth'
               
      return type1
  class1= classfication(demand)
   
  sigmadl= metric* numpy.sqrt(leadtime)
  
  if(distribution== 'normal'):
      saftey_stock= sigmadl *  scipy.stats.norm.ppf(service_level)
  elif(distribution== 'poisson'):
      saftey_stock=  scipy.stats.poisson.ppf(service_level, demand*leadtime) - (demand*leadtime)

  Max= numpy.round(dl+saftey_stock)

  if(type(Min) ==bool):
      Min= numpy.round(Min_to_max *Max)
    
  else :
      Min= numpy.repeat(Min,N+1)
    
  
  Min[numpy.isnan(Min)]= numpy.round(Min[numpy.isnan(Min)==False].mean())
  Max[numpy.isnan(Max)]= numpy.round(Max[numpy.isnan(Max)==False].mean())
  Max[0]= Max.mean().round()

  
  
  
  
  order = numpy.zeros(N+1)
  I = numpy.zeros(N+1)
  IP = numpy.zeros(N+1)
  sales = numpy.zeros(N+1)
  recieved = numpy.zeros(N+1)
  order[0]=0




  
  if(type(initial_inventory_level)==bool):
      IP[0] = I[0] =  Max[0]
  else :
      IP[0] = I[0] =  initial_inventory_level
    
  
  def numpy_rep(x, reps=1, each=False, length=0):
    """ implementation of functionality of rep() and rep_len() from R

    Attributes:
        x: numpy array, which will be flattened
        reps: int, number of times x should be repeated
        each: logical; should each element be repeated reps times before the next
        length: int, length desired; if >0, overrides reps argument
    """
    if length > 0:
        reps = numpy.int(numpy.ceil(length / x.size))
    x = numpy.repeat(x, reps)
    if(not each):
        x = x.reshape(-1, reps).T.ravel() 
    if length > 0:
        x = x[0:length]
    return(x)
  ordering_time= numpy_rep(numpy.repeat([0,1], [Review_period-1,1]),each=False,reps=len(demand))
  ordering_time=numpy.append(numpy.array(0), ordering_time)
  
  def hibrid_fun(t):
      
      if((IP[t-1] <= Min[t])):
                 a= max((Max[t] - IP[t-1]),0) * (IP[t-1] <= Min[t])
      if not(IP[t-1] <= Min[t]) :
                  a=max((Max[t] - IP[t-1]),0) * (ordering_time[t])           
      return a
  for t in range(1,L+1):
    sales[t] = min (demand[t], I[t-1])
    I[t] = I[t-1] - sales[t]
    order[t] = hibrid_fun(t)
    IP[t] =  IP[t-1] + order[t] - sales[t]
    
  
  
  for t in range(L+1,N+1):
    sales[t] = min(demand[t], I[t-1] + order[t-L])
    I[t] = I[t-1] + order[t-L] - sales[t]
    order[t] = hibrid_fun(t)
    IP[t] = IP[t-1] + order[t] - sales[t]
    recieved[t]= order[t-L]
  
  
  data=pandas.DataFrame({'period':range(1,N+2),'demand':demand,'forecast':forecast,'sales':sales,'inventory_level':I,
                   'inventory_position':IP,'saftey_stock': saftey_stock,'min':Min,'order': order,'max':Max,
                   'recieved':recieved},index= range(1,N+2))
  
  data['lost_order']= data['demand'] - data['sales']
  error_mape=abs(demand-forecast)/abs(demand)
  error_mape= error_mape[numpy.isnan(error_mape)==False]
  metrics= pandas.DataFrame({'shortage_cost': sum(data['lost_order'])*shortage_cost,
                       'inventory_cost': sum(data['inventory_level'])*inventory_cost,
                       'average_inventory_level': data['inventory_level'].mean(),'total_orders':len(order[order>0]),
                       'total_lost_sales': sum(data['lost_order']),
                       'ordering_cost':  len(data['order'][data['order']>0]) *ordering_cost,'average_ordering_quantity':(order[order>0]).mean(),
                       'ordering_interval': str(round(len(demand)/len(order[order>0]),2))+'_periods',
                       'Item_fill_rate': 1-(sum(data['lost_order'][data['lost_order']>0]))/sum(demand[1:(len(demand)-1)]),
                       'cycle_service_level': 1-(len(data['lost_order'][data['lost_order']>0])/(len(demand)-1)),
                       'saftey_stock':saftey_stock.mean(),'average_sales': sales.mean() },index= [0])
  metrics['average_flow_time(throughput)']= metrics['average_inventory_level']/metrics['average_sales']
  metrics['class']= class1
  metrics['rmse']= numpy.sqrt(numpy.mean((demand-forecast)**2))
  metrics['mae']= numpy.mean(abs(demand-forecast))
  metrics['me']= numpy.mean(demand-forecast)
  metrics['mape']= numpy.mean(error_mape *100)


  
  if(plot== True):
      large_rockwell_template = dict(
       layout=plotly.graph_objects.Layout(title_font=dict(family="Rockwell", size=24))
                                      )
      fig= plotly.graph_objects.Figure()
        
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['inventory_level'],
                                                 mode='markers',marker=dict(color='green'),
                                                 name= 'inventory level'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['order'],
                    line= dict(color= 'grey'),
                    name='order'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['demand'],
                    line= dict(color= 'royalblue'),
                    name='demand'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['forecast'],
                    line= dict(color= 'green'),
                    name='forecast'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['sales'],
                    line= dict(color= 'orange'),
                    name='sales'))
      fig.update_layout(title= 'Hybrid Policy Dynamic',
                   xaxis_title='Period',
                   yaxis_title='Demand' ,template=large_rockwell_template)


      fig.show()
      
  
  
  a= [data,metrics]
  return a 

def hybrid(demand, leadtime, service_level,Review_period,Min_to_max=0.6,distribution= 'normal',mean = False, sd=False,
                       shortage_cost = False, inventory_cost = False, 
                       ordering_cost = False,initial_inventory_level = False,
                       Min= False,Max=False,recalculate=False,recalculate_windows=False,plot=False):
  """[Simulating a hybrid Min Max periodic policy, 
     diffirent from R,s,S because here order is made in case the Inventory position reaches min or the
     ordering period comes  .
     The Function takes a demand vector, mean of demand ,sd,lead time and requested service level to simulate an inventory system, 
     orders are lost if inventory level is less than requested demand, also ordering is made at
    day t+1, metrics like item fill rate and cycle service level are calculated. 
    the min is calculated based on a normal distribution or a poisson distribution, also min can be set manually.
    Max - inventory position is ordered whenever inventory position reaches min or at the period of review ]

   Args:
      demand ([float]): [demand in N time periods]
      leadtime ([float]): [lead time from order to arrival]
      service_level ([float]): [cycle service level requested]
      Review_period ([float]):the number of periods where every order is allowed to be made.
      Min_to_max ([float]): the ratio of min to max calculation , default 0.6 but can be changed manually.
      distribution ([str]) :distribution  to calculate safety stock based on demand distribution, current choices are 'normal' or 'poisson'
      mean ([float]): [average demand in N time periods.]
      sd ([float]): [standard deviation in N time periods.]
      shortage_cost (bool, optional): [shortage cost per unit of sales lost]. Defaults to False.
      inventory_cost (bool, optional): [inventory cost per unit.]. Defaults to False.
      ordering_cost (bool, optional): [ordering cost for every time an order is made.]. Defaults to False.
      initial_inventory_level ([float]): Default is False and simulation starts with min as inventory level
      min  ([float]):Default is False and min is calculated based on mean,demand and lead time unless set manually
      Max  ([float]):Default is False and max is calculated as a ratio to min,otherwise set manually.
      recalculate  ([float]): the mean and sd is recalculated every X periods from first period to x,default is FALSE .
      recalculate_windows  ([float]): the min  mean and sd windows to recalculate , for exammple if it is set to 4 mean and sd
                           is calculated from t to t-4,,default is FALSE .
      plot  (bool, optional): Default is False, if true a plot is generated
   Returns:
      [list]: [a list of two, the simulation and the metrics.]

   Examples:
      [hybrid(demand=numpy.random.uniform(2,20,200).round(),Min_to_max=0.5,leadtime=5,
              service_level=0.95,Review_period=10,plot=True)]

  """    

  L = leadtime
  N = len(demand)
  
  if( type(recalculate) != bool):
      mean = numpy.zeros(N+1)
      sd= numpy.zeros(N+1)
      minn= numpy.zeros(N+1)
      Max= numpy.zeros(N+1)
      for i in range(len(mean)):
          mean[i]= numpy.mean(demand[0:i])if (numpy.isnan(numpy.mean(demand[0:i]))==False) else demand[0]
          sd[i]= numpy.std(demand[0:i])if (numpy.isnan(numpy.std(demand[0:i]))==False) else 0
          if(distribution== 'normal'):
              minn[i]= round((mean[i] *(leadtime+Review_period))+ ((sd[i]*numpy.sqrt(leadtime+Review_period))* scipy.stats.norm.ppf(service_level)))
          else :
              minn[i]= scipy.stats.poisson.ppf(service_level,mean[i]*(leadtime+Review_period))
         
      if(type(recalculate_windows) != bool):
          mean[0]= demand[0]
          sd[0]= numpy.std(demand)
          for i in range(1,len(mean)):
              mean[i]= (numpy.mean(demand[max((i- recalculate_windows),0):(i-1)])if 
                        (len(demand[max((i- recalculate_windows),0):(i-1)])>0) else demand[0]) 
              sd[i]= (numpy.std(demand[max((i- recalculate_windows),0):(i-1)])if 
                        (len(demand[max((i- recalculate_windows),0):(i-1)])>0) else sd[0]) 
              if(distribution== 'normal'):
                  minn[i]= round((mean[i] *(leadtime+Review_period))+ ((sd[i]*numpy.sqrt(leadtime+Review_period))* scipy.stats.norm.ppf(service_level)))
              else :
                  minn[i]= scipy.stats.poisson.ppf(service_level,mean[i]*(leadtime+Review_period))
      Max[0]= minn[1]  
      for i in range(1,len(Max)):
          Max[i]= Max[i-1] if((i % recalculate) != 0) else minn[i]
  
  def classfication(demand):
      def intervals(x):
          y=numpy.zeros(len(x)+2)
          k=0
          counter=0
          for tmp in range(len(x)):
              if (x[tmp]==0):
                  counter= counter +1
              else :
                  k=k+1
                  y[k]= counter
                  counter =1
          y= y[y>0]
          y[numpy.isnan(y)]=1
          return y
      def demand1(x):
          y= x[x!=0]
          return y
      D = demand1(demand)
      ADI = numpy.mean(intervals(demand))
      CV2 = (numpy.std(D)/numpy.mean(D))**2
      
      if (ADI > 4/3):
          if (CV2 >0.5):
              type1= 'Lumpy'
          else :
              type1= 'Intermittent'
      else  :
          if(CV2 >0.5):
              type1= 'Erratic'
          else:
              type1= 'Smooth'
               
      return type1
  class1= classfication(demand)
   
  if((type(mean)== bool) & (type(recalculate)==bool)):
    mean= numpy.mean(demand)
  elif ((type(mean)!= bool) & (type(recalculate)==bool)):
    mean=mean
  
  
  if((type(sd)== bool) & (type(recalculate)==bool)):
    sd= numpy.std(demand)
  elif ((type(sd)!= bool) & (type(recalculate)==bool)):
    sd =sd
  
  
  if ((type(Max) != bool) & (type(recalculate) == bool)):
    
    Max= Max
    Max =  numpy.repeat(Max,N+1)
    
  elif((distribution== 'normal')& (type(recalculate)== bool)):
    
    Max = round((mean *(leadtime+Review_period))+ ((sd*numpy.sqrt(leadtime+Review_period))* scipy.stats.norm.ppf(service_level)))
    Max =  numpy.repeat(Max,N+1)
    
  elif ((distribution== 'poisson') & (type(recalculate)== bool)):
    
    Max = scipy.stats.poisson.ppf(service_level,mean[i]*(leadtime+Review_period))
    Max =  numpy.repeat(Max,N+1)
    
  saftey_stock= Max- (mean *(leadtime+Review_period))          

  if(type(Min)==bool):
    Min= numpy.round(Min_to_max *Max)
  else:
    Min=numpy.repeat(Min,len(Max))
  


  order = numpy.zeros(N+1)
  I = numpy.zeros(N+1)
  IP = numpy.zeros(N+1)
  sales = numpy.zeros(N+1)
  recieved = numpy.zeros(N+1)
  order[0]=0
  demand= numpy.append(numpy.array(0),demand)

  if(initial_inventory_level==False):
    IP[0] = I[0] =  Max[0]
  else :
    IP[0] = I[0] =  initial_inventory_level
  
    
  def numpy_rep(x, reps=1, each=False, length=0):
    """ implementation of functionality of rep() and rep_len() from R

    Attributes:
        x: numpy array, which will be flattened
        reps: int, number of times x should be repeated
        each: logical; should each element be repeated reps times before the next
        length: int, length desired; if >0, overrides reps argument
    """
    if length > 0:
        reps = numpy.int(numpy.ceil(length / x.size))
    x = numpy.repeat(x, reps)
    if(not each):
        x = x.reshape(-1, reps).T.ravel() 
    if length > 0:
        x = x[0:length]
    return(x)
  ordering_time= numpy_rep(numpy.repeat([0,1], [Review_period-1,1]),each=False,reps=len(demand))
  ordering_time=numpy.append(numpy.array(0), ordering_time)
  
  def hibrid_fun(t):
      
      if((IP[t-1] <= Min[t])):
                 a= (Max[t] - IP[t-1]) * (IP[t-1] <= Min[t])
      if not(IP[t-1] <= Min[t]) :
                  a=(Max[t] - IP[t-1]) * (ordering_time[t])           
      return a
  for t in range(1,L+1):
    sales[t] = min (demand[t], I[t-1])
    I[t] = I[t-1] - sales[t]
    order[t] = hibrid_fun(t)
    IP[t] =  IP[t-1] + order[t] - sales[t]
    
  
  
  for t in range(L+1,N+1):
    sales[t] = min(demand[t], I[t-1] + order[t-L])
    I[t] = I[t-1] + order[t-L] - sales[t]
    order[t] = hibrid_fun(t)
    IP[t] = IP[t-1] + order[t] - sales[t]
    recieved[t]= order[t-L]
  
  
  data=pandas.DataFrame({'period':range(1,N+2),'demand':demand,'sales':sales,'inventory_level':I,
                   'inventory_position':IP,'saftey_stock': saftey_stock,'min':Min,'order': order,'max':Max,
                   'recieved':recieved},index= range(1,N+2))
  
  data['lost_order']= data['demand'] - data['sales']
  
  metrics= pandas.DataFrame({'shortage_cost': sum(data['lost_order'])*shortage_cost,
                       'inventory_cost': sum(data['inventory_level'])*inventory_cost,
                       'average_inventory_level': data['inventory_level'].mean(),'total_orders':len(order[order>0]),
                       'total_lost_sales': sum(data['lost_order']),
                       'ordering_cost':  len(data['order'][data['order']>0]) *ordering_cost,'average_ordering_quantity':(order[order>0]).mean(),
                       'ordering_interval': str(round(len(demand)/len(order[order>0]),2))+'_periods',
                       'Item_fill_rate': 1-(sum(data['lost_order'][data['lost_order']>0]))/sum(demand[1:(len(demand)-1)]),
                       'cycle_service_level': 1-(len(data['lost_order'][data['lost_order']>0])/(len(demand)-1)),
                       'saftey_stock':saftey_stock.mean(),'average_sales': sales.mean() },index= [0])
  metrics['average_flow_time(throughput)']= metrics['average_inventory_level']/metrics['average_sales']
  metrics['class']= class1
  
  if(plot== True):
      large_rockwell_template = dict(
       layout=plotly.graph_objects.Layout(title_font=dict(family="Rockwell", size=24))
                                      )
      fig= plotly.graph_objects.Figure()
        
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['inventory_level'],
                                                 mode='markers',marker=dict(color='green'),
                                                 name= 'inventory level'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['order'],
                    line= dict(color= 'grey'),
                    name='order'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['demand'],
                    line= dict(color= 'royalblue'),
                    name='demand'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['sales'],
                    line= dict(color= 'orange'),
                    name='sales'))
      fig.update_layout(title= 'Hybrid Policy',
                   xaxis_title='Period',
                   yaxis_title='Demand' ,template=large_rockwell_template)


      fig.show()
      
  
  
  a= [data,metrics]
  return a 

def Max_policy_dynamic(demand,forecast, leadtime, service_level,initial_inventory_level=False,
                               one_step_forecast=True,shortage_cost = False, 
                inventory_cost = False, ordering_cost = False,
                distribution= 'normal', error_metric= 'rmse',metric_windows= False,plot=False):
  """[Max_policy_dynamic

    Simulating a  max policy or also called S policy, the Max is dynamically calculated based on a forecast vector.

    The Function takes a demand vector, mean of demand ,sd,lead time and requested service level to simulate an inventory system, 
    orders are lost if inventory level is less than requested demand, also ordering is made at
    day t+1, metrics like item fill rate and cycle service level are calculated. 
    the min is calculated based on a normal distribution or a poisson distribution, also min can be set manually.
    and order is equal to max((Max[t]-inventory position [t-1])+ sales[t],0).]

   Args:
      demand ([float]): [demand in N time periods]
      forecast ([float]): [the forecast vector of equal n periods to demand.]
      leadtime ([float]): [lead time from order to arrival]
      service_level ([float]): [cycle service level requested]
      initial_inventory_level ([float]): [Default is False and simulation starts with min as inventory level]
      one_step_forecast ([logical]): [Default is true where demand lead time is calcluated as(forecast at period t * leadtime)]
      shortage_cost (bool, optional): [shortage cost per unit of sales lost]. Defaults to False.]
      inventory_cost (bool, optional): [inventory cost per unit.]. Defaults to False.]
      ordering_cost (bool, optional): [ordering cost for every time an order is made. Defaults to False.]
      distribution ([str]) :[distribution  to calculate safety stock based on demand distribution, current choices are 
                             'normal' or 'poisson']
      error_metric ([str]):[metric is currently 'rmse' and 'mae', this calculates the error
                            from period 1 to period t unless metric_windows is set.]
      metric_windows  ([float]): [for exammple if it is set to 4 rmse for t is calculated from t-1 to t-4,default is FALSE]
      plot  (bool, optional): [Default is False, if true a plot is generated]
   Returns:
      [list]: [a list of two, the simulation and the metrics.]

   Examples:
      [Max_policy_dynamic(demand=numpy.random.uniform(2,20,200).round(),forecast=numpy.random.uniform(2,20,200).round(),
                          leadtime=5,service_level=0.9)]

  """    

  
###########################################################
  
  L = leadtime
  N = len(demand) 

  
  demand=numpy.append(numpy.array(0),demand)
  forecast= numpy.append(numpy.array(0),forecast)

  if (one_step_forecast== True):
       dl=forecast*leadtime
  else :
       dl= numpy.zeros(len(demand))
    
       for i in range(len(demand)):
           dl[i]= sum(forecast[i : min((i+leadtime-1),len(dl))])
  
  metric= numpy.zeros(len(demand))

  if(error_metric == 'rmse'):
      if (type(metric_windows)== bool):
          for i in range(1,len(demand)):
              metric[i]= numpy.sqrt(numpy.mean((demand[1:i-1]- forecast[1:i-1])**2))
  
      else :
          for i in range(1,len(demand)):
              metric[i]= numpy.sqrt(numpy.mean((demand[max((i- metric_windows),0):(i-1)]- forecast[max((i- metric_windows),0):(i-1)])**2))

  if(error_metric == 'mae'):
      if (type(metric_windows)== bool):
          for i in range(1,len(demand)):
              metric[i]= numpy.mean(abs((demand[1:i-1]- forecast[1:i-1])**2))
  
      else :
          for i in range(1,len(demand)):
              metric[i]= numpy.mean(abs((demand[max((i- metric_windows),0):(i-1)]- forecast[max((i- metric_windows),0):(i-1)])**2))

  metric[numpy.isnan(metric)]= numpy.round(metric[numpy.isnan(metric)==False].mean())



  def classfication(demand):
      def intervals(x):
          y=numpy.zeros(len(x)+2)
          k=0
          counter=0
          for tmp in range(len(x)):
              if (x[tmp]==0):
                  counter= counter +1
              else :
                  k=k+1
                  y[k]= counter
                  counter =1
          y= y[y>0]
          y[numpy.isnan(y)]=1
          return y
      def demand1(x):
          y= x[x!=0]
          return y
      D = demand1(demand)
      ADI = numpy.mean(intervals(demand))
      CV2 = (numpy.std(D)/numpy.mean(D))**2
      
      if (ADI > 4/3):
          if (CV2 >0.5):
              type1= 'Lumpy'
          else :
              type1= 'Intermittent'
      else  :
          if(CV2 >0.5):
              type1= 'Erratic'
          else:
              type1= 'Smooth'
               
      return type1
  class1= classfication(demand)
   
  sigmadl= metric* numpy.sqrt(leadtime)
  
  if(distribution== 'normal'):
      saftey_stock= sigmadl *  scipy.stats.norm.ppf(service_level)
  elif(distribution== 'poisson'):
      saftey_stock=  scipy.stats.poisson.ppf(service_level, demand*leadtime) - (demand*leadtime)

  Max= numpy.round(dl+saftey_stock)

    
  
  Max[numpy.isnan(Max)]= numpy.round(Max[numpy.isnan(Max)==False].mean())
  Max[0]= Max.mean().round()

  
  
  
  
  order = numpy.zeros(N+1)
  I = numpy.zeros(N+1)
  IP = numpy.zeros(N+1)
  sales = numpy.zeros(N+1)
  recieved = numpy.zeros(N+1)
  order[0]=0
  
  if(initial_inventory_level==False):
      IP[0] = I[0] =  Max[0]
  else :
      IP[0] = I[0] =  initial_inventory_level
    
  
  def numpy_rep(x, reps=1, each=False, length=0):
    """ implementation of functionality of rep() and rep_len() from R

    Attributes:
        x: numpy array, which will be flattened
        reps: int, number of times x should be repeated
        each: logical; should each element be repeated reps times before the next
        length: int, length desired; if >0, overrides reps argument
    """
    if length > 0:
        reps = numpy.int(numpy.ceil(length / x.size))
    x = numpy.repeat(x, reps)
    if(not each):
        x = x.reshape(-1, reps).T.ravel() 
    if length > 0:
        x = x[0:length]
    return(x)
 
  
  for t in range(1,L+1):
    sales[t] = min (demand[t], I[t-1])
    I[t] = I[t-1] - sales[t]
    order[t] =  max((Max[t] - IP[t-1]+sales[t]),0)
    IP[t] =  IP[t-1] + order[t] - sales[t]
    
  
  
  for t in range(L+1,N+1):
    sales[t] = min(demand[t], I[t-1] + order[t-L])
    I[t] = I[t-1] + order[t-L] - sales[t]
    order[t] =  max((Max[t] - IP[t-1]+sales[t]),0)
    IP[t] = IP[t-1] + order[t] - sales[t]
    recieved[t]= order[t-L]
  
  
  data=pandas.DataFrame({'period':range(1,N+2),'demand':demand,'forecast':forecast,'sales':sales,'inventory_level':I,
                   'inventory_position':IP,'saftey_stock': saftey_stock,'order': order,'max':Max,
                   'recieved':recieved},index= range(1,N+2))
  
  data['lost_order']= data['demand'] - data['sales']
  error_mape=abs(demand-forecast)/abs(demand)
  error_mape= error_mape[numpy.isnan(error_mape)==False]
  metrics= pandas.DataFrame({'shortage_cost': sum(data['lost_order'])*shortage_cost,
                       'inventory_cost': sum(data['inventory_level'])*inventory_cost,
                       'average_inventory_level': data['inventory_level'].mean(),'total_orders':len(order[order>0]),
                       'total_lost_sales': sum(data['lost_order']),
                       'ordering_cost':  len(data['order'][data['order']>0]) *ordering_cost,'average_ordering_quantity':(order[order>0]).mean(),
                       'ordering_interval': str(round(len(demand)/len(order[order>0]),2))+'_periods',
                       'Item_fill_rate': 1-(sum(data['lost_order'][data['lost_order']>0]))/sum(demand[1:(len(demand)-1)]),
                       'cycle_service_level': 1-(len(data['lost_order'][data['lost_order']>0])/(len(demand)-1)),
                       'saftey_stock':saftey_stock.mean(),'average_sales': sales.mean() },index= [0])
  metrics['average_flow_time(throughput)']= metrics['average_inventory_level']/metrics['average_sales']
  metrics['class']= class1
  metrics['rmse']= numpy.sqrt(numpy.mean((demand-forecast)**2))
  metrics['mae']= numpy.mean(abs(demand-forecast))
  metrics['me']= numpy.mean(demand-forecast)
  metrics['mape']= numpy.mean(error_mape *100)


  
  if(plot== True):
      large_rockwell_template = dict(
       layout=plotly.graph_objects.Layout(title_font=dict(family="Rockwell", size=24))
                                      )
      fig= plotly.graph_objects.Figure()
        
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['inventory_level'],
                                                 mode='markers',marker=dict(color='green'),
                                                 name= 'inventory level'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['order'],
                    line= dict(color= 'grey'),
                    name='order'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['demand'],
                    line= dict(color= 'royalblue'),
                    name='demand'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['forecast'],
                    line= dict(color= 'green'),
                    name='forecast'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['sales'],
                    line= dict(color= 'orange'),
                    name='sales'))
      fig.update_layout(title= 'Max Policy Dynamic',
                   xaxis_title='Period',
                   yaxis_title='Demand' ,template=large_rockwell_template)


      fig.show()
      
  
  
  a= [data,metrics]
  return a 

def R_S_dynamic(demand,forecast, leadtime, Review_period,service_level,initial_inventory_level=False,
                               one_step_forecast=True,shortage_cost = False, 
                inventory_cost = False, ordering_cost = False,
                distribution= 'normal', error_metric= 'rmse',metric_windows= False,plot=False):
  """[Simulating a  periodic policy, different from R,s,S because here order is made at the ordering time without a min(reordering quantity)
     the Max is dynamically calculated based on a forecast vector. .

     The Function takes a demand vector, forecast vector and requested service level to simulate an inventory system, 
     orders are lost if inventory level is less than requested demand, also ordering is made at
    day t+1, metrics like item fill rate and cycle service level are calculated. 
    the min is calculated based on a normal distribution or a poisson distribution, also min can be set manually.
    Max - inventory position is ordered  at the period of review ]

   Args:
      demand ([float]): [demand in N time periods]
      forecast ([float]): [the forecast vector of equal n periods to demand.]
      leadtime ([float]): [lead time from order to arrival]
      Review_period ([float]):[the number of periods where every order is allowed to be made.]
      service_level ([float]): [cycle service level requested]
      initial_inventory_level ([float]): [Default is False and simulation starts with min as inventory level]
      Min_to_max ([float]): [the ratio of min to max calculation , default 0.6 but can be changed manually.]
      Min  ([float]):[Default is False and min is calculated based on mean,demand and lead time unless set manually]
      one_step_forecast ([logical]): [Default is true where demand lead time is calcluated as(forecast at period t * leadtime)]
      shortage_cost (bool, optional): [shortage cost per unit of sales lost]. Defaults to False.]
      inventory_cost (bool, optional): [inventory cost per unit.]. Defaults to False.]
      ordering_cost (bool, optional): [ordering cost for every time an order is made. Defaults to False.]
      distribution ([str]) :[distribution  to calculate safety stock based on demand distribution, current choices are 
                             'normal' or 'poisson']
      error_metric ([str]):[metric is currently 'rmse' and 'mae', this calculates the error
                            from period 1 to period t unless metric_windows is set.]
      metric_windows  ([float]): [for exammple if it is set to 4 rmse for t is calculated from t-1 to t-4,default is FALSE]
      plot  (bool, optional): [Default is False, if true a plot is generated]
   Returns:
      [list]: [a list of two, the simulation and the metrics.]

   Examples:
      [R_S_dynamic(demand=numpy.random.uniform(2,20,200).round(),
                     forecast=numpy.random.uniform(2,20,200).round(), leadtime=8, Review_period=10, service_level=0.95)]

  """    
  
###########################################################
  
  L = leadtime
  N = len(demand) 
  
  demand=numpy.append(numpy.array(0),demand)
  forecast= numpy.append(numpy.array(0),forecast)

  if (one_step_forecast== True):
       dl=forecast*leadtime
  else :
       dl= numpy.zeros(len(demand))
    
       for i in range(len(demand)):
           dl[i]= sum(forecast[i : min((i+leadtime-1),len(dl))])
  
  metric= numpy.zeros(len(demand))

  if(error_metric == 'rmse'):
      if (type(metric_windows)== bool):
          for i in range(1,len(demand)):
              metric[i]= numpy.sqrt(numpy.mean((demand[1:i-1]- forecast[1:i-1])**2))
  
      else :
          for i in range(1,len(demand)):
              metric[i]= numpy.sqrt(numpy.mean((demand[max((i- metric_windows),0):(i-1)]- forecast[max((i- metric_windows),0):(i-1)])**2))

  if(error_metric == 'mae'):
      if (type(metric_windows)== bool):
          for i in range(1,len(demand)):
              metric[i]= numpy.mean(abs((demand[1:i-1]- forecast[1:i-1])**2))
  
      else :
          for i in range(1,len(demand)):
              metric[i]= numpy.mean(abs((demand[max((i- metric_windows),0):(i-1)]- forecast[max((i- metric_windows),0):(i-1)])**2))

  metric[numpy.isnan(metric)]= numpy.round(metric[numpy.isnan(metric)==False].mean())



  def classfication(demand):
      def intervals(x):
          y=numpy.zeros(len(x)+2)
          k=0
          counter=0
          for tmp in range(len(x)):
              if (x[tmp]==0):
                  counter= counter +1
              else :
                  k=k+1
                  y[k]= counter
                  counter =1
          y= y[y>0]
          y[numpy.isnan(y)]=1
          return y
      def demand1(x):
          y= x[x!=0]
          return y
      D = demand1(demand)
      ADI = numpy.mean(intervals(demand))
      CV2 = (numpy.std(D)/numpy.mean(D))**2
      
      if (ADI > 4/3):
          if (CV2 >0.5):
              type1= 'Lumpy'
          else :
              type1= 'Intermittent'
      else  :
          if(CV2 >0.5):
              type1= 'Erratic'
          else:
              type1= 'Smooth'
               
      return type1
  class1= classfication(demand)
   
  sigmadl= metric* numpy.sqrt(leadtime)
  
  if(distribution== 'normal'):
      saftey_stock= sigmadl *  scipy.stats.norm.ppf(service_level)
  elif(distribution== 'poisson'):
      saftey_stock=  scipy.stats.poisson.ppf(service_level, demand*leadtime) - (demand*leadtime)

  Max= numpy.round(dl+saftey_stock)

    
  
  Max[numpy.isnan(Max)]= numpy.round(Max[numpy.isnan(Max)==False].mean())
  Max[0]= Max.mean().round()

  
  
  
  
  order = numpy.zeros(N+1)
  I = numpy.zeros(N+1)
  IP = numpy.zeros(N+1)
  sales = numpy.zeros(N+1)
  recieved = numpy.zeros(N+1)
  order[0]=0
  
  if(initial_inventory_level==False):
      IP[0] = I[0] =  Max[0]
  else :
      IP[0] = I[0] =  initial_inventory_level
    
  
  def numpy_rep(x, reps=1, each=False, length=0):
    """ implementation of functionality of rep() and rep_len() from R

    Attributes:
        x: numpy array, which will be flattened
        reps: int, number of times x should be repeated
        each: logical; should each element be repeated reps times before the next
        length: int, length desired; if >0, overrides reps argument
    """
    if length > 0:
        reps = numpy.int(numpy.ceil(length / x.size))
    x = numpy.repeat(x, reps)
    if(not each):
        x = x.reshape(-1, reps).T.ravel() 
    if length > 0:
        x = x[0:length]
    return(x)
  ordering_time= numpy_rep(numpy.repeat([0,1], [Review_period-1,1]),each=False,reps=len(demand))
  ordering_time=numpy.append(numpy.array(0), ordering_time)
  
  
  for t in range(1,L+1):
    sales[t] = min (demand[t], I[t-1])
    I[t] = I[t-1] - sales[t]
    order[t] = max((Max[t] - IP[t-1]),0) *ordering_time[t]
    IP[t] =  IP[t-1] + order[t] - sales[t]
    
  
  
  for t in range(L+1,N+1):
    sales[t] = min(demand[t], I[t-1] + order[t-L])
    I[t] = I[t-1] + order[t-L] - sales[t]
    order[t] = max((Max[t] - IP[t-1]),0) *ordering_time[t]
    IP[t] = IP[t-1] + order[t] - sales[t]
    recieved[t]= order[t-L]
  
  
  data=pandas.DataFrame({'period':range(1,N+2),'demand':demand,'forecast':forecast,'sales':sales,'inventory_level':I,
                   'inventory_position':IP,'saftey_stock': saftey_stock,'order': order,'max':Max,
                   'recieved':recieved},index= range(1,N+2))
  
  data['lost_order']= data['demand'] - data['sales']
  error_mape=abs(demand-forecast)/abs(demand)
  error_mape= error_mape[numpy.isnan(error_mape)==False]
  metrics= pandas.DataFrame({'shortage_cost': sum(data['lost_order'])*shortage_cost,
                       'inventory_cost': sum(data['inventory_level'])*inventory_cost,
                       'average_inventory_level': data['inventory_level'].mean(),'total_orders':len(order[order>0]),
                       'total_lost_sales': sum(data['lost_order']),
                       'ordering_cost':  len(data['order'][data['order']>0]) *ordering_cost,'average_ordering_quantity':(order[order>0]).mean(),
                       'ordering_interval': str(round(len(demand)/len(order[order>0]),2))+'_periods',
                       'Item_fill_rate': 1-(sum(data['lost_order'][data['lost_order']>0]))/sum(demand[1:(len(demand)-1)]),
                       'cycle_service_level': 1-(len(data['lost_order'][data['lost_order']>0])/(len(demand)-1)),
                       'saftey_stock':saftey_stock.mean(),'average_sales': sales.mean() },index= [0])
  metrics['average_flow_time(throughput)']= metrics['average_inventory_level']/metrics['average_sales']
  metrics['class']= class1
  metrics['rmse']= numpy.sqrt(numpy.mean((demand-forecast)**2))
  metrics['mae']= numpy.mean(abs(demand-forecast))
  metrics['me']= numpy.mean(demand-forecast)
  metrics['mape']= numpy.mean(error_mape *100)


  
  if(plot== True):
      large_rockwell_template = dict(
       layout=plotly.graph_objects.Layout(title_font=dict(family="Rockwell", size=24))
                                      )
      fig= plotly.graph_objects.Figure()
        
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['inventory_level'],
                                                 mode='markers',marker=dict(color='green'),
                                                 name= 'inventory level'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['order'],
                    line= dict(color= 'grey'),
                    name='order'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['demand'],
                    line= dict(color= 'royalblue'),
                    name='demand'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['forecast'],
                    line= dict(color= 'green'),
                    name='forecast'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['sales'],
                    line= dict(color= 'orange'),
                    name='sales'))
      fig.update_layout(title= 'R-S Dynamic',
                   xaxis_title='Period',
                   yaxis_title='Demand' ,template=large_rockwell_template)


      fig.show()
      
  
  
  a= [data,metrics]
  return a 



def periodic(demand, leadtime, service_level,Review_period,distribution= 'normal',mean = False, sd=False,
                       shortage_cost = False, inventory_cost = False, 
                       ordering_cost = False,initial_inventory_level = False,
                       Max=False,recalculate=False,recalculate_windows=False,plot=False):
  """[Simulating a  periodic policy, different from R,s,S because here order is made at the ordering time without a min(reordering quantity)
     the Max is dynamically calculated based on a forecast vector. .

     The Function takes a demand vector, mean of demand ,sd,lead time and requested service level to simulate an inventory system, 
     orders are lost if inventory level is less than requested demand, also ordering is made at
     day t+1, metrics like item fill rate and cycle service level are calculated. 
     the min is calculated based on a normal distribution or a poisson distribution, also min can be set manually.
     Max - inventory position is ordered  at the period of review ]

   Args:
      demand ([float]): [demand in N time periods]
      leadtime ([float]): [lead time from order to arrival]
      service_level ([float]): [cycle service level requested]
      Review_period ([float]):the number of periods where every order is allowed to be made.
      distribution ([str]) :distribution  to calculate safety stock based on demand distribution, current choices are 'normal' or 'poisson'
      mean ([float]): [average demand in N time periods.]
      sd ([float]): [standard deviation in N time periods.]
      shortage_cost (bool, optional): [shortage cost per unit of sales lost]. Defaults to False.
      inventory_cost (bool, optional): [inventory cost per unit.]. Defaults to False.
      ordering_cost (bool, optional): [ordering cost for every time an order is made.]. Defaults to False.
      initial_inventory_level ([float]): Default is False and simulation starts with min as inventory level
      Max  ([float]):Default is False and max is calculated as a ratio to min,otherwise set manually.
      recalculate  ([float]): the mean and sd is recalculated every X periods from first period to x,default is FALSE .
      recalculate_windows  ([float]): the min  mean and sd windows to recalculate , for exammple if it is set to 4 mean and sd
                           is calculated from t to t-4,,default is FALSE .
      plot  (bool, optional): Default is False, if true a plot is generated
   Returns:
      [list]: [a list of two, the simulation and the metrics.]

   Examples:
      [periodic(demand=numpy.random.uniform(2,20,200).round(),leadtime=5,service_level=0.95,Review_period=10,plot=True)]

  """    

  L = leadtime
  N = len(demand)
  
  if( type(recalculate) != bool):
      mean = numpy.zeros(N+1)
      sd= numpy.zeros(N+1)
      minn= numpy.zeros(N+1)
      Max= numpy.zeros(N+1)
      for i in range(len(mean)):
          mean[i]= numpy.mean(demand[0:i])if (numpy.isnan(numpy.mean(demand[0:i]))==False) else demand[0]
          sd[i]= numpy.std(demand[0:i])if (numpy.isnan(numpy.std(demand[0:i]))==False) else 0
          if(distribution== 'normal'):
              minn[i]= round((mean[i] *(leadtime+Review_period))+ ((sd[i]*numpy.sqrt(leadtime+Review_period))* scipy.stats.norm.ppf(service_level)))
          else :
              minn[i]= scipy.stats.poisson.ppf(service_level,mean[i]*(leadtime+Review_period))
         
      if(type(recalculate_windows) != bool):
          mean[0]= demand[0]
          sd[0]= numpy.std(demand)
          for i in range(1,len(mean)):
              mean[i]= (numpy.mean(demand[max((i- recalculate_windows),0):(i-1)])if 
                        (len(demand[max((i- recalculate_windows),0):(i-1)])>0) else demand[0]) 
              sd[i]= (numpy.std(demand[max((i- recalculate_windows),0):(i-1)])if 
                        (len(demand[max((i- recalculate_windows),0):(i-1)])>0) else sd[0]) 
              if(distribution== 'normal'):
                  minn[i]= round((mean[i] *(leadtime+Review_period))+ ((sd[i]*numpy.sqrt(leadtime+Review_period))* scipy.stats.norm.ppf(service_level)))
              else :
                  minn[i]= scipy.stats.poisson.ppf(service_level,mean[i]*(leadtime+Review_period))
      Max[0]= minn[1]  
      for i in range(1,len(Max)):
          Max[i]= Max[i-1] if((i % recalculate) != 0) else minn[i]
  
  def classfication(demand):
      def intervals(x):
          y=numpy.zeros(len(x)+2)
          k=0
          counter=0
          for tmp in range(len(x)):
              if (x[tmp]==0):
                  counter= counter +1
              else :
                  k=k+1
                  y[k]= counter
                  counter =1
          y= y[y>0]
          y[numpy.isnan(y)]=1
          return y
      def demand1(x):
          y= x[x!=0]
          return y
      D = demand1(demand)
      ADI = numpy.mean(intervals(demand))
      CV2 = (numpy.std(D)/numpy.mean(D))**2
      
      if (ADI > 4/3):
          if (CV2 >0.5):
              type1= 'Lumpy'
          else :
              type1= 'Intermittent'
      else  :
          if(CV2 >0.5):
              type1= 'Erratic'
          else:
              type1= 'Smooth'
               
      return type1
  class1= classfication(demand)
   
  if((type(mean)== bool) & (type(recalculate)==bool)):
    mean= numpy.mean(demand)
  elif ((type(mean)!= bool) & (type(recalculate)==bool)):
    mean=mean
  
  
  if((type(sd)== bool) & (type(recalculate)==bool)):
    sd= numpy.std(demand)
  elif ((type(sd)!= bool) & (type(recalculate)==bool)):
    sd =sd
  
  
  if ((type(Max) != bool) & (type(recalculate) == bool)):
    
    Max= Max
    Max =  numpy.repeat(Max,N+1)
    
  elif((distribution== 'normal')& (type(recalculate)== bool)):
    
    Max = round((mean *(leadtime+Review_period))+ ((sd*numpy.sqrt(leadtime+Review_period))* scipy.stats.norm.ppf(service_level)))
    Max =  numpy.repeat(Max,N+1)
    
  elif ((distribution== 'poisson') & (type(recalculate)== bool)):
    
    Max = scipy.stats.poisson.ppf(service_level,mean[i]*(leadtime+Review_period))
    Max =  numpy.repeat(Max,N+1)
    
  saftey_stock= Max- (mean *(leadtime+Review_period))          

  

  order = numpy.zeros(N+1)
  I = numpy.zeros(N+1)
  IP = numpy.zeros(N+1)
  sales = numpy.zeros(N+1)
  recieved = numpy.zeros(N+1)
  order[0]=0
  demand= numpy.append(numpy.array(0),demand)

  if(initial_inventory_level==False):
    IP[0] = I[0] =  Max[0]
  else :
    IP[0] = I[0] =  initial_inventory_level
  
    
  def numpy_rep(x, reps=1, each=False, length=0):
    """ implementation of functionality of rep() and rep_len() from R

    Attributes:
        x: numpy array, which will be flattened
        reps: int, number of times x should be repeated
        each: logical; should each element be repeated reps times before the next
        length: int, length desired; if >0, overrides reps argument
    """
    if length > 0:
        reps = numpy.int(numpy.ceil(length / x.size))
    x = numpy.repeat(x, reps)
    if(not each):
        x = x.reshape(-1, reps).T.ravel() 
    if length > 0:
        x = x[0:length]
    return(x)
  ordering_time= numpy_rep(numpy.repeat([0,1], [Review_period-1,1]),each=False,reps=len(demand))
  ordering_time=numpy.append(numpy.array(0), ordering_time)
  
 
  for t in range(1,L+1):
    sales[t] = min (demand[t], I[t-1])
    I[t] = I[t-1] - sales[t]
    order[t] = (Max[t] - IP[t-1]) * (ordering_time[t])    
    IP[t] =  IP[t-1] + order[t] - sales[t]
    
  
  
  for t in range(L+1,N+1):
    sales[t] = min(demand[t], I[t-1] + order[t-L])
    I[t] = I[t-1] + order[t-L] - sales[t]
    order[t] = (Max[t] - IP[t-1]) * (ordering_time[t])    
    IP[t] = IP[t-1] + order[t] - sales[t]
    recieved[t]= order[t-L]
  
  
  data=pandas.DataFrame({'period':range(1,N+2),'demand':demand,'sales':sales,'inventory_level':I,
                   'inventory_position':IP,'saftey_stock': saftey_stock,'order': order,'max':Max,
                   'recieved':recieved},index= range(1,N+2))
  
  data['lost_order']= data['demand'] - data['sales']
  
  metrics= pandas.DataFrame({'shortage_cost': sum(data['lost_order'])*shortage_cost,
                       'inventory_cost': sum(data['inventory_level'])*inventory_cost,
                       'average_inventory_level': data['inventory_level'].mean(),'total_orders':len(order[order>0]),
                       'total_lost_sales': sum(data['lost_order']),
                       'ordering_cost':  len(data['order'][data['order']>0]) *ordering_cost,'average_ordering_quantity':(order[order>0]).mean(),
                       'ordering_interval': str(round(len(demand)/len(order[order>0]),2))+'_periods',
                       'Item_fill_rate': 1-(sum(data['lost_order'][data['lost_order']>0]))/sum(demand[1:(len(demand)-1)]),
                       'cycle_service_level': 1-(len(data['lost_order'][data['lost_order']>0])/(len(demand)-1)),
                       'saftey_stock':saftey_stock.mean(),'average_sales': sales.mean() },index= [0])
  metrics['average_flow_time(throughput)']= metrics['average_inventory_level']/metrics['average_sales']
  metrics['class']= class1
  
  if(plot== True):
      large_rockwell_template = dict(
       layout=plotly.graph_objects.Layout(title_font=dict(family="Rockwell", size=24))
                                      )
      fig= plotly.graph_objects.Figure()
        
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['inventory_level'],
                                                 mode='markers',marker=dict(color='green'),
                                                 name= 'inventory level'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['order'],
                    line= dict(color= 'grey'),
                    name='order'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['demand'],
                    line= dict(color= 'royalblue'),
                    name='demand'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['sales'],
                    line= dict(color= 'orange'),
                    name='sales'))
      fig.update_layout(title= 'Periodic R-S Policy',
                   xaxis_title='Period',
                   yaxis_title='Demand' ,template=large_rockwell_template)


      fig.show()
      
  
  
  a= [data,metrics]
  return a 


def possible_markdowns(begining_inventory,
                              weeks,
                              current_week,
                              inventory_at_week,
                              expected_at_season_end,plot=True):
    """[a markdown model 
  This is a markdown model proposed in
  Walker, John. "A model for determining price markdowns of seasonal merchandise." 
  Journal of Product & Brand Management (1999), the idea that it is possible for seasonal merchandise to forecast how much
  for a specific product can be left at the end of the season. based on the sales rate in the periods of the selling season.
  for example, if a seasonal shirt initial buying quantity is 500, during the the first two weeks we sold 100 and the season for this
  shirt is 6 weeks, then it is possible to forecast for a one time shot product how much is expected to be left with at the end of the 
  season (at the end of the 6 weeks), the function applies the algorithm in walker (1999), the returning value is a classification of
  the item if it is a slow moving or a regular item. also the possible markdowns that can be applied.
  (only markdowns where there is a economic viability) and this can be a dynamic markdown process where the process can be repeated
  every week, preferably when the product changes its status from Regular to slow moving. if the markdown recommendation is for example 
  0.9 then it means that the new price is 90 % of the original price. and so on for the following week, hence the dynamic process..]

   Args:
      begining_inventory ([float]): [inventory at the beginning of the season before selling.]
      weeks ([float]): [expected sellling priod for this item]
      current_week ([float]): [the end of the current week]
      inventory_at_week ([float]): [inventory at the end of the current week.]
      expected_at_season_end ([str]) : [expected inventory left for salvage or writing off at the end of the season, if the forecast is
                                                below it, then it becomes a regular item if the forecast is higher than 
                                                expected at season end then it becomes a slow moving item.]
 
     plot  (bool, optional): [Default is False, if true a plot is generated]
   Returns:
      [list]: [data frame of spoosible markdowns,reccomendation]

   Examples:
      [        
possible_markdowns(begining_inventory=1000,weeks=16,
   current_week=2,inventory_at_week=825,expected_at_season_end=150,plot=True)]

  """    
    
    
    def end_of_season_inventory(begining_inventory,
                                   weeks,
                                   current_week,
                                   inventory_at_week,
                                   expected_at_season_end):
        fc= (inventory_at_week/begining_inventory)**(1/current_week)
        expected_inventory=   inventory_at_week * fc ** (weeks - current_week)
        verdict= 'Regular' if (expected_inventory < expected_at_season_end) else 'Slow moving'
        return [expected_inventory,verdict]
    ending_inventory=end_of_season_inventory(begining_inventory,
                                                     weeks,
                                                     current_week,
                                                     inventory_at_week,
                                                     expected_at_season_end)[0]
    status=end_of_season_inventory(begining_inventory,
                                weeks,
                                current_week,
                                inventory_at_week,
                                expected_at_season_end)[1]
    def markdown_critical(end_of_period_inventory_ratio,week,periods,percentage_reduction):
       i_ratio=end_of_period_inventory_ratio
       reduction=percentage_reduction
       lower1= 1- (i_ratio)**(1/week)
       higher1= 1-(1- ((1-(i_ratio)**((periods-week)/week))/reduction))**(1/(periods-week))
       return(higher1/lower1)
    markdown= numpy.linspace(0,1,101)
    margin=[]
    for i in range(len(markdown)):
        a= markdown_critical(inventory_at_week/begining_inventory,current_week,weeks,markdown[i])
        margin.append(a)
        
    data1= pandas.DataFrame({'markdown': markdown,
                                              'margin_sales_increase': margin,
                                              'product current status':status,
                                              'expected_inventory_at_end_of_season':ending_inventory})
    
    data= data1[data1.margin_sales_increase >0].reset_index()
    if(plot== True):
         large_rockwell_template = dict(
         layout=plotly.graph_objects.Layout(title_font=dict(family="Rockwell", size=24))
                                      )
         fig= plotly.graph_objects.Figure()
        
         fig.add_trace(plotly.graph_objects.Bar(x=data['markdown'], y= data['margin_sales_increase']
                                                ))
     
         fig.update_layout(title= 'possible markdowns at current week',
                   xaxis_title='Markdowns',
                   yaxis_title='Expected increase  in sales next week' ,template=large_rockwell_template)


         fig.show()
         
    if(status== 'Slow moving'):
          a= """it is recommended to apply markdowns as the item is forecasted to be a slow moving item with excess inventory at end of season,
      the markdown reprsents the new selling price percentage from full original price
      and margin sales increase column is the expected increase in sales to achieve  that is economicaly viable the following week"""
    else :
          a= ' it is not recommended to do markdown at this week as the item is forecasted to have a regular selling pattern '

    return [data1,a]


def R_s_S(demand, leadtime, service_level,Review_period,Min_to_max=0.6,distribution= 'normal',mean = False, sd=False,
                       shortage_cost = False, inventory_cost = False, 
                       ordering_cost = False,initial_inventory_level = False,
                       Min= False,Max=False,recalculate=False,recalculate_windows=False,plot=False):
  """[Simulating a Min Max periodic policy or also called R,s,S policy, R represents the ordering/review period, 
      the Max is dynamically calculated based on a forecast vector. .
  
     The Function takes a demand vector, mean of demand ,sd,lead time and requested service level to simulate an inventory system, 
     orders are lost if inventory level is less than requested demand, also ordering is made at
     day t+1, metrics like item fill rate and cycle service level are calculated. 
     the min is calculated based on a normal distribution or a poisson distribution, also min can be set manually.
     Max - inventory position is ordered whenever inventory position reaches min at the priod of review   ]

   Args:
      demand ([float]): [demand in N time periods]
      leadtime ([float]): [lead time from order to arrival]
      service_level ([float]): [cycle service level requested]
      Review_period ([float]):the number of periods where every order is allowed to be made.
      Min_to_max ([float]): the ratio of min to max calculation , default 0.6 but can be changed manually.
      distribution ([str]) :distribution  to calculate safety stock based on demand distribution, current choices are 'normal' or 'poisson'
      mean ([float]): [average demand in N time periods.]
      sd ([float]): [standard deviation in N time periods.]
      shortage_cost (bool, optional): [shortage cost per unit of sales lost]. Defaults to False.
      inventory_cost (bool, optional): [inventory cost per unit.]. Defaults to False.
      ordering_cost (bool, optional): [ordering cost for every time an order is made.]. Defaults to False.
      initial_inventory_level ([float]): Default is False and simulation starts with min as inventory level
      min  ([float]):Default is False and min is calculated based on mean,demand and lead time unless set manually
      Max  ([float]):Default is False and max is calculated as a ratio to min,otherwise set manually.
      recalculate  ([float]): the mean and sd is recalculated every X periods from first period to x,default is FALSE .
      recalculate_windows  ([float]): the min  mean and sd windows to recalculate , for exammple if it is set to 4 mean and sd
                           is calculated from t to t-4,,default is FALSE .
      plot  (bool, optional): Default is False, if true a plot is generated
   Returns:
      [list]: [a list of two, the simulation and the metrics.]

   Examples:
      [R_s_S(demand=numpy.random.uniform(2,20,200).round(),Min_to_max=0.5,leadtime=5,service_level=0.95,Review_period=10,plot=True)]

  """    

  L = leadtime
  N = len(demand)
  
  if( type(recalculate) != bool):
      mean = numpy.zeros(N+1)
      sd= numpy.zeros(N+1)
      minn= numpy.zeros(N+1)
      Max= numpy.zeros(N+1)
      for i in range(len(mean)):
          mean[i]= numpy.mean(demand[0:i])if (numpy.isnan(numpy.mean(demand[0:i]))==False) else demand[0]
          sd[i]= numpy.std(demand[0:i])if (numpy.isnan(numpy.std(demand[0:i]))==False) else 0
          if(distribution== 'normal'):
              minn[i]= round((mean[i] *(leadtime+Review_period))+ ((sd[i]*numpy.sqrt(leadtime+Review_period))* scipy.stats.norm.ppf(service_level)))
          else :
              minn[i]= scipy.stats.poisson.ppf(service_level,mean[i]*(leadtime+Review_period))
         
      if(type(recalculate_windows) != bool):
          mean[0]= demand[0]
          sd[0]= numpy.std(demand)
          for i in range(1,len(mean)):
              mean[i]= (numpy.mean(demand[max((i- recalculate_windows),0):(i-1)])if 
                        (len(demand[max((i- recalculate_windows),0):(i-1)])>0) else demand[0]) 
              sd[i]= (numpy.std(demand[max((i- recalculate_windows),0):(i-1)])if 
                        (len(demand[max((i- recalculate_windows),0):(i-1)])>0) else sd[0]) 
              if(distribution== 'normal'):
                  minn[i]= round((mean[i] *(leadtime+Review_period))+ ((sd[i]*numpy.sqrt(leadtime+Review_period))* scipy.stats.norm.ppf(service_level)))
              else :
                  minn[i]= scipy.stats.poisson.ppf(service_level,mean[i]*(leadtime+Review_period))
      Max[0]= minn[1]  
      for i in range(1,len(Max)):
          Max[i]= Max[i-1] if((i % recalculate) != 0) else minn[i]
  
  def classfication(demand):
      def intervals(x):
          y=numpy.zeros(len(x)+2)
          k=0
          counter=0
          for tmp in range(len(x)):
              if (x[tmp]==0):
                  counter= counter +1
              else :
                  k=k+1
                  y[k]= counter
                  counter =1
          y= y[y>0]
          y[numpy.isnan(y)]=1
          return y
      def demand1(x):
          y= x[x!=0]
          return y
      D = demand1(demand)
      ADI = numpy.mean(intervals(demand))
      CV2 = (numpy.std(D)/numpy.mean(D))**2
      
      if (ADI > 4/3):
          if (CV2 >0.5):
              type1= 'Lumpy'
          else :
              type1= 'Intermittent'
      else  :
          if(CV2 >0.5):
              type1= 'Erratic'
          else:
              type1= 'Smooth'
               
      return type1
  class1= classfication(demand)
   
  if((type(mean)== bool) & (type(recalculate)==bool)):
    mean= numpy.mean(demand)
  elif ((type(mean)!= bool) & (type(recalculate)==bool)):
    mean=mean
  
  
  if((type(sd)== bool) & (type(recalculate)==bool)):
    sd= numpy.std(demand)
  elif ((type(sd)!= bool) & (type(recalculate)==bool)):
    sd =sd
  
  
  if ((type(Max) != bool) & (type(recalculate) == bool)):
    
    Max= Max
    Max =  numpy.repeat(Max,N+1)
    
  elif((distribution== 'normal')& (type(recalculate)== bool)):
    
    Max = round((mean *(leadtime+Review_period))+ ((sd*numpy.sqrt(leadtime+Review_period))* scipy.stats.norm.ppf(service_level)))
    Max =  numpy.repeat(Max,N+1)
    
  elif ((distribution== 'poisson') & (type(recalculate)== bool)):
    
    Max = scipy.stats.poisson.ppf(service_level,mean[i]*(leadtime+Review_period))
    Max =  numpy.repeat(Max,N+1)
    
  saftey_stock= Max- (mean *(leadtime+Review_period))          

  if(type(Min)==bool):
    Min= numpy.round(Min_to_max *Max)
  else:
    Min=numpy.repeat(Min,len(Max))
  


  order = numpy.zeros(N+1)
  I = numpy.zeros(N+1)
  IP = numpy.zeros(N+1)
  sales = numpy.zeros(N+1)
  recieved = numpy.zeros(N+1)
  order[0]=0
  demand= numpy.append(numpy.array(0),demand)

  if(initial_inventory_level==False):
    IP[0] = I[0] =  Max[0]
  else :
    IP[0] = I[0] =  initial_inventory_level
  
    
  def numpy_rep(x, reps=1, each=False, length=0):
    """ implementation of functionality of rep() and rep_len() from R

    Attributes:
        x: numpy array, which will be flattened
        reps: int, number of times x should be repeated
        each: logical; should each element be repeated reps times before the next
        length: int, length desired; if >0, overrides reps argument
    """
    if length > 0:
        reps = numpy.int(numpy.ceil(length / x.size))
    x = numpy.repeat(x, reps)
    if(not each):
        x = x.reshape(-1, reps).T.ravel() 
    if length > 0:
        x = x[0:length]
    return(x)
  ordering_time= numpy_rep(numpy.repeat([0,1], [Review_period-1,1]),each=False,reps=len(demand))
  ordering_time=numpy.append(numpy.array(0), ordering_time)
  
  def hibrid_fun(t):
      
      if((IP[t-1] <= Min[t])):
                 a= (Max[t] - IP[t-1]) * (IP[t-1] <= Min[t])
      if not(IP[t-1] <= Min[t]) :
                  a=(Max[t] - IP[t-1]) * (ordering_time[t])           
      return a
  for t in range(1,L+1):
    sales[t] = min (demand[t], I[t-1])
    I[t] = I[t-1] - sales[t]
    order[t] = (Max[t] - IP[t-1]) * (IP[t-1] <= Min[t])* ordering_time[t]
    IP[t] =  IP[t-1] + order[t] - sales[t]
    
  
  
  for t in range(L+1,N+1):
    sales[t] = min(demand[t], I[t-1] + order[t-L])
    I[t] = I[t-1] + order[t-L] - sales[t]
    order[t] = (Max[t] - IP[t-1]) * (IP[t-1] <= Min[t])* ordering_time[t]
    IP[t] = IP[t-1] + order[t] - sales[t]
    recieved[t]= order[t-L]
  
  
  data=pandas.DataFrame({'period':range(1,N+2),'demand':demand,'sales':sales,'inventory_level':I,
                   'inventory_position':IP,'saftey_stock': saftey_stock,'min':Min,'order': order,'max':Max,
                   'recieved':recieved},index= range(1,N+2))
  
  data['lost_order']= data['demand'] - data['sales']
  
  metrics= pandas.DataFrame({'shortage_cost': sum(data['lost_order'])*shortage_cost,
                       'inventory_cost': sum(data['inventory_level'])*inventory_cost,
                       'average_inventory_level': data['inventory_level'].mean(),'total_orders':len(order[order>0]),
                       'total_lost_sales': sum(data['lost_order']),
                       'ordering_cost':  len(data['order'][data['order']>0]) *ordering_cost,'average_ordering_quantity':(order[order>0]).mean(),
                       'ordering_interval': str(round(len(demand)/len(order[order>0]),2))+'_periods',
                       'Item_fill_rate': 1-(sum(data['lost_order'][data['lost_order']>0]))/sum(demand[1:(len(demand)-1)]),
                       'cycle_service_level': 1-(len(data['lost_order'][data['lost_order']>0])/(len(demand)-1)),
                       'saftey_stock':saftey_stock.mean(),'average_sales': sales.mean() },index= [0])
  metrics['average_flow_time(throughput)']= metrics['average_inventory_level']/metrics['average_sales']
  metrics['cllass']= class1
  
  if(plot== True):
      large_rockwell_template = dict(
       layout=plotly.graph_objects.Layout(title_font=dict(family="Rockwell", size=24))
                                      )
      fig= plotly.graph_objects.Figure()
        
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['inventory_level'],
                                                 mode='markers',marker=dict(color='green'),
                                                 name= 'inventory level'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['order'],
                    line= dict(color= 'grey'),
                    name='order'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['demand'],
                    line= dict(color= 'royalblue'),
                    name='demand'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['sales'],
                    line= dict(color= 'orange'),
                    name='sales'))
      fig.update_layout(title= 'Min Max Policy',
                   xaxis_title='Period',
                   yaxis_title='Demand' ,template=large_rockwell_template)


      fig.show()
      
  
  
  a= [data,metrics]
  return a 


def base_stock_policy(demand, leadtime, service_level, Base = False, mean=False, sd=False,
                            ordering_delay = False, shortage_cost = False, inventory_cost = False, 
                            ordering_cost = False,distribution= 'normal',
                            recalculate=False,recalculate_windows=False,plot=False):
  """[Simulating a  base stock policy 
    where order is made every period equal to the demand sold and having a Base stock enough for leadtime and saftey stock.
   The Function takes a demand vector, mean of demand ,sd,lead time and requested service level to simulate an inventory system, 
   orders are lost if inventory level is less than requested demand, also ordering is made at
   day t+1, metrics like item fill rate and cycle service level are calculated. 
   the min is calculated based on a normal distribution or a poisson distribution, also min can be set manually.
   demand and base adjustment (if any) is ordered every period.]

   Args:
      demand ([float]): [demand in N time periods]
      leadtime ([float]): [lead time from order to arrival]
      service_level ([float]): [cycle service level requested]
      Base(bool, optional): Default is False and calculated based on mean and sd(normal) or rate of demand (poisson),otherwise set manually.
      mean ([float]): [average demand in N time periods.]
      sd ([float]): [standard deviation in N time periods.].
      oredering_delay(bool, optional): Default is FALSE,if TRUE, orders are delayed one period.
      shortage_cost (bool, optional): [shortage cost per unit of sales lost]. Defaults to False.
      inventory_cost (bool, optional): [inventory cost per unit.]. Defaults to False.
      ordering_cost (bool, optional): [ordering cost for every time an order is made.]. Defaults to False.
      distribution ([str]) :distribution  to calculate safety stock based on demand distribution, current choices are 'normal' or 'poisson'
      recalculate  ([float]): the mean and sd is recalculated every X periods from first period to x,default is FALSE .
      recalculate_windows  ([float]): the min  mean and sd windows to recalculate , for exammple if it is set to 4 mean and sd
                           is calculated from t to t-4,,default is FALSE .
      plot  (bool, optional): Default is False, if true a plot is generated
   Returns:
      [list]: [a list of two, the simulation and the metrics.]

   Examples:
      [base_stock_policy(demand=numpy.random.uniform(2,20,200).round(),leadtime=5,service_level=0.95,plot=True)]

  """    

  L = leadtime
  N = len(demand)
  
  if( type(recalculate) != bool):
      mean = numpy.zeros(N+1)
      sd= numpy.zeros(N+1)
      minn= numpy.zeros(N+1)
      Min= numpy.zeros(N+1)
      for i in range(len(mean)):
          mean[i]= numpy.mean(demand[0:i])if (numpy.isnan(numpy.mean(demand[0:i]))==False) else demand[0]
          sd[i]= numpy.std(demand[0:i])if (numpy.isnan(numpy.std(demand[0:i]))==False) else 0
          if(distribution== 'normal'):
              minn[i]= round((mean[i] *leadtime)+ ((sd[i]*numpy.sqrt(leadtime))* scipy.stats.norm.ppf(service_level)))
          else :
              minn[i]= scipy.stats.poisson.ppf(service_level,mean[i]*leadtime)
         
      if(type(recalculate_windows) != bool):
          mean[0]= demand[0]
          sd[0]= numpy.std(demand)
          for i in range(1,len(mean)):
              mean[i]= (numpy.mean(demand[max((i- recalculate_windows),0):(i-1)])if 
                        (len(demand[max((i- recalculate_windows),0):(i-1)])>0) else demand[0]) 
              sd[i]= (numpy.std(demand[max((i- recalculate_windows),0):(i-1)])if 
                        (len(demand[max((i- recalculate_windows),0):(i-1)])>0) else sd[0]) 
              if(distribution== 'normal'):
                  minn[i]= round((mean[i] *leadtime)+ ((sd[i]*numpy.sqrt(leadtime))* scipy.stats.norm.ppf(service_level)))
              else :
                  minn[i]= scipy.stats.poisson.ppf(service_level,mean[i]*leadtime)  
      Min[0]= minn[1] 
      for i in range(1,len(Base)):
          Base[i]= Base[i-1] if((i % recalculate) != 0) else minn[i]
  
  def classfication(demand):
      def intervals(x):
          y=numpy.zeros(len(x)+2)
          k=0
          counter=0
          for tmp in range(len(x)):
              if (x[tmp]==0):
                  counter= counter +1
              else :
                  k=k+1
                  y[k]= counter
                  counter =1
          y= y[y>0]
          y[numpy.isnan(y)]=1
          return y
      def demand1(x):
          y= x[x!=0]
          return y
      D = demand1(demand)
      ADI = numpy.mean(intervals(demand))
      CV2 = (numpy.std(D)/numpy.mean(D))**2
      
      if (ADI > 4/3):
          if (CV2 >0.5):
              type1= 'Lumpy'
          else :
              type1= 'Intermittent'
      else  :
          if(CV2 >0.5):
              type1= 'Erratic'
          else:
              type1= 'Smooth'
               
      return type1
  class1= classfication(demand)
   
  if((type(mean)== bool) & (type(recalculate)==bool)):
    mean= numpy.mean(demand)
  elif ((type(mean)!= bool) & (type(recalculate)==bool)):
    mean=mean
  
  
  if((type(sd)== bool) & (type(recalculate)==bool)):
    sd= numpy.std(demand)
  elif ((type(sd)!= bool) & (type(recalculate)== bool)):
    sd =sd
  
  
  
  if ((type(Base) != bool) & (type(recalculate) == bool)):
    
    Base= Base
    Base =  numpy.repeat(Base,N+1)
    
  elif((distribution== 'normal')& (type(recalculate)== bool)):
    
    Base = round((mean *leadtime)+ ((sd*numpy.sqrt(leadtime))* scipy.stats.norm.ppf(service_level)))
    Base =  numpy.repeat(Base,N+1)
    
  elif ((distribution== 'poisson') & (type(recalculate)== bool)):
    
    Base = scipy.stats.poisson.ppf(service_level,mean[i]*leadtime)
    Base =  numpy.repeat(Base,N+1)
    
    
  saftey_stock= Base- (mean *leadtime)          

  

  order = numpy.zeros(N+1)
  I = numpy.zeros(N+1)
  IP = numpy.zeros(N+1)
  sales = numpy.zeros(N+1)
  recieved = numpy.zeros(N+1)
  order[0]=0
  demand= numpy.append(numpy.array(0),demand)

  IP[0] = I[0] =  Base[0]
  
 
  for t in range(1,L+1):
    sales[t] = min (demand[t], I[t-1])
    I[t] = I[t-1] - sales[t]
    order[t] = max(sales[t - ordering_delay]+ (Base[t]- Base[t-1]),0)
    IP[t] =  IP[t-1] + order[t] - sales[t]
    
  
  
  for t in range(L+1,N+1):
    sales[t] = min(demand[t], I[t-1] + order[t-L])
    I[t] = I[t-1] + order[t-L] - sales[t]
    order[t] = max(sales[t - ordering_delay]+ (Base[t]- Base[t-1]),0)
    IP[t] = IP[t-1] + order[t] - sales[t]
    recieved[t]= order[t-L]
  
  
  data=pandas.DataFrame({'period':range(1,N+2),'demand':demand,'sales':sales,'inventory_level':I,
                   'inventory_position':IP,'saftey_stock': saftey_stock,'order': order,'Base':Base,
                   'recieved':recieved},index= range(1,N+2))
  
  data['lost_order']= data['demand'] - data['sales']
  
  metrics= pandas.DataFrame({'shortage_cost': sum(data['lost_order'])*shortage_cost,
                       'inventory_cost': sum(data['inventory_level'])*inventory_cost,
                       'average_inventory_level': data['inventory_level'].mean(),'total_orders':len(order[order>0]),
                       'total_lost_sales': sum(data['lost_order']),
                       'ordering_cost':  len(data['order'][data['order']>0]) *ordering_cost,'average_ordering_quantity':(order[order>0]).mean(),
                       'ordering_interval': str(round(len(demand)/len(order[order>0]),2))+'_periods',
                       'Item_fill_rate': 1-(sum(data['lost_order'][data['lost_order']>0]))/sum(demand[1:(len(demand)-1)]),
                       'cycle_service_level': 1-(len(data['lost_order'][data['lost_order']>0])/(len(demand)-1)),
                       'saftey_stock':saftey_stock.mean(),'average_sales': sales.mean() },index= [0])
  metrics['average_flow_time(throughput)']= metrics['average_inventory_level']/metrics['average_sales']
  metrics['class']= class1
  
  if(plot== True):
      large_rockwell_template = dict(
       layout=plotly.graph_objects.Layout(title_font=dict(family="Rockwell", size=24))
                                      )
      fig= plotly.graph_objects.Figure()
        
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['inventory_level'],
                                                 mode='markers',marker=dict(color='green'),
                                                 name= 'inventory level'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['order'],
                    line= dict(color= 'grey'),
                    name='order'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['demand'],
                    line= dict(color= 'royalblue'),
                    name='demand'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['sales'],
                    line= dict(color= 'orange'),
                    name='sales'))
      fig.update_layout(title= 'Base Stock Policy',
                   xaxis_title='Period',
                   yaxis_title='Demand' ,template=large_rockwell_template)


      fig.show()
      
  
  
  a= [data,metrics]
  return a 

def sim_min_max (demand, leadtime, service_level,Max_to_min=1.3,distribution= 'normal',mean = False, sd=False,
                       shortage_cost = False, inventory_cost = False, 
                       ordering_cost = False,initial_inventory_level = False,Min=False,
                       Max=False,recalculate=False,recalculate_windows=False,plot=False):
  """[Simulating a min max policy or also called s,S policy,  .
    The Function takes a demand vector, mean of demand ,sd,lead time and requested service level to simulate an inventory system, 
    orders are lost if inventory level is less than requested demand, also ordering is made at
    day t+1, metrics like item fill rate and cycle service level are calculated. 
    the min is calculated based on a normal distribution or a poisson distribution, also min can be set manually.
    Max - inventory position is ordered whenever inventory position reaches min.]

   Args:
      demand ([float]): [demand in N time periods]
      leadtime ([float]): [lead time from order to arrival]
      service_level ([float]): [cycle service level requested]
      Max_to_min ([float]): the ratio of Max to min calculation , default 1.3 but can be changed manually.
      distribution ([str]) :distribution  to calculate safety stock based on demand distribution, current choices are 'normal' or 'poisson'
      mean ([float]): [average demand in N time periods.]
      sd ([float]): [standard deviation in N time periods.]
      shortage_cost (bool, optional): [shortage cost per unit of sales lost]. Defaults to False.
      inventory_cost (bool, optional): [inventory cost per unit.]. Defaults to False.
      ordering_cost (bool, optional): [ordering cost for every time an order is made.]. Defaults to False.
      initial_inventory_level ([float]): Default is False and simulation starts with min as inventory level
      Min  ([float]):Default is False and min is calculated based on mean,demand and lead time unless set manually
      Max  ([float]):Default is False and max is calculated as a ratio to min,otherwise set manually.
      recalculate  ([float]): the mean and sd is recalculated every X periods from first period to x,default is FALSE .
      recalculate_windows  ([float]): the min  mean and sd windows to recalculate , for exammple if it is set to 4 mean and sd
                           is calculated from t to t-4,,default is FALSE .
      plot  (bool, optional): Default is False, if true a plot is generated
   Returns:
      [list]: [a list of two, the simulation and the metrics.]

   Examples:
      [sim_min_max(demand=numpy.random.uniform(2,20,200).round(),mean=10,sd=0.2,leadtime=5,service_level=0.95,Max=90,
       shortage_cost= False,inventory_cost=False,ordering_cost=False,Min=50,plot=True)]

  """    
  
  L = leadtime
  N = len(demand) 
 
  if( type(recalculate) != bool):
      mean = numpy.zeros(N+1)
      sd= numpy.zeros(N+1)
      minn= numpy.zeros(N+1)
      Min= numpy.zeros(N+1)
      for i in range(len(mean)):
          mean[i]= numpy.mean(demand[0:i])if (numpy.isnan(numpy.mean(demand[0:i]))==False) else demand[0]
          sd[i]= numpy.std(demand[0:i])if (numpy.isnan(numpy.std(demand[0:i]))==False) else 0
          if(distribution== 'normal'):
              minn[i]= round((mean[i] *leadtime)+ ((sd[i]*numpy.sqrt(leadtime))* scipy.stats.norm.ppf(service_level)))
          else :
              minn[i]= scipy.stats.poisson.ppf(service_level,mean[i]*leadtime)
         
      if(type(recalculate_windows) != bool):
          mean[0]= demand[0]
          sd[0]= numpy.std(demand)
          for i in range(1,len(mean)):
              mean[i]= (numpy.mean(demand[max((i- recalculate_windows),0):(i-1)])if 
                        (len(demand[max((i- recalculate_windows),0):(i-1)])>0) else demand[0]) 
              sd[i]= (numpy.std(demand[max((i- recalculate_windows),0):(i-1)])if 
                        (len(demand[max((i- recalculate_windows),0):(i-1)])>0) else sd[0]) 
              if(distribution== 'normal'):
                  minn[i]= round((mean[i] *leadtime)+ ((sd[i]*numpy.sqrt(leadtime))* scipy.stats.norm.ppf(service_level)))
              else :
                  minn[i]= scipy.stats.poisson.ppf(service_level,mean[i]*leadtime)  
      Min[0]= minn[1]  
      for i in range(1,len(Min)):
          Min[i]= Min[i-1] if((i % recalculate) != 0) else minn[i]
  
  def classfication(demand):
      def intervals(x):
          y=numpy.zeros(len(x)+2)
          k=0
          counter=0
          for tmp in range(len(x)):
              if (x[tmp]==0):
                  counter= counter +1
              else :
                  k=k+1
                  y[k]= counter
                  counter =1
          y= y[y>0]
          y[numpy.isnan(y)]=1
          return y
      def demand1(x):
          y= x[x!=0]
          return y
      D = demand1(demand)
      ADI = numpy.mean(intervals(demand))
      CV2 = (numpy.std(D)/numpy.mean(D))**2
      
      if (ADI > 4/3):
          if (CV2 >0.5):
              type1= 'Lumpy'
          else :
              type1= 'Intermittent'
      else  :
          if(CV2 >0.5):
              type1= 'Erratic'
          else:
              type1= 'Smooth'
               
      return type1
  class1= classfication(demand)
   
  if((type(mean)== bool) & (type(recalculate)==bool)):
    mean= numpy.mean(demand)
  elif ((type(mean)!= bool) & (type(recalculate)==bool)):
    mean=mean
  
  
  if((type(sd)== bool) & (type(recalculate)==bool)):
    sd= numpy.std(demand)
  elif ((type(sd)!= bool) & (type(recalculate)== bool)):
    sd =sd
  
  
  if ((type(Min) != bool) & (type(recalculate) == bool)):
    
    Min= Min
    Min =  numpy.repeat(Min,N+1)
    
  elif((distribution== 'normal')& (type(recalculate)== bool)):
    
    Min = round((mean *leadtime)+ ((sd*numpy.sqrt(leadtime))* scipy.stats.norm.ppf(service_level)))
    Min =  numpy.repeat(Min,N+1)
    
  elif ((distribution== 'poisson') & (type(recalculate)== bool)):
    
    Min = scipy.stats.poisson.ppf(service_level,mean[i]*leadtime)
    Min =  numpy.repeat(Min,N+1)
    
  saftey_stock= Min- (mean *leadtime)            

  if(type(Max)== bool):
    Max= numpy.round(Max_to_min *Min)
  else:
    Max= numpy.repeat(Max,len(Min))
  


  order = numpy.zeros(N+1)
  I = numpy.zeros(N+1)
  IP = numpy.zeros(N+1)
  sales = numpy.zeros(N+1)
  recieved = numpy.zeros(N+1)
  order[0]=0
  demand= numpy.append(numpy.array(0),demand)

  if(type(initial_inventory_level)== bool):
    IP[0] = I[0] =  Max[0]
  else :
    IP[0] = I[0] =  initial_inventory_level


  
  
  for t in range(1,L+1):
    sales[t] = min (demand[t], I[t-1])
    I[t] = I[t-1] - sales[t]
    order[t] = (Max[t]- IP[t-1]) * (IP[t-1] <= Min[t])
    IP[t] =  IP[t-1] + order[t] - sales[t]
    
  
  
  for t in range(L+1,N+1):
    sales[t] = min(demand[t], I[t-1] + order[t-L])
    I[t] = I[t-1] + order[t-L] - sales[t]
    order[t] = (Max[t]- IP[t-1]) * (IP[t-1] <= Min[t])
    IP[t] = IP[t-1] + order[t] - sales[t]
    recieved[t]= order[t-L]
  
  data=pandas.DataFrame({'period':range(1,N+2),'demand':demand,'sales':sales,'inventory_level':I,
                   'inventory_position':IP,'saftey_stock': saftey_stock,'min':Min,'order': order,'max':Max,
                   'recieved':recieved},index= range(1,N+2))
  
  data['lost_order']= data['demand'] - data['sales']
  
  metrics= pandas.DataFrame({'shortage_cost': sum(data['lost_order'])*shortage_cost,
                       'inventory_cost': sum(data['inventory_level'])*inventory_cost,
                       'average_inventory_level': data['inventory_level'].mean(),'total_orders':len(order[order>0]),
                       'total_lost_sales': sum(data['lost_order']),
                       'ordering_cost':  len(data['order'][data['order']>0]) *ordering_cost,'average_ordering_quantity':(order[order>0]).mean(),
                       'ordering_interval': str(round(len(demand)/len(order[order>0]),2))+'_periods',
                       'Item_fill_rate': 1-(sum(data['lost_order'][data['lost_order']>0]))/sum(demand[1:(len(demand)-1)]),
                       'cycle_service_level': 1-(len(data['lost_order'][data['lost_order']>0])/(len(demand)-1)),
                       'saftey_stock':saftey_stock.mean(),'average_sales': sales.mean() },index= [0])
  metrics['average_flow_time(throughput)']= metrics['average_inventory_level']/metrics['average_sales']
  metrics['class']= class1
  
  if(plot== True):
      large_rockwell_template = dict(
       layout=plotly.graph_objects.Layout(title_font=dict(family="Rockwell", size=24))
                                      )
      fig= plotly.graph_objects.Figure()
        
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['inventory_level'],
                                                 mode='markers',marker=dict(color='green'),
                                                 name= 'inventory level'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['order'],
                    line= dict(color= 'grey'),
                    name='order'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['demand'],
                    line= dict(color= 'royalblue'),
                    name='demand'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['sales'],
                    line= dict(color= 'orange'),
                    name='sales'))
      fig.update_layout(title= 'Min Max Policy',
                   xaxis_title='Period',
                   yaxis_title='Demand' ,template=large_rockwell_template)


      fig.show()
      
  
  
  a= [data,metrics]
  return a 

def sim_min_max_dynamic(demand,forecast, leadtime, service_level,initial_inventory_level=False, Max_to_min=1.5,Max=False,
                               one_step_forecast=True,shortage_cost = False, 
                inventory_cost = False, ordering_cost = False,
                distribution= 'normal', error_metric= 'rmse',metric_windows= False,plot=False):
  """[sim_min_max_dynamic

    Simulating a min max policy or also called s,S policy, 
    the Max is dynamically calculated based on a forecast vector. .
    The Function takes a demand vector, FORECAST vector ,lead time and requested service level to simulate an inventory system, 
    orders are lost if inventory level is less than requested demand, also ordering is made at
    day t+1, metrics like item fill rate and cycle service level are calculated. 
    the min is calculated based on a normal distribution or a poisson distribution, also min can be set manually.
    Max - inventory position is ordered whenever inventory position reaches min.]

   Args:
      demand ([float]): [demand in N time periods]
      forecast ([float]): [the forecast vector of equal n periods to demand.]
      leadtime ([float]): [lead time from order to arrival]
      service_level ([float]): [cycle service level requested]
      initial_inventory_level ([float]): [Default is False and simulation starts with min as inventory level]
      Max_to_min ([float]): [the ratio of Max to min calculation , default 1.3 but can be changed manually.]
      Max  ([float]):[Default is False and max is calculated as a ratio to min,otherwise set manually.]
      one_step_forecast ([logical]): [Default is true where demand lead time is calcluated as(forecast at period t * leadtime)]
      shortage_cost (bool, optional): [shortage cost per unit of sales lost]. Defaults to False.
      inventory_cost (bool, optional): [inventory cost per unit.]. Defaults to False.
      ordering_cost (bool, optional): [ordering cost for every time an order is made.]. Defaults to False.
      distribution ([str]) :distribution  to calculate safety stock based on demand distribution, current choices are 'normal' or 'poisson'
      error_metric ([str]):[metric is currently 'rmse' and 'mae', this calculates the error
                            from period 1 to period t unless metric_windows is set.]
      metric_windows  ([float]): [for exammple if it is set to 4 rmse for t is calculated from t-1 to t-4,default is FALSE]
      plot  (bool, optional): [Default is False, if true a plot is generated]
   Returns:
      [list]: [a list of two, the simulation and the metrics.]

   Examples:
      [sim_min_max_dynamic(demand=numpy.random.uniform(2,20,200).round(),forecast=numpy.random.uniform(2,20,200).round(),
                 
      leadtime=5,service_level=0.95,Max=90,error_metric='rmse',metric_windows=4,distribution= 'normal',
       shortage_cost= False,inventory_cost=False,ordering_cost=False,one_step_forecast=True)]

  """    

  
###########################################################
  
  L = leadtime
  N = len(demand) 
  
  demand=numpy.append(numpy.array(0),demand)
  forecast= numpy.append(numpy.array(0),forecast)

  if (one_step_forecast== True):
       dl=forecast*leadtime
  else :
       dl= numpy.zeros(len(demand))
    
       for i in range(len(demand)):
           dl[i]= sum(forecast[i : min((i+leadtime-1),len(dl))])
  
  metric= numpy.zeros(len(demand))

  if(error_metric == 'rmse'):
      if (type(metric_windows)== bool):
          for i in range(1,len(demand)):
              metric[i]= numpy.sqrt(numpy.mean((demand[1:i-1]- forecast[1:i-1])**2))
  
      else :
          for i in range(1,len(demand)):
              metric[i]= numpy.sqrt(numpy.mean((demand[max((i- metric_windows),0):(i-1)]- forecast[max((i- metric_windows),0):(i-1)])**2))

  if(error_metric == 'mae'):
      if (type(metric_windows)== bool):
          for i in range(1,len(demand)):
              metric[i]= numpy.mean(abs((demand[1:i-1]- forecast[1:i-1])**2))
  
      else :
          for i in range(1,len(demand)):
              metric[i]= numpy.mean(abs((demand[max((i- metric_windows),0):(i-1)]- forecast[max((i- metric_windows),0):(i-1)])**2))

  metric[numpy.isnan(metric)]= numpy.round(metric[numpy.isnan(metric)==False].mean())



  def classfication(demand):
      def intervals(x):
          y=numpy.zeros(len(x)+2)
          k=0
          counter=0
          for tmp in range(len(x)):
              if (x[tmp]==0):
                  counter= counter +1
              else :
                  k=k+1
                  y[k]= counter
                  counter =1
          y= y[y>0]
          y[numpy.isnan(y)]=1
          return y
      def demand1(x):
          y= x[x!=0]
          return y
      D = demand1(demand)
      ADI = numpy.mean(intervals(demand))
      CV2 = (numpy.std(D)/numpy.mean(D))**2
      
      if (ADI > 4/3):
          if (CV2 >0.5):
              type1= 'Lumpy'
          else :
              type1= 'Intermittent'
      else  :
          if(CV2 >0.5):
              type1= 'Erratic'
          else:
              type1= 'Smooth'
               
      return type1
  class1= classfication(demand)
   
  sigmadl= metric* numpy.sqrt(leadtime)
  
  if(distribution== 'normal'):
      saftey_stock= sigmadl *  scipy.stats.norm.ppf(service_level)
  elif(distribution== 'poisson'):
      saftey_stock=  scipy.stats.poisson.ppf(service_level, demand*leadtime) - (demand*leadtime)

  Min= numpy.round(dl+saftey_stock)

  if(type(Max) ==bool):
      Max= numpy.round(Max_to_min *Min)
    
  else :
      Max= numpy.repeat(Max,N+1)
    
  
  Min[numpy.isnan(Min)]= numpy.round(Min[numpy.isnan(Min)==False].mean())
  Max[numpy.isnan(Max)]= numpy.round(Max[numpy.isnan(Max)==False].mean())
  Min[0]= Min.mean().round()
  Max[0]= Max.mean().round()

  
  
  
  
  order = numpy.zeros(N+1)
  I = numpy.zeros(N+1)
  IP = numpy.zeros(N+1)
  sales = numpy.zeros(N+1)
  recieved = numpy.zeros(N+1)
  order[0]=0


  
  if(initial_inventory_level==False):
      IP[0] = I[0] =  Max[0]
  else :
      IP[0] = I[0] =  initial_inventory_level
    
  
  
  for t in range(1,L+1):
    sales[t] = min (demand[t], I[t-1])
    I[t] = I[t-1] - sales[t]
    order[t] = (Max[t]- IP[t-1]) * (IP[t-1] <= Min[t])
    IP[t] =  IP[t-1] + order[t] - sales[t]
    
  
  
  for t in range(L+1,N+1):
    sales[t] = min(demand[t], I[t-1] + order[t-L])
    I[t] = I[t-1] + order[t-L] - sales[t]
    order[t] = (Max[t]- IP[t-1]) * (IP[t-1] <= Min[t])
    IP[t] = IP[t-1] + order[t] - sales[t]
    recieved[t]= order[t-L]
  
  data=pandas.DataFrame({'period':range(1,N+2),'demand':demand,'forecast':forecast,'sales':sales,'inventory_level':I,
                   'inventory_position':IP,'saftey_stock': saftey_stock,'min':Min,'order': order,'max':Max,
                   'recieved':recieved},index= range(1,N+2))
  
  data['lost_order']= data['demand'] - data['sales']
  error_mape=abs(demand-forecast)/abs(demand)
  error_mape= error_mape[numpy.isnan(error_mape)==False]
  metrics= pandas.DataFrame({'shortage_cost': sum(data['lost_order'])*shortage_cost,
                       'inventory_cost': sum(data['inventory_level'])*inventory_cost,
                       'average_inventory_level': data['inventory_level'].mean(),'total_orders':len(order[order>0]),
                       'total_lost_sales': sum(data['lost_order']),
                       'ordering_cost':  len(data['order'][data['order']>0]) *ordering_cost,'average_ordering_quantity':(order[order>0]).mean(),
                       'ordering_interval': str(round(len(demand)/len(order[order>0]),2))+'_periods',
                       'Item_fill_rate': 1-(sum(data['lost_order'][data['lost_order']>0]))/sum(demand[1:(len(demand)-1)]),
                       'cycle_service_level': 1-(len(data['lost_order'][data['lost_order']>0])/(len(demand)-1)),
                       'saftey_stock':saftey_stock.mean(),'average_sales': sales.mean() },index= [0])
  metrics['average_flow_time(throughput)']= metrics['average_inventory_level']/metrics['average_sales']
  metrics['class']= class1
  metrics['rmse']= numpy.sqrt(numpy.mean((demand-forecast)**2))
  metrics['mae']= numpy.mean(abs(demand-forecast))
  metrics['me']= numpy.mean(demand-forecast)
  metrics['mape']= numpy.mean(error_mape *100)


  
  if(plot== True):
      large_rockwell_template = dict(
       layout=plotly.graph_objects.Layout(title_font=dict(family="Rockwell", size=24))
                                      )
      fig= plotly.graph_objects.Figure()
        
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['inventory_level'],
                                                 mode='markers',marker=dict(color='green'),
                                                 name= 'inventory level'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['order'],
                    line= dict(color= 'grey'),
                    name='order'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['demand'],
                    line= dict(color= 'royalblue'),
                    name='demand'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['forecast'],
                    line= dict(color= 'green'),
                    name='forecast'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['sales'],
                    line= dict(color= 'orange'),
                    name='sales'))
      fig.update_layout(title= 'Min Max Policy Dynamic',
                   xaxis_title='Period',
                   yaxis_title='Demand' ,template=large_rockwell_template)


      fig.show()
      
  
  
  a= [data,metrics]
  return a 

def sim_min_Q_dynamic(demand,forecast, leadtime, service_level,Quantity,initial_inventory_level=False,
                               one_step_forecast=True,shortage_cost = False, 
                inventory_cost = False, ordering_cost = False,
                distribution= 'normal', error_metric= 'rmse',metric_windows= False,plot=False):
  """[Simulating a Min,Q policy or also called S,Q policy,

    
   the min is dynamically calculated based on a forecast vector. .
   The Function takes a demand vector, forecast vector ,lead time and requested service level to simulate an inventory system, 
   orders are lost if inventory level is less than requested demand, also ordering is made at
   day t+1, metrics like item fill rate and cycle service level are calculated. 
   the min is calculated based on a normal distribution or a poisson distribution, also min can be set manually.
   Q  (fixed quantity) is ordered whenever inventory position reaches min.]

   Args:
      demand ([float]): [demand in N time periods]
      forecast ([float]): [the forecast vector of equal n periods to demand.]
      leadtime ([float]): [lead time from order to arrival]
      service_level ([float]): [cycle service level requested]
      Quantity ([float]): [fixed order quantity]
      initial_inventory_level ([float]): [Default is False and simulation starts with min as inventory level.]
      one_step_forecast ([logical]): [Default is true where demand lead time is calcluated as(forecast at period t * leadtime)]
      shortage_cost (bool, optional): [shortage cost per unit of sales lost]. Defaults to False.
      inventory_cost (bool, optional): [inventory cost per unit.]. Defaults to False.
      ordering_cost (bool, optional): [ordering cost for every time an order is made.]. Defaults to False.
      distribution ([str]) :[distribution  to calculate safety stock based on demand distribution, 
                             current choices are 'normal' or 'poisson']
      error_metric ([str]):[metric is currently 'rmse' and 'mae', this calculates the error
                            from period 1 to period t unless metric_windows is set.]
      metric_windows  ([float]): [for exammple if it is set to 4 rmse for t is calculated from t-1 to t-4,default is FALSE]
      plot  (bool, optional): Default is False, if true a plot is generated
   Returns:
      [list]: [a list of two, the simulation and the metrics.]

   Examples:
      [sim_min_Q_dynamic(demand=numpy.random.uniform(2,20,200).round(),forecast=numpy.random.uniform(2,20,200).round(),
              
      leadtime=5,service_level=0.95,error_metric='rmse',metric_windows=4,distribution= 'normal',Quantity=80,
       shortage_cost= False,inventory_cost=False,ordering_cost=False,one_step_forecast=True,plot=True)]

  """    

  
###########################################################
  
  L = leadtime
  N = len(demand) 
  
  demand=numpy.append(numpy.array(0),demand)
  forecast= numpy.append(numpy.array(0),forecast)

  if (one_step_forecast== True):
       dl=forecast*leadtime
  else :
       dl= numpy.zeros(len(demand))
    
       for i in range(len(demand)):
           dl[i]= sum(forecast[i : min((i+leadtime-1),len(dl))])
  
  metric= numpy.zeros(len(demand))

  if(error_metric == 'rmse'):
      if (type(metric_windows)== bool):
          for i in range(1,len(demand)):
              metric[i]= numpy.sqrt(numpy.mean((demand[1:i-1]- forecast[1:i-1])**2))
  
      else :
          for i in range(1,len(demand)):
              metric[i]= numpy.sqrt(numpy.mean((demand[max((i- metric_windows),0):(i-1)]- forecast[max((i- metric_windows),0):(i-1)])**2))

  if(error_metric == 'mae'):
      if (type(metric_windows)== bool):
          for i in range(1,len(demand)):
              metric[i]= numpy.mean(abs((demand[1:i-1]- forecast[1:i-1])**2))
  
      else :
          for i in range(1,len(demand)):
              metric[i]= numpy.mean(abs((demand[max((i- metric_windows),0):(i-1)]- forecast[max((i- metric_windows),0):(i-1)])**2))

  metric[numpy.isnan(metric)]= numpy.round(metric[numpy.isnan(metric)==False].mean())



  def classfication(demand):
      def intervals(x):
          y=numpy.zeros(len(x)+2)
          k=0
          counter=0
          for tmp in range(len(x)):
              if (x[tmp]==0):
                  counter= counter +1
              else :
                  k=k+1
                  y[k]= counter
                  counter =1
          y= y[y>0]
          y[numpy.isnan(y)]=1
          return y
      def demand1(x):
          y= x[x!=0]
          return y
      D = demand1(demand)
      ADI = numpy.mean(intervals(demand))
      CV2 = (numpy.std(D)/numpy.mean(D))**2
      
      if (ADI > 4/3):
          if (CV2 >0.5):
              type1= 'Lumpy'
          else :
              type1= 'Intermittent'
      else  :
          if(CV2 >0.5):
              type1= 'Erratic'
          else:
              type1= 'Smooth'
               
      return type1
  class1= classfication(demand)
   
  sigmadl= metric* numpy.sqrt(leadtime)
  
  if(distribution== 'normal'):
      saftey_stock= sigmadl *  scipy.stats.norm.ppf(service_level)
  elif(distribution== 'poisson'):
      saftey_stock=  scipy.stats.poisson.ppf(service_level, demand*leadtime) - (demand*leadtime)

  Min= numpy.round(dl+saftey_stock)
    
  
  Min[numpy.isnan(Min)]= numpy.round(Min[numpy.isnan(Min)==False].mean())
  Min[0]= Min.mean().round()

  
  
  
  
  order = numpy.zeros(N+1)
  I = numpy.zeros(N+1)
  IP = numpy.zeros(N+1)
  sales = numpy.zeros(N+1)
  recieved = numpy.zeros(N+1)
  order[0]=0


  
  if(initial_inventory_level==False):
      IP[0] = I[0] =  Min[0]
  else :
      IP[0] = I[0] =  initial_inventory_level
    
  
  
  for t in range(1,L+1):
    sales[t] = min (demand[t], I[t-1])
    I[t] = I[t-1] - sales[t]
    order[t] = Quantity * (IP[t-1] <= Min[t])
    IP[t] =  IP[t-1] + order[t] - sales[t]
    
  
  
  for t in range(L+1,N+1):
    sales[t] = min(demand[t], I[t-1] + order[t-L])
    I[t] = I[t-1] + order[t-L] - sales[t]
    order[t] = Quantity * (IP[t-1] <= Min[t])
    IP[t] = IP[t-1] + order[t] - sales[t]
    recieved[t]= order[t-L]
  
  data=pandas.DataFrame({'period':range(1,N+2),'demand':demand,'forecast':forecast,'sales':sales,'inventory_level':I,
                   'inventory_position':IP,'saftey_stock': saftey_stock,'min':Min,'order': order,
                   'recieved':recieved},index= range(1,N+2))
  
  data['lost_order']= data['demand'] - data['sales']
  error_mape=abs(demand-forecast)/abs(demand)
  error_mape= error_mape[numpy.isnan(error_mape)==False]
  metrics= pandas.DataFrame({'shortage_cost': sum(data['lost_order'])*shortage_cost,
                       'inventory_cost': sum(data['inventory_level'])*inventory_cost,
                       'average_inventory_level': data['inventory_level'].mean(),'total_orders':len(order[order>0]),
                       'total_lost_sales': sum(data['lost_order']),
                       'ordering_cost':  len(data['order'][data['order']>0]) *ordering_cost,'average_ordering_quantity':(order[order>0]).mean(),
                       'ordering_interval': str(round(len(demand)/len(order[order>0]),2))+'_periods',
                       'Item_fill_rate': 1-(sum(data['lost_order'][data['lost_order']>0]))/sum(demand[1:(len(demand)-1)]),
                       'cycle_service_level': 1-(len(data['lost_order'][data['lost_order']>0])/(len(demand)-1)),
                       'saftey_stock':saftey_stock.mean(),'average_sales': sales.mean() },index= [0])
  metrics['average_flow_time(throughput)']= metrics['average_inventory_level']/metrics['average_sales']
  metrics['class']= class1
  metrics['rmse']= numpy.sqrt(numpy.mean((demand-forecast)**2))
  metrics['mae']= numpy.mean(abs(demand-forecast))
  metrics['me']= numpy.mean(demand-forecast)
  metrics['mape']= numpy.mean(error_mape *100)


  
  if(plot== True):
      large_rockwell_template = dict(
       layout=plotly.graph_objects.Layout(title_font=dict(family="Rockwell", size=24))
                                      )
      fig= plotly.graph_objects.Figure()
        
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['inventory_level'],
                                                 mode='markers',marker=dict(color='green'),
                                                 name= 'inventory level'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['order'],
                    line= dict(color= 'grey'),
                    name='order'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['demand'],
                    line= dict(color= 'royalblue'),
                    name='demand'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['forecast'],
                    line= dict(color= 'green'),
                    name='forecast'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['sales'],
                    line= dict(color= 'orange'),
                    name='sales'))
      fig.update_layout(title= 'Min-Q Policy Dynamic',
                   xaxis_title='Period',
                   yaxis_title='Demand' ,template=large_rockwell_template)


      fig.show()
      
  
  
  a= [data,metrics]
  return a 


def sim_min_Q(demand, leadtime, service_level,Quantity,distribution= 'normal',mean = False, sd=False,
                       shortage_cost = False, inventory_cost = False, 
                       ordering_cost = False,initial_inventory_level = False,
                       Min= False,recalculate=False,recalculate_windows=False,plot=False):
  """[Simulating a Min,Q policy or also called S,Q policy,  .
     The Function takes a demand vector, mean of demand ,sd,lead time and requested service level to simulate an inventory system, 
     orders are lost if inventory level is less than requested demand, also ordering is made at
     day t+1, metrics like item fill rate and cycle service level are calculated. 
     the min is calculated based on a normal distribution or a poisson distribution, also min can be set manually.
     Q (fixed quantity) is ordered whenever inventory position reaches min]

   Args:
      demand ([float]): [demand in N time periods]
      leadtime ([float]): [lead time from order to arrival]
      service_level ([float]): [cycle service level requested]
      Quantity ([float]): Fixed order quantity to be ordered at min.
      distribution ([str]) :distribution  to calculate safety stock based on demand distribution, current choices are 'normal' or 'poisson'
      mean ([float]): [average demand in N time periods.]
      sd ([float]): [standard deviation in N time periods.]
      shortage_cost (bool, optional): [shortage cost per unit of sales lost]. Defaults to False.
      inventory_cost (bool, optional): [inventory cost per unit.]. Defaults to False.
      ordering_cost (bool, optional): [ordering cost for every time an order is made.]. Defaults to False.
      initial_inventory_level ([float]): Default is False and simulation starts with min as inventory level
      min  ([float]):Default is False and min is calculated based on mean,demand and lead time unless set manually
      recalculate  ([float]): the mean and sd is recalculated every X periods from first period to x,default is FALSE .
      recalculate_windows  ([float]): the min  mean and sd windows to recalculate , for exammple if it is set to 4 mean and sd
                           is calculated from t to t-4,,default is FALSE .
      plot  (bool, optional): Default is False, if true a plot is generated
   Returns:
      [list]: [a list of two, the simulation and the metrics.]

   Examples:
      [sim_min_Q(demand=numpy.random.uniform(2,20,200).round(),Quantity=100,
          leadtime=5,service_level=0.95,plot=True)]

  """    
  L = leadtime
  N = len(demand) 
  Q=Quantity
  if( type(recalculate) != bool):
      mean = numpy.zeros(N+1)
      sd= numpy.zeros(N+1)
      minn= numpy.zeros(N+1)
      Min= numpy.zeros(N+1)
      for i in range(len(mean)):
          mean[i]= numpy.mean(demand[0:i])if (numpy.isnan(numpy.mean(demand[0:i]))==False) else demand[0]
          sd[i]= numpy.std(demand[0:i])if (numpy.isnan(numpy.std(demand[0:i]))==False) else 0
          if(distribution== 'normal'):
              minn[i]= round((mean[i] *leadtime)+ ((sd[i]*numpy.sqrt(leadtime))* scipy.stats.norm.ppf(service_level)))
          else :
              minn[i]= scipy.stats.poisson.ppf(service_level,mean[i]*leadtime)
         
      if(type(recalculate_windows) != bool):
          mean[0]= demand[0]
          sd[0]= numpy.std(demand)
          for i in range(1,len(mean)):
              mean[i]= (numpy.mean(demand[max((i- recalculate_windows),0):(i-1)])if 
                        (len(demand[max((i- recalculate_windows),0):(i-1)])>0) else demand[0]) 
              sd[i]= (numpy.std(demand[max((i- recalculate_windows),0):(i-1)])if 
                        (len(demand[max((i- recalculate_windows),0):(i-1)])>0) else sd[0]) 
              if(distribution== 'normal'):
                  minn[i]= round((mean[i] *leadtime)+ ((sd[i]*numpy.sqrt(leadtime))* scipy.stats.norm.ppf(service_level)))
              else :
                  minn[i]= scipy.stats.poisson.ppf(service_level,mean[i]*leadtime)  
      Min[0]= minn[1]  
      for i in range(1,len(Min)):
          Min[i]= Min[i-1] if((i % recalculate) != 0) else minn[i]
  
  def classfication(demand):
      def intervals(x):
          y=numpy.zeros(len(x)+2)
          k=0
          counter=0
          for tmp in range(len(x)):
              if (x[tmp]==0):
                  counter= counter +1
              else :
                  k=k+1
                  y[k]= counter
                  counter =1
          y= y[y>0]
          y[numpy.isnan(y)]=1
          return y
      def demand1(x):
          y= x[x!=0]
          return y
      D = demand1(demand)
      ADI = numpy.mean(intervals(demand))
      CV2 = (numpy.std(D)/numpy.mean(D))**2
      
      if (ADI > 4/3):
          if (CV2 >0.5):
              type1= 'Lumpy'
          else :
              type1= 'Intermittent'
      else  :
          if(CV2 >0.5):
              type1= 'Erratic'
          else:
              type1= 'Smooth'
               
      return type1
  class1= classfication(demand)
   
  if((type(mean)== bool) & (type(recalculate)==bool)):
    mean= numpy.mean(demand)
  elif ((type(mean)!= bool) & (type(recalculate)==bool)):
    mean=mean
  
  
  if((type(sd)== bool) & (type(recalculate)==bool)):
    sd= numpy.std(demand)
  elif ((type(sd)!= bool) & (type(recalculate)== bool)):
    sd =sd
  
  
  if ((type(Min) != bool) & (type(recalculate) == bool)):
    
    Min= Min
    Min =  numpy.repeat(Min,N+1)
    
  elif((distribution== 'normal')& (type(recalculate)== bool)):
    
    Min = round((mean *leadtime)+ ((sd*numpy.sqrt(leadtime))* scipy.stats.norm.ppf(service_level)))
    Min =  numpy.repeat(Min,N+1)
    
  elif ((distribution== 'poisson') & (type(recalculate)== bool)):
    
    Min = scipy.stats.poisson.ppf(service_level,mean[i]*leadtime)
    Min =  numpy.repeat(Min,N+1)
    
  saftey_stock= Min- (mean *leadtime)            

  order = numpy.zeros(N+1)
  I = numpy.zeros(N+1)
  IP = numpy.zeros(N+1)
  sales = numpy.zeros(N+1)
  recieved = numpy.zeros(N+1)
  order[0]=0
  demand= numpy.append(numpy.array(0),demand)

  if(initial_inventory_level==False):
    IP[0] = I[0] =  Min[0]
  else :
    IP[0] = I[0] =  initial_inventory_level


  
  
  for t in range(1,L+1):
    sales[t] = min (demand[t], I[t-1])
    I[t] = I[t-1] - sales[t]
    order[t] = Q * (IP[t-1] <= Min[t])
    IP[t] =  IP[t-1] + order[t] - sales[t]
    
  
  
  for t in range(L+1,N+1):
    sales[t] = min(demand[t], I[t-1] + order[t-L])
    I[t] = I[t-1] + order[t-L] - sales[t]
    order[t] = Q * (IP[t-1] <= Min[t])
    IP[t] = IP[t-1] + order[t] - sales[t]
    recieved[t]= order[t-L]
  
 

  data=pandas.DataFrame({'period':range(1,N+2),'demand':demand,'sales':sales,'inventory_level':I,
                   'inventory_position':IP,'saftey_stock': saftey_stock,'min':Min,'order': order,'Q':Quantity,
                   'recieved':recieved},index= range(1,N+2))
  
  data['lost_order']= data['demand'] - data['sales']
  
  metrics= pandas.DataFrame({'shortage_cost': sum(data['lost_order'])*shortage_cost,
                       'inventory_cost': sum(data['inventory_level'])*inventory_cost,
                       'average_inventory_level': data['inventory_level'].mean(),'total_orders':len(order[order>0]),
                       'total_lost_sales': sum(data['lost_order']),
                       'ordering_cost':  len(data['order'][data['order']>0]) *ordering_cost,'average_ordering_quantity':(order[order>0]).mean(),
                       'ordering_interval': str(round(len(demand)/len(order[order>0]),2))+'_periods',
                       'Item_fill_rate': 1-(sum(data['lost_order'][data['lost_order']>0]))/sum(demand[1:(len(demand)-1)]),
                       'cycle_service_level': 1-(len(data['lost_order'][data['lost_order']>0])/(len(demand)-1)),
                       'saftey_stock':saftey_stock.mean(),'average_sales': sales.mean() },index= [0])
  metrics['average_flow_time(throughput)']= metrics['average_inventory_level']/metrics['average_sales']
  metrics['class']= class1
  
  if(plot== True):
      large_rockwell_template = dict(
       layout=plotly.graph_objects.Layout(title_font=dict(family="Rockwell", size=24))
                                      )
      fig= plotly.graph_objects.Figure()
        
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['inventory_level'],
                                                 mode='markers',marker=dict(color='green'),
                                                 name= 'inventory level'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['order'],
                    line= dict(color= 'grey'),
                    name='order'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['demand'],
                    line= dict(color= 'royalblue'),
                    name='demand'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['period'], y= data['sales'],
                    line= dict(color= 'orange'),
                    name='sales'))
      fig.update_layout(title= 'Min Q Policy',
                   xaxis_title='Period',
                   yaxis_title='Demand' ,template=large_rockwell_template)


      fig.show()
      
  
  
  a= [data,metrics]
  return a 



def single_product_optimization(x,y,service_product_name,current_price,degree=3,cost=0,plot=False):
  """[calculate the scipy.optimized price based on the price response function. the price response function is measured twice, one with linear model and
      one time with a logit model. a simulation is then made with each price response function to define the maximum revenue for each.
      finally, a suggestion of which model to choose and the optimum price to use for this product.
      it is preferable to de-seasonalize the sales data before fitting if the sales
       are affected by spikes and declines due to regular events as holidays and weekends.]

  Args:
      x ([array]): [a vector of average weekly/monthly/daily price data of a product]
      y ([array]): [a vector of average weekly/monthly/daily sales data of a product]
      degree ([int]): [degree of polynomial,Default is 3]
      service_product_name ([objct]): [he name of the product or service.]
      current_price ([float]): [the current price of the product or service.]
      cost ([float]): [cost of the product.Default is Zero]
  Returns:
     [list]:[list of the squared error of th logit model, the squared error of the linear model, 
     the best model for this product, the optimum
             price for both the linear and the logit model, the current price,
             the a,b,c parameters of th logit model,the linear model paremeters , data simulated
             at different price points and th expected revenue and the fitting 
             results of both the logit and linear model.]     
  Examples:
     [single_product_optimization(x= [5,8,10,12],y=[25,21,23,15],degree=3,
       service_product_name = "Goat Cheese",current_price = 8.5,cost=7,plot=True)]

    """
  """   """
  Measured = pandas.DataFrame({'x':x,'y':y})
  X= Measured[['x']].values
  y=Measured[['y']].values
  model= sklearn.linear_model.LinearRegression().fit(X,y)
  poly = sklearn.preprocessing.PolynomialFeatures(degree=degree, include_bias=False)
  poly_features = poly.fit_transform(X.reshape(-1, 1))
  model_poly=sklearn.linear_model.LinearRegression().fit(poly_features,y)
  Measured['lm_p']=model.predict(X)
  Measured['poly_p']= model_poly.predict(poly_features)
  squared_sum_lm=sum((Measured['y'] - Measured['lm_p'])**2)
  squared_sum_poly=sum((Measured['y'] - Measured['poly_p'])**2)

  #initialize values
  c=max(Measured['y'])
  b = -model.coef_*4/c
  a = -(Measured['x'].median())*b
  x0= [a,b,c]
  #define function to optimise: optim will minimize the output
  def f (x) :

       y=0
       a=x[0]
       b=x[1]
       c=x[2]

       Predicted_y =  c * numpy.exp(-(a+b*Measured['x'])/(1+numpy.exp(-(a+b*Measured['x']))))

       y = sum(( Measured['y']-Predicted_y)**2)

       return y

  
  
  #call optim: results will be available in variable Y
  Y= scipy.optimize.minimize(f, x0, method='Nelder-Mead', tol=1e-6,options={'maxiter': 100000})


  sum_squared_logit=Y.fun

  data=pandas.DataFrame({'x': numpy.arange(min(Measured['x'])-1.8*(Measured['x'].std()),
                                           max(Measured['x'])+1.8*(Measured['x'].std()))})

  def logit1 (x,a=Y.x[0] ,b=Y.x[1],c=Y.x[2]):
      y= c * numpy.exp(-(a+b*x)/(1+numpy.exp(-(a+b*x))))
      return(y)
  poly_featuresq = poly.fit_transform(data[['x']].values.reshape(-1, 1))
  Measured['logit_p']=logit1(Measured['x'])
  data['predicted_linear']= model.predict(data[['x']])
  data['predicted_logit']= logit1(data['x'])
  data['revenue_linear']= data['predicted_linear'] *data['x']
  data['revenue_logit']= data['predicted_logit'] *data['x']
  data['profit_linear']= data['revenue_linear']-( data['predicted_linear']*cost)
  data['profit_logit']= data['revenue_logit']-( data['predicted_logit']*cost)
  data['predicted_poly']= model_poly.predict(poly_featuresq)
  data['revenue_poly']= data['predicted_poly'] *data['x']
  data['profit_poly']= data['revenue_poly']-( data['predicted_poly']*cost)


  def best_model():
     if(min(sum_squared_logit ,squared_sum_lm,squared_sum_poly)== sum_squared_logit):
        a=  'Logit model'
 
     elif(min(sum_squared_logit ,squared_sum_lm,squared_sum_poly)== squared_sum_lm):
        a='linear model'
     else :
        a= 'Poly model'
     return a
 
  best_model= best_model()  
  
  best_price_profit_linear= data['x'][data['profit_linear']==max(data['profit_linear'])]
  best_price_profit_logit=data['x'][data['profit_logit']==max(data['profit_logit'])]
  best_price_profit_poly=data['x'][data['profit_poly']==max(data['profit_poly'])]

  
  best_price_linear= data['x'][data['revenue_linear']==max(data['revenue_linear'])]
  best_price_logit=data['x'][data['revenue_logit']==max(data['revenue_logit'])]
  best_price_poly=data['x'][data['revenue_poly']==max(data['revenue_poly'])]

  
  all_data={'optimization_paremeters':Y,'lm_model':model,
            'squared_error_logit':'squared_error_logit= '+ str(sum_squared_logit),
                 'squared_error_linear':'squared_errorr_lm= '+ str(squared_sum_lm),
                 'squared_error_poly':'squared_errorr_poly= '+ str(squared_sum_poly),

                 'simulated data':data,
                 'best_model':'best_model is '+ str(best_model)+'for '+str(service_product_name) ,
                 'optimum_linear':'optimum linear revenue price is '+str(numpy.array(best_price_linear))+'for '+str(service_product_name),
                 'optimum_logit':'optimum logit revenue price is '+str(numpy.array(best_price_logit))+'for '+str(service_product_name),
                 'optimum_poly':'optimum poly revenue price is '+str(numpy.array(best_price_poly))+'for '+str(service_product_name),

                 'current_price':'current price is '+str(current_price),
                'article_name':'article name is '+str(service_product_name),
                'predictions':Measured,
                 'point_of_maximum_profits': {'linear':numpy.array(best_price_profit_linear),'logit':numpy.array(best_price_profit_logit),
                    'poly': numpy.array(best_price_profit_poly)}}
  
  if(plot== True):
      large_rockwell_template = dict(
       layout=plotly.graph_objects.Layout(title_font=dict(family="Rockwell", size=24))
                                      )
      data= data[(data.revenue_poly > 0) & (data.x >0) &(data.profit_poly >0) ]
      fig= plotly.graph_objects.Figure()
        
      fig.add_trace(plotly.graph_objects.Scatter(x=data['x'], y= data['revenue_poly'],
                                                 line= dict(color= 'orange'),
                                                 name= 'Revenue Polynomial'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['x'], y= data['revenue_linear'],
                                                    line= dict(color= 'brown'),
                    name='Revenue Linear'))
      fig.add_trace(plotly.graph_objects.Scatter(x=data['x'], y= data['revenue_logit'],
                                               line= dict(color= 'magenta'),
                    name='Revenue Logit'))
      
      fig.update_layout(title= 'Revenue curve for '+ service_product_name,
                   xaxis_title='Price',
                   yaxis_title='Expected' ,template=large_rockwell_template)


      fig.show()
      
      fig4= plotly.graph_objects.Figure()
      
      fig4.add_trace(plotly.graph_objects.Scatter(x=data['x'], y= data['profit_poly'],
                                                 line= dict(color= 'orange'),
                                                 name= 'Profit Polynomial'))
      fig4.add_trace(plotly.graph_objects.Scatter(x=data['x'], y= data['profit_linear'],
                    line= dict(color= 'magenta'),
                    name='Profit Linear'))
      fig4.add_trace(plotly.graph_objects.Scatter(x=data['x'], y= data['profit_logit'],
                    line= dict(color= 'brown'),
                    name='Profit Logit'))
      
      fig4.update_layout(title= 'Profit curve for '+ service_product_name,
                   xaxis_title='Price',
                   yaxis_title='Expected' ,template=large_rockwell_template)


      fig4.show()
      
      fig2= plotly.graph_objects.Figure()
        
      fig2.add_trace(plotly.graph_objects.Scatter(x=Measured['x'], y= Measured['y'],
                                                 mode='markers',marker=dict(color='green'),
                                                 name= 'Actual observations'))
      fig2.add_trace(plotly.graph_objects.Scatter(x=Measured['x'], y=  Measured['lm_p'],
                    line= dict(color= 'grey'),
                    name='Fit Linear'))
      fig2.add_trace(plotly.graph_objects.Scatter(x=Measured['x'], y=  Measured['poly_p'],
                    line= dict(color= 'blue'),
                    name='Fit Polynomial'))
     
      
      fig2.add_trace(plotly.graph_objects.Scatter(x=Measured['x'], y=  Measured['logit_p'],
                    line= dict(color= 'orange'),
                    name='Fit Logit'))
     
      
      fig2.update_layout(title= 'Models fit for '+ service_product_name,
                   xaxis_title='Price',
                   yaxis_title='Demand' ,template=large_rockwell_template)


      fig2.show()
      
      fig3= plotly.graph_objects.Figure()
        
      fig3.add_trace(plotly.graph_objects.Scatter(x=data['x'], y= data['predicted_linear'],
                                                 line= dict(color= 'grey'),
                                                 name= 'Linear Response function'))
      fig3.add_trace(plotly.graph_objects.Scatter(x=data['x'], y= data['predicted_logit'],
                                                 line= dict(color= 'blue'),
                                                 name= 'Logit Response function'))
      fig3.add_trace(plotly.graph_objects.Scatter(x=data['x'], y= data['predicted_poly'],
                                                 line= dict(color= 'orange'),
                                                 name= 'Poly Response function'))
     
      
     
      
      fig3.update_layout(title= 'Response functions for '+ service_product_name,
                   xaxis_title='Price',
                   yaxis_title='Demand' ,template=large_rockwell_template)


      fig3.show()
  
  
  
  return(all_data)
               
  

               
  
