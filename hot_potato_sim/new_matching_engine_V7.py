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


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stderr)



import time

from datetime import datetime, timezone


from v2_orderbook.Order_Class import Order
from v2_orderbook.Trade_Class import Trade

from collections import defaultdict

"""UPDATE : THING YOU SAID WE MISSED IS NOW FULLY DONE , OVER AND OUT , THE WHOLE LIMIT ORDER LOGIC IS NOW DONE"""
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

#  ///// oid is shorthand for order_ird ///////////////

    def remove_order(self,order_id,timestamp, silent=False):
        # now use this for orderexecuted message ,okay, boy ;)   
        # look this function return a trade 

        if order_id in self.orders_by_id:
            order = self.orders_by_id[order_id]
            price = order.price

            if order.side == "BUY":
                        if price in self.bids:
                            self.bids[price].remove(order)  # // order removed from book
                            
                            # there was the flaw , now fixed below...............................................................................................................................................12:03AM 7 jan 2026
                            """so the error explained breifly here , the thing was the best bid and ask log file 
                            was just sticking to a bid or ask even when it was having 0 qty st it , then i
                            realized that even after we remove the order_id and order key value pair from self.order_by_id
                            and from the bid (or ask) dict also ,still the price level in the big(or ask) dict exist when 
                            even when this removal or cancellation result in the whole qty vanishing at this price level.
                            in previos versions of the sim , this thing was not much bothering anyone , and nkt even seen , as
                            at that time only agent had the ability to remove/cancel the orders , which most times did not usually
                            vanish the price level as whole , as there were people at that price even when agent removed the order.
                            we can understand why agent do this order placing on that type of level only , where there is someone already ,
                            and the logic is there in the agents.py itself , which is says our agent's actions"""
                            
                            del self.orders_by_id[order_id] # // key value pair removed
                            if not self.bids[price]:  # check if whole price level is at 0 qty after this removing this order.
                                del self.bids[price] # if yes , delete the price level from the asks dict , so no price like this can be fetched in get_best_ask func....... 12:26 AM 7 jan 2026

                            if not silent: # <--- ONLY LOG IF NOT SILENT
                                logging.info(f"CONFIRMATION: [{timestamp}] ORDER REMOVED at price {order.price}  ORDER ID=({order_id})")
                     
            elif order.side == "SELL":
                        if price in self.asks:
                            self.asks[price].remove(order)
                            # here also was the error,see previous commit , now fixed...............................................................................................................................................12:06AM 7 jan 2026 
                            
                            del self.orders_by_id[order_id]
                            if not self.asks[price]:  # check if whole price level is at 0 qty after this removing this order
                                del self.asks[price] # if yes , delete the price level from the asks dict , so no price like this can be fetched in get_best_ask func....... 12:26 AM 7 jan 2026

                            if not silent: # <--- ONLY LOG IF NOT SILENT
                                logging.info(f"CONFIRMATION: [{timestamp}] ORDER REMOVED at price {order.price}  ORDER ID=({order_id})")
        else:
            if not silent:
                logging.info(f"FAILED: [{timestamp}] ORDER REMOVAL ({order_id})")   # if order not in book . means our agent took it off , so.../
        # /... nothing needs to be done . so no print , no log . that trade already may have done the logging , when agent interacted with that order ! 
        # IMP CONCEPT discussed just above ... look sometimes , when docmentation is done # __________________________________________________________________________________ good point , understand

    def reduce_order_qty(self,cancel_qty , order_id,timestamp):
        if order_id not in self.orders_by_id:
            return
        
        order = self.orders_by_id[order_id]
        old_qty = order.qty

        if cancel_qty < old_qty:
            self.orders_by_id[order_id].qty = old_qty - cancel_qty
            logging.info(f"CONFIRMATION: [{timestamp}] ORDER PARTIALLY CANCELLED at price {order.price} | qty {old_qty}->{new_qty} | ID=({order_id})")

        elif cancel_qty == order.qty:
            self.remove_order(order_id,timestamp,silent=True)
            logging.info(f"CONFIRMATION: [{timestamp}] ORDER REMOVED (Full Cancel) at price {order.price} | ID=({order_id})")
        else: # a weired case
            return

    def replace_order(self ,old_oid ,new_oid ,new_price ,new_qty,timestamp):
        # first we know keep queue postion when only the same price and if size is decremented !

        if old_oid not in self.orders_by_id:
            logging.info(f"FAILED: [{timestamp}] REPLACE REJECTED - ID {old_oid} not found")
            return

        old_order = self.orders_by_id[old_oid]
        old_price = old_order.price
        old_qty = old_order.qty

        if new_price == old_order.price and new_qty <= old_qty : # here new_qty is less 
            new_order = old_order
            new_order.order_id = new_oid
            del self.orders_by_id[old_oid]
            self.orders_by_id[new_oid] = new_order 
            
            self.orders_by_id[new_oid].qty = new_qty  # queue position is preserved !
            # Use new_oid if the exchange protocol replaces the ID even on amend
            logging.info(f"CONFIRMATION: [{timestamp}] ORDER AMENDED (Priority Kept): ID({old_oid})->({new_oid}) | price {new_price} | qty {old_qty}->{new_qty}")

        else : # loses queue position ! // (this type of cases->) new_price != old_order.price or new_qty > old_qty 
            self.remove_order(old_oid,timestamp, silent=True) # old order removed !
            
            new_order = Order(new_oid ,None,"LIMIT",old_order.side,new_qty ,old_order.symbol,new_price,timestamp)
            self.add_place_limit_order(new_order,timestamp) # new order placed.
            
            logging.info(f"CONFIRMATION: [{timestamp}] ORDER REPLACED: ID({old_oid})->({new_oid}) | price {old_price}->{new_price} | qty {old_qty}->{new_qty}")

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

    def get_best_price_and_qtys(self):
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()

        if best_bid is not None and best_ask is not None:
            bid_qty = sum(o.qty for o in self.bids[best_bid])  # it would be generally fast , as many times the best price will be having low qty , ,maybe i think so...
            ask_qty = sum(o.qty for o in self.asks[best_ask])
            return (best_bid , bid_qty , best_ask , ask_qty)
            # best_logger.info(f"{best_bid} ({bid_qty})  |  {best_ask} ({ask_qty})")
        return ()

    def add_place_limit_order(self,L_Order,sim_time):   # places limit order in orderbook !

        # if L_Order.timestamp == None:   # when order have no timestamp then do make one. As in market order case where it become limit ,we will let it carry the old timestamp it had !
        #     L_Order.timestamp = datetime.now(timezone.utc)   # Time object is made which is aware of timezone 
    
        sim_time = sim_time #---- check this ---- status : pending

        
        bids = self.bids
        asks = self.asks
        #  check if  the varialbe have reference to same object -> status : checked , and yes

        recent_trades = []  # to return the trades happened in this iteration / temprory , no history !

        if L_Order.side == 'BUY' :
            min_ask = self.get_best_ask()  # Finds the key with MINIMUM Price Value
          
            if min_ask is not None: # means ask side is not over 

                if L_Order.price >= min_ask :
                
                    for order in list(self.asks[min_ask]):  # first order is on priority (check append rule of list.) 

                        diff = L_Order.qty - order.qty

                        if L_Order.agent_id is not None and order.agent_id is not None: # prevents self matching b/w people , mostly for our agent
                            if L_Order.agent_id == order.agent_id:
                                continue  # move to next order                        

                        if diff == 0: 
                            self.trades.append(Trade(order.price,L_Order.qty,L_Order.agent_id,order.agent_id,sim_time))
                            recent_trades.append(Trade(order.price,L_Order.qty,L_Order.agent_id,order.agent_id,sim_time))# for returning recent trades...
                            self.asks[min_ask].remove(order)  # complete fill order is removed  # book updated
                            del self.orders_by_id[order.order_id] # / 08 NOV 25 -------------------------------------------------------id

                            if not self.asks[min_ask]:  # whole price level consumed
                                del self.asks[min_ask]  # Removes or Delete the key value pair , of min_ask thing...
                            break

                            # return f'{self.trades[-1]} successful '   # A full complete trade Executed ,, with NO Complexity unlike Below ! 
                            # remove the above comment ( most probably )...

                        elif diff < 0: 
                            self.trades.append(Trade(order.price,L_Order.qty, L_Order.agent_id, order.agent_id,sim_time))
                            recent_trades.append(Trade(order.price,L_Order.qty, L_Order.agent_id, order.agent_id,sim_time))# for returning recent trades...
                            order.qty = abs(diff)   # qty updated  # book updated
                            break

                        elif diff > 0: 
                            self.trades.append(Trade(order.price,order.qty,L_Order.agent_id,order.agent_id,sim_time))
                            recent_trades.append(Trade(order.price,order.qty,L_Order.agent_id,order.agent_id,sim_time))# for returning recent trades...
                            self.asks[min_ask].remove(order)    # book updated
                            del self.orders_by_id[order.order_id] # / 08 NOV 25 -------------------------------------------------------id

                            L_Order.qty = abs(diff)    # qty updated  L_Order 
                            
                            if not self.asks[min_ask]:   # min price level consumed 
                                del self.asks[min_ask]    # list with min price deleted 
                                recent_trades.extend(self.add_place_limit_order(L_Order,sim_time))  # now same function for nxt minimum price # recursion 
                                break
                    
                    return recent_trades # //this is one case where recursion returns , but no update to book , FOR L_Order , as this is only when the the L_Order is over.                                                        /////// base condition one for recursion
                
                else:  # now L_order.price is not above ask , so place the bid order.                                                                                                                                              /////// base condition two of recursion
                    self.bids[L_Order.price].append(L_Order)          #  eg. self.bids[210] == [Order]
                    self.orders_by_id[L_Order.order_id] = L_Order
                    return recent_trades

            else:  # now ask side is fully over , nothing left , so place the L_Order into bid. // this case is where recursion returns , but when L_Order is still not over , so we updated(placed the remaining L_Order INTO BID) the book with returning.    /////// base condition three of recursion

                    self.bids[L_Order.price].append(L_Order)          #  eg. self.bids[210] == [Order]
                    self.orders_by_id[L_Order.order_id] = L_Order
                    return recent_trades  # this you , it is imp for returns in recursion calls also...../ you see  , you already updated the book , bid , in recursion.  


        elif L_Order.side == 'SELL':
            max_bid = self.get_best_bid()  # Finds the key with MAXIMUM Price Value 

            if max_bid is not None: # means bid side is not over

                if L_Order.price <= max_bid :

                    for order in list(self.bids[max_bid]):  # first order is on priority (check append rule of list.) 

                        diff = L_Order.qty - order.qty

                        if L_Order.agent_id is not None and order.agent_id is not None: # prevents self matching b/w people , mostly for our agent
                            if L_Order.agent_id == order.agent_id:
                                continue  # move to next order

                        if diff == 0: 
                            self.trades.append(Trade(order.price,L_Order.qty,order.agent_id,L_Order.agent_id,sim_time))
                            recent_trades.append(Trade(order.price,L_Order.qty,order.agent_id,L_Order.agent_id,sim_time))# for returning recent trades...
                            self.bids[max_bid].remove(order)  # complete fill order is removed  # book updated
                            del self.orders_by_id[order.order_id] #  / 08 NOV 25 -------------------------------------------------------id

                            if not self.bids[max_bid]:  # whole price level consumed
                                del self.bids[max_bid]  # Removes or Delete the key value pair , of max_bid thing...
                            break

                        elif diff < 0: 
                            self.trades.append(Trade(order.price,L_Order.qty,order.agent_id,L_Order.agent_id,sim_time))
                            recent_trades.append(Trade(order.price,L_Order.qty,order.agent_id,L_Order.agent_id,sim_time))# for returning recent trades...
                            order.qty = abs(diff)   # qty updated  # book updated
                            break

                        elif diff > 0: 
                            self.trades.append(Trade(order.price,order.qty,order.agent_id,L_Order.agent_id,sim_time))
                            recent_trades.append(Trade(order.price,order.qty,order.agent_id,L_Order.agent_id,sim_time))# for returning recent trades...
                            self.bids[max_bid].remove(order)    # book updated
                            del self.orders_by_id[order.order_id] #  / 08 NOV 25 -------------------------------------------------------id

                            L_Order.qty = abs(diff)    # qty updated  L_Order 
                            
                            if not self.bids[max_bid]:   # max price level consumed 
                                del self.bids[max_bid]    # list with max price deleted 
                                recent_trades.extend(self.add_place_limit_order(L_Order,sim_time))  # now same function for nxt minimum price # recursion 
                                break

                    return recent_trades # //this is one case where recursion returns , but no update to book , FOR L_Order , as this is only when the the L_Order is over.                                                        /////// base condition one for recursion
                
                else:  # now L_order.price is not below bid , so place the ask order.                                                                                                                                             /////// base condition two of recursion
                        self.asks[L_Order.price].append(L_Order)          #  eg. self.bids[211] == [Order]
                        self.orders_by_id[L_Order.order_id] = L_Order
                        return recent_trades
                
            else:  # now bid side is fully over , nothing left , so place the L_Order into ask. // this case is where recursion returns , but when L_Order is still not over , so we updated(placed the remaining L_Order INTO ASK) the book with returning.    /////// base condition three of recursion
                    self.asks[L_Order.price].append(L_Order)          #  eg. self.bids[210] == [Order]
                    self.orders_by_id[L_Order.order_id] = L_Order
                    return recent_trades  # this you , it is imp for returns in recursion calls also...../ you see  , you already updated the book , ask , in recursion.  


            """.
            .
            .
            .
            wait for some time , ...............................................
            .
            .
            .
            .
            .
            ."""


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

                if M_Order.agent_id is not None and order.agent_id is not None: # prevents self matching b/w people , mostly for our agent
                    if M_Order.agent_id == order.agent_id:
                        continue  # move to next order

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

                if M_Order.agent_id is not None and order.agent_id is not None:  # prevents self matching b/w people , mostly for our agent
                    if M_Order.agent_id == order.agent_id:
                        continue  # move to next order

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
                
            agent_id = None # no MPID , hohou!
            order_id_that_was_hit = payload.get("OrderReferenceNumber")


            # ORDER executed was stting on buy side . means /// below... 
            #     side = "SELL" # A sell MAKRET ORDER hits the thing , so we make one, we are making//.
           
            # 1. Check if this order is still in our book 
            if order_id_that_was_hit in self.orders_by_id:
                
                    
                    # 2. Find out what side the *resting* order was
                    resting_order_side = self.orders_by_id[order_id_that_was_hit].side
                    
                    # 3. Create the *opposite* MARKET order that caused this
                    aggressor_side = "SELL" if resting_order_side == "BUY" else "BUY"
                    aggressor_order_id = random.randint(100000000000,999999999999)  # a 12 digit , so different from others....

                    qty = payload.get("ExecutedShares")
                    order = Order(order_id=aggressor_order_id,agent_id=agent_id,type="MARKET",side=aggressor_side,qty=qty,
                                symbol="SPY",price=None,timestamp=timestamp)
                    return order

            else:
                return None # // no order// # do nothing , we are going to ignore the message . and make no market , as we can;t know the side.
               ##  brilliant insight: our agent already filled this!
            


        

# logic for ORDEREXECUTED OR WITH PRICE , IS IN main_sim.py itself__________________________________________________ 1:34AM 06 NOV 25 
# ignore above comment...///




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

