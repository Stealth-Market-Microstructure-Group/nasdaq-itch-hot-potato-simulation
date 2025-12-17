import random 
import time
import sys
import os


# Get the path to the current file's directory (e.g., .../hot_potato_sim)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the path to the parent directory (e.g., .../Research hot potato test sim)
parent_dir = os.path.dirname(current_dir)

# Add the parent directory to Python's list of places to look for modules
sys.path.append(parent_dir)



import json
import logging
from hot_potato_sim.new_matching_engine_V7 import OrderBook  # fixed  
from agents import newAgentB
from v2_orderbook.Order_Class import Order
from v2_orderbook.Trade_Class import Trade




# --- 1. SETUP LOGGING TO STDERR (Your setup is PERFECT) ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stderr)
# -----------------------------------------------------------

# ///////////////////////////////////////

# # Separate logger for best bid/ask snapshots
# best_logger = logging.getLogger("best_bid_ask_logger")
# best_logger.setLevel(logging.INFO)

# # 'a' = append mode (keeps all history)
# # 'w' = overwrite each run (starts clean each time)
# file_handler = logging.FileHandler("best_bid_ask_snapshots.log", mode='w')

# file_formatter = logging.Formatter('%(asctime)s | BEST_BID=%(message)s')
# file_handler.setFormatter(file_formatter)

# best_logger.addHandler(file_handler)

# best_logger.propagate = False  # ← prevents file logs from showing up in terminal

# ////////////////////////////////////////
best_logger = logging.getLogger("best_bid_ask_logger")
best_logger.setLevel(logging.INFO)
file_handler = logging.FileHandler("best_bid_ask_history.log", mode='a')
file_formatter = logging.Formatter('%(asctime)s | %(message)s')
file_handler.setFormatter(file_formatter)
best_logger.addHandler(file_handler)
best_logger.propagate = False



order_book = OrderBook()
agent_a = newAgentB('A')  # most likey we are not going to use this ....
agent_b = newAgentB('AgentB')
current_sim_time_ns = 0


MAX_LINES_TO_PROCESS = 50000  # Stop after 50,000 lines (adjust as needed)
VISUAL_DELAY_SECONDS = 0.2   # Pause for 0.1 seconds after each event


logging.info("Simulator alive, reading from 'spy_data.jsonl'...")

#______________________________________________________________________________________________________________________________________________________




# ///////////////////////////////////
script_dir = os.path.dirname(os.path.abspath(__file__))
live_log_path = os.path.join(script_dir, "best_bid_ask_live.log")


def log_best_bid_ask_to_file():
    data = order_book.get_best_price_and_qtys()
    with open("best_bid_ask_live.log", "w") as f:  # ← append mode like original
        if data:
            best_bid, bid_qty, best_ask, ask_qty = data
            f.write(
                f"BEST ASK: {best_ask:>8}  --  {ask_qty} shares\n"
                f"BEST BID: {best_bid:>8}  --  {bid_qty} shares\n"
                f"{'-'*35}\n"
            )
        else:
            f.write("BOOK EMPTY\n")



# def log_best_bid_ask_to_file():
#     data = order_book.get_best_price_and_qtys()
#     with open(live_log_path, "w", buffering=1) as f:  # overwrite + line-buffered
#         if data:
#             best_bid, bid_qty, best_ask, ask_qty = data
#             f.write(
#                 f"BEST ASK: {best_ask:>8}  --  {ask_qty} shares\n"
#                 f"{'-'*35}\n"
#                 f"BEST BID: {best_bid:>8}  --  {bid_qty} shares\n"
#             )
#         else:
#             f.write("BOOK EMPTY\n")

#         #  ensure immediate update on disk
#         f.flush()
#         os.fsync(f.fileno())

# """
# write :
# cd "C:/Users/p7379/OneDrive/Documents/SMMG/NOV 2025  .  HOT POTATO IN ITCH/HOT POTATO ITCH . AGENT TEST/Research hot potato sim ITCH/hot_potato_sim"
# $OutputEncoding = [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
# Get-Content "C:/Users/p7379/OneDrive/Documents/SMMG/NOV 2025  .  HOT POTATO IN ITCH/HOT POTATO ITCH . AGENT TEST/Research hot potato sim ITCH/hot_potato_sim/best_bid_ask_live.log" -Wait -Tail 0

