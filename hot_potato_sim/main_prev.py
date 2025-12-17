import time

"""
# --- File: order_book.py ---
# Contains existing OrderBook class with efficient data structures
# Methods: add_order, cancel_order, get_best_bid, get_best_ask, get_book_snapshot, etc.
# Importantly: Matching methods should return a list of Trade objects generated.
"""


import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logging.info("Logging configured. Simulation starting...")


import sys
import os

# Get the path to the current file's directory (e.g., .../hot_potato_sim)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the path to the parent directory (e.g., .../Research hot potato test sim)
parent_dir = os.path.dirname(current_dir)

# Add the parent directory to Python's list of places to look for modules
sys.path.append(parent_dir)

# --- Now your imports will work ---
# from v2_orderbook.Trade_Class import Trade
# ... other imports ...


# --- File: main_simulator.py (The Engine) ---

import heapq # For the unified event queue
import logging 
from matching_engine import OrderBook  # check this later .........
# from order_types import Order, Trade # Your classes
from agents import AgentA, AgentB, AgentC, AgentD
from v2_orderbook.Order_Class import Order
from v2_orderbook.Trade_Class import Trade

# --- Configuration ---
# (Kafka details, logging setup as before)

# --- Initialization ---
order_book = OrderBook()

# maps agents with there agent_id

agents = {'B': AgentB(), 'D': AgentD() ,'C': AgentC(),'A': AgentA() }  # objects created and mapped with id

current_sim_time_ns = 0 # Start time
event_queue = [] # This is the Unified Event Queue: stores (timestamp, event_object) tuples
# heapq requires tuples where the first element is the sort key (timestamp)

# --- (Optional) Pre-fill book ---
# initial_orders = [...] # Define some starting limit orders
# for order in initial_orders:
#    add_event(order.timestamp, order) # Function to add events to heapq

# --- Function to Add Events to Queue (Ensures Order) ---


import itertools
counter = itertools.count()  # global counter

def add_event(timestamp, event):
    # defensive: skip / normalize None timestamps so heap never gets (None, ..., ...)
    if timestamp is None:
        logging.warning(f"Skipping event with None timestamp: {getattr(event, 'order_id', getattr(event, 'id', event))}")
        return
    # accept only numeric timestamps
    if not isinstance(timestamp, (int, float)):
        logging.warning(f"Non-numeric timestamp {timestamp!r} for event {event}; skipping")
        return
    heapq.heappush(event_queue, (timestamp, next(counter), event))


# def add_event(timestamp, event):
#     heapq.heappush(event_queue, (timestamp, next(counter), event))


"""
# --- Kafka Consumer Setup (If running Mode 1 or Mode 2 with Market Data) ---
# consumer = KafkaConsumer(...) 
# Start a separate thread or use async programming to continuously pull 
# messages from Kafka and call add_event(message_timestamp, parsed_order_object)
# For the TOY MODEL, you might skip Kafka and just pre-populate the queue or generate events procedurally.

# --- Agent Action Request Handling (If running Mode 2) ---
# This part handles orders coming *from* your agents
# Simplest for toy model: Directly call agent logic in the main loop.
# Advanced (Phase 4): Use Flask/API. Agent sends HTTP request -> API handler calls add_event(assigned_timestamp, agent_order)
"""




MAX_STEPS = 10000  # or whatever
step = 0

# --- The Main Event Loop ------------------------------------------------------------------------
logging.info("Starting simulation loop...")
while step < MAX_STEPS: # for a do while loop 
    step += 1
    current_event = None # so when event queue is empty ,it is just dont run the processing ,and directly agent placxes nxt order
    
    trades_generated = []
    
    # 1. Get the absolute next event in time
    if event_queue:
        timestamp, _, current_event = heapq.heappop(event_queue)
 
    
    # 2. Advance Simulation Time ,mostly ignore this condition for now , not much , till agent not braining !
    if current_event:    
        if timestamp < current_sim_time_ns:
            logging.warning(f"Out-of-order event skipped: {timestamp} < {current_sim_time_ns}")
            continue

        current_sim_time_ns = timestamp # sim time updated.
        logging.debug(f"--- Processing event | time {current_sim_time_ns} ---")



        # 3. Process the Event using OrderBook
        if isinstance(current_event, Order): # Check if it's an Order object
            order = current_event
            logging.info(f"Received Order: {order} from agent {order.agent_id}")

            if order.type == 'LIMIT':
                trades_generated = order_book.add_place_limit_order(order, current_sim_time_ns) 
            elif order.type == 'MARKET':
                trades_generated = order_book.add_match_market_order(order, current_sim_time_ns)
            # Add elif for Cancel, Modify - calling appropriate order_book methods
            

        # def update_state(self,last_trade_info):        
        #     for trade in last_trade_info:
        #         if self.id == trade.buyer_id :
        #             self.trades.append(trade)
        #             self.inventory += trade.qty
        
        #         elif self.id == trade.seller_id :
        #             self.trades.append(trade)
        #             self.inventory -= trade.qty


            # Log generated trades
            time.sleep(1)
            if trades_generated:    
                for trade in trades_generated:
                    logging.info(f"TRADE EXECUTED: {trade}")

                    if trade.buyer_id in agents:
                        agents[trade.buyer_id].inventory += trade.qty
                        agents[trade.buyer_id].trades.append(trade)
                    if trade.seller_id in agents:
                        agents[trade.seller_id].inventory -= trade.qty
                        agents[trade.seller_id].trades.append(trade)

                    time.sleep(1)
                    logging.info(f" {trade.buyer_id} net : {agents[trade.buyer_id].inventory} | {trade.seller_id} net : {agents[trade.seller_id].inventory}")

    #inventory done !! 
                """ this take big assumption that trade occurs b/w agents present in the agents dict 
                otherwise you cant access other buyer or seller 
                and upddate there inventory which would be wrong then"""
                # Update inventories of agents involved in the trade (using trade.buyer_agent_id, etc.)
                # agents[trade.buyer_agent_id].inventory += trade.qty 
                # agents[trade.seller_agent_id].inventory -= trade.qty

        # --- (Agent Reaction Logic - Integrated Here for Toy Model) ---
    
    

        # 4. Get current market state AFTER processing the event
    best_bid = order_book.get_best_bid() # Implement these methods , i did that ! 
    best_ask = order_book.get_best_ask()

    # 5. Let agents react to the new state
    for agent_id, agent in agents.items():
        # Pass relevant info (sim time, book state, maybe last trade info)
        new_action = agent.decide_action(current_sim_time_ns, best_bid, best_ask, trades_generated) # Pass None or trade info
        
        if new_action and isinstance(new_action.timestamp, (int, float)):
            add_event(new_action.timestamp, new_action)
        else:
            logging.debug(f"No valid action for agent {agent_id}")

        # if new_action: # If agent decided to place an order

        #     timestamp = new_action.timestamp
        #     logging.debug(f"Agent {agent_id} decides to act: {new_action}")

        #     # Assign timestamp slightly after current event, add to queue
        #     add_event( timestamp, new_action) # +1 ns, simplified




    if event_queue == [] :
        # time.sleep(1)
        # logging.info(f"A pnl : {} | B pnl : {} | C pnl : {} | D pnl : {} ")
        break    

    time.sleep(1)



time.sleep(1)

# --- End of Simulation ---
logging.info("Simulation finished.")
# (Analyze final agent inventories, trades list in order_book.trades, etc.)
