import random
import logging

import sys
import os

# Get the path to the current file's directory (e.g., .../hot_potato_sim)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the path to the parent directory (e.g., .../Research hot potato test sim)
parent_dir = os.path.dirname(current_dir)

# Add the parent directory to Python's list of places to look for modules
sys.path.append(parent_dir)



import time

from datetime import datetime, timezone


from v2_orderbook.Order_Class import Order
from v2_orderbook.Trade_Class import Trade

from collections import defaultdict

"""Missed this case in limit-limit matching , imporve it , till then ,
we assume agents places the orders with thier brain on!"""

"""below one"""
""" A limit order executes only at its specified price or better. If it arrives and
finds liquidity on the opposite side at its exact price, it matches.
If it finds liquidity at a better price (e.g., a buy limit at $100.05 finds asks at $100.04),
it should match at that better price. If there's no liquidity at its price or better,
it sits on the book at its specified price."""


class OrderBook:
    def __init__(self):
        self.bids = defaultdict(list)     # This made our below task of appending any list having new key , easy !
        self.asks = defaultdict(list)     # As Mentioned Above , and Refered Below !
        self.trades = []                  # will store the Trade Objects , after each executed trade !
        self.orders_by_id = {}          # use for cancel order / or to remove orders , becoz market hits from itch      


    def remove_order(self,order_id,timestamp):
        # now use this for orderexecuted message ,okay, boy ;)   
        # look this function return a trade 

        if order_id in self.orders_by_id:
            order = self.orders_by_id[order_id]
            price = order.price

            if order.side == "BUY":
                        if price in self.bids:
                            self.bids[price].remove(order)  # // order removed from book
                            del self.orders_by_id[order_id] # // key value pair removed
                            return Trade(price=order.price,qty=order.qty,buyer_id=order.agent_id,seller_id=None,timestamp=timestamp)
                     
            elif order.side == "SELL":
                        if price in self.asks:
                            self.asks[price].remove(order)
                            del self.orders_by_id[order_id]   
                            return Trade(price=order.price,qty=order.qty,buyer_id=None,seller_id=order.agent_id,timestamp=timestamp)  

        return None # if order not in book . means our agent took it off , so.../
        # /... nothing needs to be done . so no print , no log . that trade already may have done the logging , when agent interacted with that order ! 
        # IMP CONCEPT discussed just above ... look sometimes , when docmentation is done # __________________________________________________________________________________ good point , understand

    def __repr__(self):
        return f'Bids -> {self.bids}  Asks -> {self.asks}'    

    def get_best_bid(self):
        if self.bids.keys():
            return max(self.bids.keys())
        else:
            return None
        
    def get_best_ask(self):
        if self.asks.keys():
            return min(self.asks.keys())
        else:
            return None
        

    def add_place_limit_order(self,L_Order,sim_time):   # places limit order in orderbook !

        # if L_Order.timestamp == None:   # when order have no timestamp then do make one. As in market order case where it become limit ,we will let it carry the old timestamp it had !
        #     L_Order.timestamp = datetime.now(timezone.utc)   # Time object is made which is aware of timezone 
    
        sim_time = sim_time #---- check this ---- status : pending

        price = L_Order.price
        bids = self.bids
        asks = self.asks
        #  check if  the varialbe have reference to same object -> status : checked , and yes

        recent_trades = []  # to return the trades happened in this iteration / temporery , no history !

        if L_Order.side == 'BUY':    # matches market order ! (this is old comment , ignore..)
            
            if price in asks:  # LIMIT - LIMIT MATCHING  ( Remember two type of matching , mar-lim , lim-lim) (imporve it , it still dont do the intended thing , you know that , the min_ask first , to provide better , still it currently do make execute and remaining sits and make a new price level , and that is a buy price level at 240.5 when min_ask is 238 and min_bid is 237.5,.. o look it hear , in last , rn use this , as most orders are not that shit that would place a buy above the ask)
                               # if asks is empty , it evalutes false , no crash ..... 

                for order in list(self.asks[price]) :   # iterate over copy , as we update the main 
                    
                    diff = L_Order.qty - order.qty

                    if diff == 0:
                        self.trades.append(Trade(price,L_Order.qty,L_Order.agent_id,order.agent_id,sim_time))
                        recent_trades.append(Trade(price,L_Order.qty,L_Order.agent_id,order.agent_id,sim_time))# for returning recent trades...
                        asks[price].remove(order)
                        del self.orders_by_id[order.order_id] # new / 05 NOV 25 -------------------------------------------------------id
                        if not self.asks[price]: # whole price level consumed
                            del self.asks[price]  # remove the key value pair
                        break 
                    
                    elif diff < 0:
                        self.trades.append(Trade(price,L_Order.qty,L_Order.agent_id,order.agent_id,sim_time)) 
                        recent_trades.append(Trade(price,L_Order.qty,L_Order.agent_id,order.agent_id,sim_time))# for returning recent trades...
                        order.qty =  abs(diff)
                        break

                    elif diff > 0:
                        self.trades.append(Trade(price,order.qty,L_Order.agent_id,order.agent_id,sim_time)) 
                        recent_trades.append(Trade(price,order.qty,L_Order.agent_id,order.agent_id,sim_time)) # for returning recent trades...
                        L_Order.qty = abs(diff)
                        asks[price].remove(order)
                        del self.orders_by_id[order.order_id] # new / 05 NOV 25 -------------------------------------------------------id

                        if not self.asks[price]: # whole price level consumed
                            del self.asks[price]  # remove the key value pair
                            self.bids[price].append(L_Order)    # add to bids , the remaining order qty
                            self.orders_by_id[L_Order.order_id] = L_Order  # new / 05 NOV 25 ++++++++++++++++++++++++++++++++++++++++id
                            break

            else:  # price is not in ask
                self.bids[L_Order.price].append(L_Order)          #  eg. self.bids[210] == [Order]      # HERE (Ref.)
                self.orders_by_id[L_Order.order_id] = L_Order  # new / 05 NOV 25 ++++++++++++++++++++++++++++++++++++++++++++++++++++id

        elif L_Order.side == 'SELL':
            
            if price in bids:  # LIMIT - LIMIT MATCHING  ( Remember two type of matching , mar-lim , lim-lim)
                               # even if bids is empty , it evalutes false , no crash ..... 

                for order in list(self.bids[price]):
                    
                    diff = L_Order.qty - order.qty

                    if diff == 0:
                        bids[price].remove(order)
                        del self.orders_by_id[order.order_id] # new / 05 NOV 25 -------------------------------------------------------id
                        self.trades.append(Trade(price,L_Order.qty,order.agent_id,L_Order.agent_id,sim_time))
                        recent_trades.append(Trade(price,L_Order.qty,order.agent_id,L_Order.agent_id,sim_time))# for returning recent trades...

                        if not self.bids[price]: # means last element reached
                            del self.bids[price]  # remove the key value pair                        
                        break 
                    
                    elif diff < 0:
                        self.trades.append(Trade(price,L_Order.qty,order.agent_id,L_Order.agent_id,sim_time)) 
                        recent_trades.append(Trade(price,L_Order.qty,order.agent_id,L_Order.agent_id,sim_time)) # for returning recent trades... 
                        order.qty =  abs(diff)  # qty updated
                        break

                    elif diff > 0:
                        self.trades.append(Trade(price,order.qty,order.agent_id,L_Order.agent_id,sim_time)) 
                        recent_trades.append(Trade(price,order.qty,order.agent_id,L_Order.agent_id,sim_time))# for returning recent trades...
                        L_Order.qty = abs(diff)
                        bids[price].remove(order)
                        del self.orders_by_id[order.order_id] # new / 05 NOV 25 -------------------------------------------------------id
            

                        if not self.bids[price]: # means last element reached
                            del self.bids[price]  # remove the key value pair
                            self.asks[price].append(L_Order)    # add to asks , the remaining order qty
                            self.orders_by_id[L_Order.order_id] = L_Order  # new / 05 NOV 25 ++++++++++++++++++++++++++++++++++++++++++id
                            break          
            
            else:
                self.asks[L_Order.price].append(L_Order)          #  eg. self.asks[211] == [Order]
                self.orders_by_id[L_Order.order_id] = L_Order  # new / 05 NOV 25 ++++++++++++++++++++++++++++++++++++++++++++++++++++++id
        
        return recent_trades # returning the trades occurd in recent processsing ............main statment .........................

