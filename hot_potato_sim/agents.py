import random
from v2_orderbook.Order_Class import Order
from v2_orderbook.Trade_Class import Trade
import logging


class baseagent():
    def __init__(self,id):
        self.id = id 
        self.active_orders = []
        self.trades = []
        self.inventory = 0 
        self.pnl = 0
        self.lim = 1

    def update_inventory(self,last_trade_info):        
        for trade in last_trade_info:
            if self.id == trade.buyer_id :
                self.trades.append(trade)
                self.inventory += trade.qty
    
            elif self.id == trade.seller_id :
                self.trades.append(trade)
                self.inventory -= trade.qty

    
    def update_order_list(self,order):
        self.active_orders.append(order)

    # def calc_pnl(self):

    #     if self.inventory == 0 and self.trades :
    #         for i in range(len(self.trades)):
    #             trdae_1 , trade_1 = self.trades[i] , self.trades[i+1]
    #             trade_1.price * trade_1.qty

        # amt_paid = 0 
        # for trade in self.trades:
        #     amt_paid = trade.price * trade.qty
        #     if self.id == trade.buyer_id:
        #         pnl -= amt_paid
####################################################################################################################################      

class AgentA(baseagent):
    def __init__(self):
        super().__init__('A')
        self.lim = 1
        # self.inventory = 0
        
    def decide_action(self, current_sim_time_ns, best_bid, best_ask, last_trade_info):
        

        if self.inventory == 0 and self.lim == 1:

            self.lim = 0 # put limit

            order_id = random.randint(10000000,99999999)           
            order = Order(order_id=order_id,agent_id=self.id,type='MARKET',side='BUY',qty=1000,symbol='SPY', price=None, timestamp = current_sim_time_ns+3)
            return order
        
        elif self.inventory > 0 and self.lim == 0:

            self.lim = 5 # put limit 

            order_id = random.randint(10000000,99999999)           
            order = Order(order_id,self.id,'MARKET','SELL',1000,'SPY', price=None, timestamp = current_sim_time_ns+8)
            return order
        return None
        # Simple if-then logic based on hotpot.pdf rules
        # If conditions met:
        #    return Order(agent_id='A', type='MARKET', side='BUY', size=100) 
        # Else:
        #    return None

class AgentB(baseagent):
    def __init__(self):
        super().__init__('B')
        self.lim = 1 # limit on how many times it runs
        # self.inventory = 0

    def decide_action(self, current_sim_time_ns, best_bid, best_ask, last_trade_info):
        

        # super().update_state(last_trade_info)

        if self.inventory == 0 and self.lim == 1:

            self.lim = 0 # put limit

            order_id = random.randint(10000000,99999999)         

            order = Order(order_id=order_id,agent_id=self.id,type='LIMIT',side='SELL',
                          qty=1000,symbol='SPY',price=9.11,timestamp=current_sim_time_ns+1)
            
            return order
        elif self.inventory < 0 and self.lim == 0:
            
            self.lim = 5 # put limit 

            order_id = random.randint(10000000,99999999)
            return Order(order_id=order_id,agent_id=self.id,type='MARKET',side='BUY',
                         qty=abs(self.inventory), symbol= 'SPY', price = None, timestamp = current_sim_time_ns+7)
        return None

class AgentC(baseagent):
    def __init__(self):
        super().__init__('C')
        self.lim = 1

    def decide_action(self, current_sim_time_ns, best_bid, best_ask, last_trade_info):
       

        # super().update_state(last_trade_info)

        if self.inventory == 0 and self.lim == 1:

            self.lim = 0 # put limit

            order_id = random.randint(10000000,99999999)           
            order = Order(order_id=order_id,agent_id=self.id,type='MARKET',side='SELL',qty=1000,symbol='SPY',price=None,timestamp= current_sim_time_ns+4)
            return order
        
        elif self.inventory < 0 and self.lim == 0 :

            self.lim = 5 # put limit 

            order_id = random.randint(10000000,99999999)
            return Order(order_id=order_id,agent_id=self.id,type='LIMIT',side='BUY',qty=abs(self.inventory) ,symbol='SPY',price = 9.10, timestamp= current_sim_time_ns+6)
        return None
         # etc. for C, D
    # ... similar structure ...

class AgentD(baseagent):
    def __init__(self):
        super().__init__('D')
        self.lim = 1
    

    def decide_action(self, current_sim_time_ns, best_bid, best_ask, last_trade_info):
    
        # if last_trade_info:
        #     super().update_state(last_trade_info)


        if self.inventory == 0 and self.lim == 1:

            self.lim = 0 # put limit 

            order_id = random.randint(10000000,99999999)           
            order = Order(order_id=order_id,agent_id=self.id,type='LIMIT',side='BUY',qty=1000,symbol='SPY',price=9.10,timestamp=current_sim_time_ns+2)
            return order
        
        elif self.inventory > 0 and self.lim == 0:
            
            self.lim = 5 # put limit 

            order_id = random.randint(10000000,99999999)           
            order = Order(order_id=order_id,agent_id=self.id,type='LIMIT',side='SELL',qty=1000,symbol='SPY',price=9.11,timestamp=current_sim_time_ns+5)
            return order
        return None