# in first terminal , to see clean bid ask........2:44am 9 NOV 25
# """




    # container = order_book.get_best_price_and_qtys()
    # if container:
    #     best_bid , bid_qty , best_ask , ask_qty = container
    #     best_logger.info(f"BEST_BID: {best_bid} QTY: ({bid_qty})  |  BEST_ASK: {best_ask} QTY: ({ask_qty})")
    # else:
    #     best_logger.info("BOOK EMPTY (no bid/ask)")

    # # --- Force immediate disk write ---
    # for handler in best_logger.handlers:
    #     handler.flush()

# //////////////////////////////////




# --- Get the absolute path to the directory this script is in ---
script_dir = os.path.dirname(os.path.abspath(__file__))
# --- Define the file path *relative* to this script ---
data_file_path = os.path.join(script_dir, 'spy_data.jsonl') # this is whre to put name of file. jsonl///

try:
    logging.info(f"Attempting to open file at: {data_file_path}")
    with open(data_file_path, 'r', encoding='utf-16-le') as f:
    # -------------------------------------------
        for line_number, line in enumerate(f):  

            # --- 3. NEW: STOP SIGN ---
            
            if line_number > MAX_LINES_TO_PROCESS:
                logging.info(f"Reached max lines ({MAX_LINES_TO_PROCESS}). Stopping simulation.")
                break # <-- This is your clean exit
            
            # ---------------------------
             
          
            clean_line = line.strip()
            
            if not clean_line:
                continue # Skip empty or whitespace-only lines

            try:
                market_event = json.loads(clean_line)
            except json.JSONDecodeError as json_err:
                # This log will now be accurate
                logging.warning(f"L#{line_number}: Skipping malformed JSON. Error: {json_err}. Line: '{clean_line}'")
                continue
            
            # /// From here, your simulation logic is good ///


            # symbol = market_event.get("Symbol")
            timestamp = market_event.get('TimestampUTC')
            event_type = market_event.get('EventType')
            payload = market_event.get('Payload')


            # if symbol != "SPY": # // if not same as fixed , ignore the message !
            #     continue


            if not timestamp:
                continue 
            
            current_sim_time_ns = timestamp



            # --- 3. MARKET DATA LOGIC ---

            trades = []

            if event_type == "AddOrder" or event_type == "AddOrderWithMPIDAttribution":  #here orders are alwyas LIMIT , YOU KNOW THAT. SE MESSGE TYPE
                parsed_order = order_book.parse_payload_to_order(payload, event_type, timestamp) 
                if parsed_order:
                    logging.info(f"EVENT: {parsed_order}")
                    log_best_bid_ask_to_file()
                    trades = order_book.process_order(parsed_order, current_sim_time_ns)
                    for trade in trades:
                        logging.info(f"LIMIT TRADE: {trade}")  # LIMIT TRADE MEANS INCOMING NEW LIMIT ORDER MATCHS TO SITTING LIMIT ORDER ON BOOK . 
                        log_best_bid_ask_to_file() # this fucntion logs the thing into another seperate file .......................................................//1:36am 9 NOV 25

#                   ///////////////////// 

            elif event_type == "OrderExecuted" or event_type == "OrderExecutedWithPrice":
                
                order = order_book.parse_payload_to_order(payload,event_type,timestamp)  # gives a MARKET BUY/SELL accordingly...
                
                if order is not None:
                    logging.info(f"EVENT: {order}")
                    log_best_bid_ask_to_file()  # ......................................................................................// 1:36am 9 NOV 25

                    if order.side == "BUY":
                        aggressor = "BUYER"
                    elif order.side == "SELL":
                        aggressor = "SELLER"    


                    if order:       # if some order is constructed fromb the book.
                        trades = order_book.process_order(order,sim_time=current_sim_time_ns) 

                    if trades:
                        for trade in trades:
                            logging.info(f"MARKET TRADE: Aggresor : {aggressor} . {trade}")  # MARKET TRADE MEANS MARKET ORDER HITS AND THEN TRADE OCCUR / NOT LIKE LIMIT-LIMIT MATCH
                            log_best_bid_ask_to_file()  # .......................................................................................................................// 1:37am 9 NOV 25