# check if  you wanna return some value from this function
#####################################################################################################################


    """ key concept : [object1 , object 2 , ...] ,, here in memory list is stored at lets say starting 
    from 2000 and lets say 10 order objects . so it stores till 2009 . also each bloack have address
    of the order objects , so it is like 3500 , 3790 , 3690 , 3460 , .... , 4040 ,, this are adresses
    of the order object and each orrder object could have taken a accordingly in consecutive location.
    so when we do list(self.asks[price] , the copy is returned , so now the same object references
    (as adresses) but in different location then 2000 to 2009 . it can be 9000 to 9009. 
    so by this conclusion is : when you do this : order.qty = abs(diff) , update , the 
    order object is updated and both copy list and original list in self.asks have changes reflected , 
    as both having the references or addresses """


    def add_match_market_order(self,M_Order,sim_time):
        
        sim_time = sim_time
        bids = self.bids
        asks = self.asks
        recent_trades = [] 
        
        if M_Order.side == "BUY" and len(self.asks) == 0:  # base condition
            logging.warning(f"Market Buy Order {M_Order.order_id} REJECTED - No Asks on book.")
            return recent_trades # <-- FIX: Return empty list, DO NOT add to book  

            # return self.add_place_limit_order(M_Order,sim_time)  # Places the M_Order into Orderbook ,(it becomes limit order for while) if there are No Orders left to match with ! 
            # # return gets recent trades , so and it returns ...
        
        elif M_Order.side == "SELL" and len(self.bids) == 0:  # base condition
            logging.warning(f"Market Sell Order {M_Order.order_id} REJECTED - No Bids on book.")
            return recent_trades

              
            # return self.add_place_limit_order(M_Order,sim_time)  
            # # return gets recent trades , so and it returns ...

        elif M_Order.side == 'BUY' :
            min_ask = self.get_best_ask()  # Finds the key with MINIMUM Price Value

            for order in list(self.asks[min_ask]):  # first order is on priority (check append rule of list.) 

                diff = M_Order.qty - order.qty

                if diff == 0: 
                    self.trades.append(Trade(order.price,M_Order.qty,M_Order.agent_id,order.agent_id,sim_time))
                    recent_trades.append(Trade(order.price,M_Order.qty,M_Order.agent_id,order.agent_id,sim_time))# for returning recent trades...
                    self.asks[min_ask].remove(order)  # complete fill order is removed  # book updated
                    del self.orders_by_id[order.order_id] # new / 05 NOV 25 -------------------------------------------------------id

                    if not self.asks[min_ask]:  # whole price level consumed
                        del self.asks[min_ask]  # Removes or Delete the key value pair , of min_ask thing...
                    break

                    # return f'{self.trades[-1]} successful '   # A full complete trade Executed ,, with NO Complexity unlike Below ! 
                    # remove the above comment ( most probably )

                elif diff < 0: 
                    self.trades.append(Trade(order.price,M_Order.qty, M_Order.agent_id, order.agent_id,sim_time))
                    recent_trades.append(Trade(order.price,M_Order.qty, M_Order.agent_id, order.agent_id,sim_time))# for returning recent trades...
                    order.qty = abs(diff)   # qty updated  # book updated
                    break

                elif diff > 0: 
                    self.trades.append(Trade(order.price,order.qty,M_Order.agent_id,order.agent_id,sim_time))
                    recent_trades.append(Trade(order.price,order.qty,M_Order.agent_id,order.agent_id,sim_time))# for returning recent trades...
                    self.asks[min_ask].remove(order)    # book updated
                    del self.orders_by_id[order.order_id] # new / 05 NOV 25 -------------------------------------------------------id

                    M_Order.qty = abs(diff)    # qty updated  M_Order 
                    
                    if not self.asks[min_ask]:   # min price level consumed 
                        del self.asks[min_ask]    # list with min price deleted 
                        recent_trades.extend(self.add_match_market_order(M_Order,sim_time))  # now same function for nxt minimum price # recursion 
                        break
            
            return recent_trades # returning the trades occurd in recent processsing ............main statment ........................
        
        elif M_Order.side == 'SELL':
            max_bid = self.get_best_bid()  # Finds the key with MAXIMUM Price Value 

            for order in list(self.bids[max_bid]):  # first order is on priority (check append rule of list.) 

                diff = M_Order.qty - order.qty

                if diff == 0: 
                    self.trades.append(Trade(order.price,M_Order.qty,order.agent_id,M_Order.agent_id,sim_time))
                    recent_trades.append(Trade(order.price,M_Order.qty,order.agent_id,M_Order.agent_id,sim_time))# for returning recent trades...
                    self.bids[max_bid].remove(order)  # complete fill order is removed  # book updated
                    del self.orders_by_id[order.order_id] # new / 05 NOV 25 -------------------------------------------------------id

                    if not self.bids[max_bid]:  # whole price level consumed
                        del self.bids[max_bid]  # Removes or Delete the key value pair , of max_bid thing...
                    break

                elif diff < 0: 
                    self.trades.append(Trade(order.price,M_Order.qty,order.agent_id,M_Order.agent_id,sim_time))
                    recent_trades.append(Trade(order.price,M_Order.qty,order.agent_id,M_Order.agent_id,sim_time))# for returning recent trades...
                    order.qty = abs(diff)   # qty updated  # book updated
                    break

                elif diff > 0: 
                    self.trades.append(Trade(order.price,order.qty,order.agent_id,M_Order.agent_id,sim_time))
                    recent_trades.append(Trade(order.price,order.qty,order.agent_id,M_Order.agent_id,sim_time))# for returning recent trades...
                    self.bids[max_bid].remove(order)    # book updated
                    del self.orders_by_id[order.order_id] # new / 05 NOV 25 -------------------------------------------------------id

                    M_Order.qty = abs(diff)    # qty updated  M_Order 
                    
                    if not self.bids[max_bid]:   # max price level consumed 
                        del self.bids[max_bid]    # list with max price deleted 
                        recent_trades.extend(self.add_match_market_order(M_Order,sim_time))  # now same function for nxt minimum price # recursion 
                        break

            return recent_trades # returning the trades occurd in recent processsing ............main statment .........................
        