# --- In agents.py ---


class newAgentB(baseagent):
    def __init__(self, id):
        super().__init__(id)
        # --- The Agent's State ---
        self.state = "LOOKING_TO_SELL" 
        self.my_passive_order_id = None # Track our own order
        self.our_price = None  # to track last order's placing price
        self.prev_filled_price = None # to track last trade's fill price

    def decide_action(self, current_sim_time_ns, best_bid, best_ask):
        

        if self.state == "LOOKING_TO_SELL":

            if best_ask is not None:
                order_id = random.randint(100000000000, 999999999999)
                price = best_ask 
                self.our_price = price # so as to use this later for placing more orders _______________________ 2:29AM 06 NOV 25
                qty = 107
                order = Order(order_id=order_id, agent_id=self.id, type='LIMIT', side='SELL',
                              qty=qty, symbol='SPY', price=price, timestamp=None) # Timestamp set by main loop
                
                self.my_passive_order_id = order_id  # order_id to track your order !! 
                self.state = "WAITING_FOR_FILL" # <-- CHANGE STATE
                # logging.info(f"Agent B ({self.state}): Placing passive sell {order_id} @ {price}")
                return [order] # Return as a list
            
        
        if self.state == "WAITING_FOR_FILL":
            # How do we know we're filled? The main loop calls update_inventory.
            if self.inventory < 0:
                # We got filled!
                # logging.info(f"Agent B: FILL DETECTED! Inventory is {self.inventory}. Moving to hot potato.")
                self.state = "LOOKING_TO_BUY_BACK" # <-- CHANGE STATE

                self.prev_filled_price = self.our_price
                self.my_passive_order_id = None
        

        if best_ask is not None and self.our_price is not None and self.my_passive_order_id is not None:
                
            if abs(self.our_price - best_ask) > 0.02 and self.state == "WAITING_FOR_FILL":   # every time it checks and whenever it finds it True , it cancels existing order and place new order
                order_id_to_cancel = self.my_passive_order_id  # save the order_id of previous order , which we need to cancel !!

                order_id = random.randint(100000000000, 999999999999)
                qty = 107
                order = Order(order_id=order_id, agent_id=self.id, type='LIMIT', side='SELL',
                                qty=qty, symbol='SPY', price=best_ask, timestamp=None)
                
                self.our_price = order.price  # update price
                self.my_passive_order_id = order.order_id # updated to track last order , so to cancel it , next time , when needed !!
                self.state = "WAITING_FOR_FILL"# update state
                
                return [order_id_to_cancel , order] # order_id is "int" /// and we return a order_cancel and a add order 
                


            # elif self.inventory == 0 and best_ask > self.our_price................................................. 2:31AM 06 NOV 25

            # Add more logic: What if the price moves away?
            # elif best_ask > (our_price + 0.05):
            #     # Price is moving up, cancel our order
            #     logging.info("Agent B: Price moved, cancelling order")
            #     self.state = "LOOKING_TO_SELL"
            #     return [CancelOrder(self.my_passive_order_id)] # (Need a CancelOrder object)


        
        # elif self.state == "LOOKING_TO_BUY_BACK" and best_ask == self.prev_filled_price:
        if self.state == "LOOKING_TO_BUY_BACK":
            # Logic: Immediately send a market order to flatten our position
            order_id = random.randint(100000000000, 999999999999)
            qty_to_buy = abs(self.inventory)
            order = Order(order_id=order_id, agent_id=self.id, type='MARKET', side='BUY',
                          qty=qty_to_buy, symbol='SPY', price=None, timestamp=None)
            
            self.our_price = order.price
            self.state = "IDLE" 
            logging.info(f"Agent B ({self.state}): Executing HOT POTATO. Market buying {qty_to_buy}.")  # COMMENT IT LATER 
            return [order]

        
        elif self.state == "IDLE":
            pass # Wait for some condition to reset

        return [] # Return an empty list if no action











##################################################################################

# ////   update inventory is already defined in baseagent ///// ///// //// //// ///// ////////////////////////////////


# class newAgentB(baseagent):
#     def __init__(self):
#         super().__init__('B')

#     def decide_action(self, current_sim_time_ns, best_bid, best_ask):
        
#         time = current_sim_time_ns
#         threshold = 658006594  # random value 

#         if time < threshold:
#             if self.inventory == 0 and self.lim == 1:
                
#                 self.lim = 0 # put limit 

#                 order_id = random.randint(100,999)           
#                 order = Order(order_id=order_id,agent_id=self.id,type='LIMIT',side='SELL',qty=500,symbol='SPY',
#                               price=best_ask,timestamp=current_sim_time_ns+1)
                
#                 return order
            
#             elif self.inventory < 0 and self.lim == 0:

#                 self.lim = 5
#                 order_id = random.randint(100,999)           
#                 order = Order(order_id=order_id,agent_id=self.id,type='MARKET',side='BUY',qty=500,symbol='SPY',
#                               price=None,timestamp=current_sim_time_ns+1)
                
#                 return order



#         return None    

    