#                   /////////////////////            


            if trades:  # // AGENT INVENTORY UPDATION
                agent_b.update_inventory(trades)   
                
# Design rationale documented in docs DESIGN/market_order_handling.md

# (a desgin comment was there previously , check design doc there to see the idea .......)


            # /// 4. AGENT LOGIC ///
            agent_orders_to_submit_or_remove = agent_b.decide_action(
                current_sim_time_ns, 
                order_book.get_best_bid(), 
                order_book.get_best_ask()
            )


            # /// 5. AGENT PROCESSING (Handles list OR single order) ///

            orders_to_process = []


            if agent_orders_to_submit_or_remove: # it is a list havving , sometimes two action /. remove order/ placeorder both for agent
                for x in agent_orders_to_submit_or_remove:
                    if isinstance(x,int):
                        current_sim_time_ns = current_sim_time_ns + 1
                        logging.info(f"AGENT ACTION: [{current_sim_time_ns}] CANCEL ORDER ({x})")
                        log_best_bid_ask_to_file()  # .................................................................................................................................// 1:38am 9 NOV 25
                        order_book.remove_order(x,current_sim_time_ns)  # order removed , confirm!!!
                    if isinstance(x,Order):
                        orders_to_process.append(x)  # append the orders to process

                if orders_to_process:
                        
                    for agent_order in orders_to_process:

                        current_sim_time_ns = current_sim_time_ns + 1
                        
                        agent_order.timestamp = current_sim_time_ns  

                        logging.info(f"AGENT ACTION: {agent_order}")
                        log_best_bid_ask_to_file()  # .................................................................................................................................// 1:39am 9 NOV 25

                        """" make sure you place the timestamp in agent logic itself to make sure the order of this below processs:
                        agent b limit sell -> agent A market buy -> agent A limit sell -> agent b market buy .,, beomcs right """
                        
                        # if agent_order.symbol !="SPY": # // checks symbol
                        #     continue
                         

                        agent_trades = order_book.process_order(agent_order, sim_time = current_sim_time_ns)
                        
                        if agent_order.type == "MARKET":

                            if agent_order.side == "BUY":
                                aggressor = "BUYER"
                            elif agent_order.side == "SELL":
                                aggressor = "SELLER"

                            for trade in agent_trades: # // trades happened for each order of agent is logged.
                                logging.info(f"AGENT MARKET TRADE: Aggresor : {aggressor} {trade}")  # AGENT TRADE MEANS AGENT IS HAVING TRADE WITH EITHER ORDERS IN/FROM ITCH OR WITH ANOTHER AGENT ./ BUT IN CURRENT RUN THERE IS NO AGENT , SO IT IS WITH ITCH/.
                                log_best_bid_ask_to_file()  # .................................................................................................................................// 1:39am 9 NOV 25 
                            
                        elif agent_order.type == "LIMIT":
                            for trade in agent_trades: # // trades happened for each order of agent is logged. 
                                logging.info(f"AGENT LIMIT TRADE: {trade}")  # AGENT TRADE MEANS AGENT IS HAVING TRADE WITH EITHER ORDERS IN/FROM ITCH OR WITH ANOTHER AGENT ./ BUT IN CURRENT RUN THERE IS NO AGENT , SO IT IS WITH ITCH/.
                                log_best_bid_ask_to_file()  # .................................................................................................................................// 1:40am 9 NOV 25
                            
                        if agent_trades:
                            agent_b.update_inventory(agent_trades)

 

            if VISUAL_DELAY_SECONDS > 0:
                time.sleep(VISUAL_DELAY_SECONDS)


#                     ///////////////


except FileNotFoundError:
    logging.critical(f"FATAL: 'parsed_itch_data.jsonl' not found. Make sure it's in the SAME folder as main_sim_copy.py.")
except KeyboardInterrupt:
    logging.info("...Simulation stopped by user (Ctrl+C).")    
except Exception as e:
    logging.error(f"An uncaught error occurred: {e}", exc_info=True)

#______________________________________________________________________________________________________________________________________________________

logging.info("Simulation finished (data stream ended).")