#####################################################################################################################

    def process_order(self,order,sim_time):

    #      WARNING : WE ONLY USE THIS FOR "Add Order" , NOT FOR "OrderExecuted" / SEE main_sim.py ,. ITCH 5.0 

        if order.type == "LIMIT":
            return self.add_place_limit_order(order,sim_time)
        elif order.type == "MARKET":    
            return self.add_match_market_order(order,sim_time) #---------------------------------------------------9:00 pm 5 nov 25
            # self.add_match_market_order returns a list of trades , that occur ... , similarly for add_place_limit...()


    def parse_payload_to_order(self,payload , event_type , timestamp):
        if event_type == "AddOrder" :  # check if Add Order with another thing is needed , itch 5.0 , / ................................. 1:32AM 06 NOV 25
            order_id = payload["OrderReferenceNumber"]
            side = None  ##################################################### check here  .................................................................................................3:56AM 25  / 07-11-25
            if payload["BuySellIndicator"] == 66:
                side = "BUY"
            elif payload["BuySellIndicator"] == 83:
                side = "SELL"
            type = "LIMIT"  # as it is AddOrder  
            qty = payload["Shares"]
            price = payload["Price"]/10000
            agent_id = None  # no MPID , as it is evntype 'A'
            symbol = payload["Stock"]
            order = Order(order_id,agent_id,type,side,qty,symbol,price,timestamp)
            return order  
        
        elif event_type == "AddOrderWithMPIDAttribution" :  # check if Add Order with another thing is needed , itch 5.0 , / ................................. 1:32AM 06 NOV 25
            order_id = payload["OrderReferenceNumber"]
            side = None
            if payload["BuySellIndicator"] == 66:
                side = "BUY"
            elif payload["BuySellIndicator"] == 83:
                side = "SELL"
            # side = None
            # if payload["BuySellIndicator"].strip().upper() == "B":
            #     side = "BUY"
            # elif payload["BuySellIndicator"].strip().upper() == "S":
            #     side = "SELL"
            type = "LIMIT"  # as it is AddOrder  
            qty = payload["Shares"]
            price = payload["Price"]/10000
            agent_id = payload["Attribution"]
            symbol = payload["Stock"]
            order = Order(order_id,agent_id,type,side,qty,symbol,price,timestamp)
            return order  
        

        elif event_type == "OrderExecuted" or event_type == "OrderExecutedWithPrice":
                
            order_id = random.randint(100000000000,999999999999)  # a 12 digit , so different from others....
            agent_id = None # no MPID , hohou!

            # if payload.get("BuySellIndicator") == 66: # ORDER executed was stting on buy side . means /// below... 
            #     side = "SELL" # A sell MAKRET ORDER hits the thing , so we make one, we are making//.
                    
            side = "SELL"
            if payload.get("BuySellIndicator") == 83: # ORDER executed was stting on SELL side . means /// below... 
                side = "BUY" # A BUY MAKRET ORDER hits the thing , so we make one, we are making//.

            qty = payload.get("ExecutedShares")
            order = Order(order_id,agent_id,"MARKET",side,qty,symbol="SPY",price=None,timestamp=timestamp)
            return order

        

        
# BOTH OF THIS PROCESS_ORDER AND PARSE_PAYLOAD_TO_ORDER function are used only for Add Order . _____________________
# logic for ORDEREXECUTED OR WITH PRICE , IS IN main_sim.py itself__________________________________________________ 1:34AM 06 NOV 25 



"""{
  "Source": "ITCH",
  "EventType": "AddOrderWithMPID",
  "Symbol": "AAPL",
  "Exchange": "NASDAQ",
  "TimestampUTC": 1730795400000000000,
  "Payload": {
    "OrderReferenceNumber": 987654321,
    "BuySellIndicator": "S",
    "Shares": 500,
    "Stock": "AAPL",
    "Price": 1907500,
    "Attribution": "ABCD"
  }
}
"""


"""{
  "Source": "ITCH",
  "EventType": "OrderExecutedWithPrice",
  "Symbol": "AAPL",
  "Exchange": "NASDAQ",
  "TimestampUTC": 1730795404000000000,
  "Payload": {
    "Header": {
      "MessageType": "C",
      "StockLocate": 31512,
      "TrackingNumber": 772,
      "Timestamp": 1730795404000000000
    },
    "OrderReferenceNumber": 9876543211,
    "ExecutedShares": 200,
    "MatchNumber": 4567890124,
    "Printable": "Y",
    "ExecutionPrice": 1905000
  }
}
"""


"""{
  "Source": "ITCH",
  "EventType": "AddOrder",
  "Symbol": "AAPL",
  "Exchange": "NASDAQ",
  "TimestampUTC": 1730795400000000000,
  "Payload": {
    "OrderReferenceNumber": 12345,
    "BuySellIndicator": "B",
    "Shares": 100,
    "Stock": "AAPL",
    "Price": 1905000
  }
}
"""
''''''





# if __name__ == '__main__':

#     # import v2_orderbook.Order_Class as Order_Class

#     # odr1 = Order_Class.Order('O12','1XYZ','LIMIT','BUY',10,210)

#     # Odr_book = OrderBook()

#     # Odr_book.add_place_limit_order(odr1)

#     # print(Odr_book)

#     # time.sleep(6)

    # ord2 = Order_Class.Order('O31','agent9','MARKET','SELL',9)

    # print(Odr_book.add_match_market_order(ord2))

    # time.sleep(5)

    # print(Odr_book)

