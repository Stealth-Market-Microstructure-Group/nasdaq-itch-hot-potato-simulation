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
from matching_engine import OrderBook
from agents import newAgentB
from v2_orderbook.Order_Class import Order
from v2_orderbook.Trade_Class import Trade




# --- 1. SETUP LOGGING TO STDERR (Your setup is PERFECT) ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stderr)
# -----------------------------------------------------------

order_book = OrderBook()
agent_a = newAgentB('A')
agent_b = newAgentB('B')
current_sim_time_ns = 0


MAX_LINES_TO_PROCESS = 10000000000000000000  # Stop after 50,000 lines (adjust as needed)
VISUAL_DELAY_SECONDS = 0  # Pause for 0.1 seconds after each event


logging.info("Simulator alive, reading from 'parsed_itch_data.jsonl'...")

#______________________________________________________________________________________________________________________________________________________


# --- Get the absolute path to the directory this script is in ---
script_dir = os.path.dirname(os.path.abspath(__file__))
# --- Define the file path *relative* to this script ---
data_file_path = os.path.join(script_dir, 'parsed_itch_data.jsonl')


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


            symbol = market_event.get("Symbol")
            timestamp = market_event.get('TimestampUTC')
            event_type = market_event.get('EventType')
            payload = market_event.get('Payload')


            if symbol != "SPY": # // if not same as fixed , ignore the message !
                continue


            if not timestamp:
                continue 
            
            current_sim_time_ns = timestamp



            # --- 3. MARKET DATA LOGIC ---

            market_trades = []

            if event_type == "AddOrder" or event_type == "AddOrderWithMPIDAttribution":
                pass
                # parsed_order = order_book.parse_payload_to_order(payload, event_type, timestamp) 
                # if parsed_order:
                    logging.info(f"MARKET EVENT: {parsed_order}")
                    market_trades = order_book.process_order(parsed_order, current_sim_time_ns)
                    for trade in market_trades:
                        logging.info(f"MARKET TRADE: {trade}")

#                   ///////////////////// 

            elif event_type == "OrderExecuted" or event_type == "OrderExecutedWithPrice":
                order_id = payload.get("OrderReferenceNumber")
                qty = payload.get("ExecutedShares")

                if order_id in order_book.orders_by_id : 
                    order = order_book.orders_by_id[order_id]

                    if qty > order.qty :    # 70 > 10
                        trade = order_book.remove_order(order_id,timestamp)  # trade will suurely occur // both removal manage by .remove inside 
                        logging.info(f"CATCH ME (REMOVED): {trade}")
                        market_trades = [trade]

                        """// here of you are wondoring , what we did is , that as the we wanna fix the logic , when the order , our order
                        that is sitting in the book , is sometimes let's say it was 100 sharres when it was new , but then our agent b , hit and let's
                        consumed 90 shares , now order left with 10 only , but the market doesnot care , the itch data is market events, so it sends
                        the event of past , when a "OrderExecuted" message comes and with of 70 shares , now the magic is to make a trade , so we make
                        trade of the remaining quantity , as the market order (aggreser) is never in itch , so we manipulate and show a trade of only 10
                        shares , not 70. side by side we remove the order from both book and orders_by_id in .remove() method . 
                        Now when the shares of the "OrderExecuted"  MESSAGE ARE LET'S SAY LESS , SO NO PROBLEM . EXECUTE THE TRADE , UPDATE ORDER.
                        NOW WHEN THE shares of "OrderExecuted" is euqal. remove the order AND GENERATE A TRADE
                        """ 

                        # del order_book.orders_by_id[order_id]
                        # if order.side == "BUY":
                        #     trade = Trade(price=order.price,qty=order.qty,buyer_id=order.agent_id,seller_id=None,timestamp=timestamp) # trade qty = 10
                        #     logging.info(f"MARKET EXECUTION (REMOVED): {trade}")                             
                        # elif order.side == "SELL":
                        #     trade = Trade(price=order.price,qty=order.qty,buyer_id=None,seller_id=order.agent_id,timestamp=timestamp) # trade qty = 10
                        #     logging.info(f"MARKET EXECUTION (REMOVED): {trade}")                             
                        
                    elif qty < order.qty :    # 40 < 50             ( lets assume initially it was 100,  / 50 agent consumed)
                        order_book.orders_by_id[order_id].qty = order.qty - qty   #  10 qty   / updated....
                        if order.side == "BUY":
                            trade = Trade(price=order.price,qty = qty,buyer_id=order.agent_id,seller_id=None,timestamp=timestamp) # trade qty = 10
                            logging.info(f"CATCHED ME (REMOVED): {trade}")                             
                            market_trades = [trade]                            
                        elif order.side == "SELL":
                            trade = Trade(price=order.price,qty=qty,buyer_id=None,seller_id=order.agent_id,timestamp=timestamp) # trade qty = 10
                            logging.info(f"CATCH ME (REMOVED): {trade}")                           
                            market_trades = [trade]                            
                        
                    elif qty == order.qty :    # 50 == 50             ( lets assume initially it was 100,  / 50 agent consumed)
                        trade = order_book.remove_order(order_id,timestamp)  # trade will suurely occur // both removal manage by .remove inside 
                        logging.info(f"CATCH ME (REMOVED): {trade}")
                        market_trades = [trade]                            

                    # if order.side == "BUY":
                    #     trade = Trade(price=order.price,qty = qty,buyer_id=order.agent_id,seller_id=None,timestamp=timestamp) # trade qty = 10
                    #     logging.info(f"MARKET EXECUTION (REMOVED): {trade}")                             
                    # elif order.side == "SELL":
                    #     trade = Trade(price=order.price,qty=qty,buyer_id=None,seller_id=order.agent_id,timestamp=timestamp) # trade qty = 10
                    #     logging.info(f"MARKET EXECUTION (REMOVED): {trade}")                           

#                   /////////////////////            


            if market_trades:  # // AGENT INVENTORY UPDATION
                agent_b.update_inventory(market_trades)   
                """you know what , this all ABM was scam ,. becoz your agent can't really get hit by any market order ,
                unitl and unless , you make a agent that is going to trade agaisnt this one agent ,  and there even if you think ,
                becoz in itch data , all the thing we get is orderexecuted messages and there you just do the shit thing of removing that order and 
                showing that a market order hitted him so that's why . now and also what i thought in when back then i was not knowing this , is that 
                you get market orders in the itch messages ittself , and there , what you do is , you can take them and execute with any of the best 
                price that is avaiable at that moment , and there you are having the chance , your agent is having the chance that if he is able to be fast 
                and place a order before the other peopple from data , then he would in front of queue and there he would be then be possible to execute the 
                order of himself and there he is playing like any other market participant , like no speicaility and there you dont need to make another agent 
                just so whenever my agent places a limit order , he dont have to wait for endless period of time , as there is no one coming from data
                that would hit his order , why , becozing this fucking thing is just doing the wrost of i can think , . you know that , it just do process
                the things where orderexecuted messages are just used in a way , you know the logic . this is shit. it doesnot use much of of structure of 
                market order matching fucntions i made putting fucking more effort then anything and mostly it also dont care about queue position anymore , why , 
                let me make you understand , as lets see a liimit order , addorder message comes,  what happens , the thing is going to process order and there
                this process order directs the message accordingly to add_place_limit_order or add_match_market_order , and you know what , the fucking thing is never
                going to use add_match_market_order , as this messages are jusr fucking limit orders , you dont get any market order from this , the fuck history of itch
                , so then what , then just fuck off , becoz then if you get order executed messages , you porces them using the fucking logic of just handling how to 
                print the logs then really manipulating the book like how really a mathing engine works , you just update by removing the order or updating quantity
                but you dont really do the use of match market order fucniton anytime in this fucking thing ,add_match_market_order,.
                so  , so the thing is you just use this fucking add_match_market_order when there is you process the orders of agents only and you know what 
                there also you made this big fucking fucntion add_match_market_order , just for when for a agent only , and when no one from data even need this fucntion 
                and this is shit , really ,. and now what , now you do is just make another fucking agent , which is so good at scripting the whole game before the thing , that he 
                help facilitate the hot potato effect agent b is trying to show , and there , you need to be this agent , new agent which when agent b places a limit sell , he should 
                be also placing the market order in such a way that he hit s ageent b , as otherwise agent b can't get fucking filledd , and then when agent b is short 
                 he decides and places another order in next iteration and which is to buy back , and that would be a market order , and but before that agent A should be placing a 
                 limit sell to make sure he is there to be the person to which agent B hits and , there you know what the order of placing the ORDERS is like this:
                 agent b places a limit sell , agent A places a market buy (and in such way , it consumes the person in front of queue and reaches b also to consume it ) and the 
                 agent A places another order , a limit sell to hedge agianst the order of market buy he did and then finally agent b places a order a market buy and hits to show 
                  hot potato and to get flat and this is clear order : agent b limit sell -> agent A market buy -> agent A limit sell -> agent b market buy .
                  and this is one thing . 
                  after this fucking thing. this task , and the hot potato thing get done . i would make so many massive changes in this whole project this probelm of no market order 
                  from itch data for my agents and i need precise agent who places market orders to get against the first agent to make sure the first agent is able to get his thing get done when he places a limit order 
                  this things needs a permanent solution , so what i am going to do . i woul try to convert the orderexecuted messages into market order , and yes you heared it right , i would take its qty and its side , if it is buy 
                  sell and then make a order object of this type and a random order id and then a everything it needed was just qty and side , if it is nuy or sell and then i will make the use of 
                  my add_match_market_order and make the game fair , and then the porblem will be solved,  i would never need to make another agent to help faciliate that my limit orders
                  of agents get filled . and there everything will just be on logic based and pure orderbook dynamics and no shity things likee the if orderexecuted messaages currelty does .
                  so this is the plan. 
                  

                this fucking logic of if messagetype == orderexecuted or .... that is used , but the fucking fucntions of add_place_limit_order and add_match_market_order
                this both are just so limited . as now when that o
                    """ 



            # --- 4. AGENT LOGIC ---
            agent_orders_to_submit = agent_b.decide_action(
                current_sim_time_ns, 
                order_book.get_best_bid(), 
                order_book.get_best_ask()
            )


            # --- 5. AGENT PROCESSING (Handles list OR single order) ---
            if agent_orders_to_submit:
                
                orders_to_process = []
                if isinstance(agent_orders_to_submit, list):
                    orders_to_process = agent_orders_to_submit
                else:
                    orders_to_process = [agent_orders_to_submit] # Put the single order in a list

                for agent_order in orders_to_process:
                    """" make sure you place the timestamp in agent logic itself to make sure the order of this below processs:
                    agent b limit sell -> agent A market buy -> agent A limit sell -> agent b market buy .,, beomcs right """
                    
                    if agent_order.symbol !="SPY": # // checks symbol
                        continue

                    current_sim_time_ns = current_sim_time_ns + 1   # // advance current_sim time 


                    agent_order.timestamp = current_sim_time_ns   
                    logging.info(f"AGENT ACTION: {agent_order}")
                

                    agent_trades = order_book.process_order(agent_order, current_sim_time_ns)
                    
                    for trade in agent_trades: # // trades happened for each order of agent is logged. 
                        logging.info(f"AGENT TRADE: {trade}")
                    
                    if agent_trades:  # // AGENT INVENTORY UPDATION
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




















# import sys
# import json
# import logging
# from matching_engine import OrderBook
# from agents import newAgentB 



# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',stream=sys.stderr)
# order_book = OrderBook()
# agent_b = newAgentB('B')
# current_sim_time_ns = 0
# # ... (all your imports and setup) ...

# logging.info("Simulator alive, reading from 'parsed_itch_data.jsonl'...")

# #______________________________________________________________________________________________________________________________________________________

# # --- NEW LOOP: Read from the pre-parsed file ---

# try:
#     with open('parsed_itch_data.jsonl', 'r', encoding='utf-8') as f:
#         for line_number, line in enumerate(f):
            
#             clean_line = line.strip()
            
#             # This is the only check you need.
#             if not clean_line:
#                 continue # Skip empty or whitespace-only lines

#             try:
#                 market_event = json.loads(clean_line)
#             except json.JSONDecodeError as json_err:
#                 logging.warning(f"L#{line_number}: Skipping malformed JSON line. Error: {json_err}. Line: '{clean_line}'")
#                 continue
            
#             # --- From here, your code is good ---

#             timestamp = market_event.get('TimestampUTC')
#             event_type = market_event.get('EventType')
#             payload = market_event.get('Payload')

#             if not timestamp:
#                 continue 
            
#             current_sim_time_ns = timestamp


#         #____________________________________________________________________________________________________________________________
#             # -- Market Data Logic first -
#             # 3. Process the historical event from the data feed

#             if event_type == "AddOrder" or event_type== "AddOrderWithMPIDAttribution":
#                 parsed_order = order_book.parse_payload_to_order(payload, event_type, timestamp) # Your parser
#                 if parsed_order:
#                     logging.info(f"{parsed_order}")
#                     trades = order_book.process_order(parsed_order,current_sim_time_ns)
#                     for trade in trades:
#                         logging.info(f"MARKET TRADE: {trade}")

#                     agent_b.update_inventory(trades) # even if no trade , it just checks

#             # just added "OrderExecutedWithPrice" in if condition , chck if needed later . 1:29AM  06 NOV 25..................................................1:30AM 06 NOV 25
#             elif event_type =="OrderExecuted" or event_type =="OrderExecutedWithPrice": # sometimes this order doesnot exist in the book , maybe already consumed by our agent B , so use some mech , i did , see in remove order and here below !!! god luck !
#                 order_id = payload["OrderReferenceNumber"]
#                 trade = order_book.remove_order(order_id,timestamp) # timestamp is imp / .remove() checks inside if this order exist in book , see logic , . if agent did smth ;) 
#                 if trade:
#                     trades = []
#                     trades.append(trade) # to help upate inventory , we do make list "trades"
#                     agent_b.update_inventory(trades)            
#                     logging.info(f"MARKET TRADE: {trade}")
#                 # if trade None , nothing needs to be done..... already may be done , read .remove() 

#         #_____________________________________________________________________________________________________________________________




#         #_____________________________________________________________________________________________________________________________
#             # 4. Let your agent react to the *new* market state
#             #    (e.g., check its own inventory, look at the order book)

#             agent_orders_to_submit = agent_b.decide_action(
#                 current_sim_time_ns, 
#                 order_book.get_best_bid(), 
#                 order_book.get_best_ask()
#             )
#         #_____________________________________________________________________________________________________________________________
#             # 5. Process agent's new orders
#             if agent_orders_to_submit:  # .......................2:13AM 06 NOV 25
#                 for agent_order in agent_orders_to_submit:
#                     logging.info(f"{agent_order}")
#                     agent_order.timestamp = current_sim_time_ns + 1
            
#                     trades = order_book.process_order(agent_order, current_sim_time_ns) # here 
#                     for trade in trades:
#                         logging.info(f"AGENT TRADE: {trade}")
                    
#                     agent_b.update_inventory(trades)
#         # ___________________________________________________________________________________________________________________________
    



#             # ... (Rest of your simulation logic: Market Data, Agent React, Agent Process) ...
#             # ... (Your logic for event_type == "AddOrder" is good)
#             # ... (Your logic for event_type == "OrderExecuted" is good)
#             # ... (Your logic for agent_b.decide_action() is good)
#             # ... (Your logic for processing agent_orders_to_submit is good)

# except FileNotFoundError:
#     logging.critical(f"FATAL: 'parsed_itch_data.jsonl' not found. Make sure it's in the same folder as main_sim_copy.py.")
# except Exception as e:
#     logging.error(f"An uncaught error occurred: {e}", exc_info=True)

















# try:
#     with open('hot_potato_sim/parsed_itch_data.jsonl', 'r') as f:
#         for line in f:
#             try:
#                 clean_line = line.strip() # Still good practice
#                 if not clean_line:
#                     continue
#                 market_event = json.loads(clean_line)
#             except json.JSONDecodeError:
#                 logging.warning(f"Skipping malformed JSON line: {line}")
#                 continue

#             timestamp = market_event.get('TimestampUTC')
#             event_type = market_event.get('EventType')
#             payload = market_event.get('Payload')

#         #------------------------------------------------------------------------------> check here 

#             if not timestamp:
#                 continue # Skip events without time

#             # Advance simulation time...........CHECK THIS , MIGHT BE A FLAW , IF THEN NEEDS TO ADJUST THE AGENT AND OTHER ORDER PROCESSING... UPDATE: CHECK COMPLETE , FLAWS FIXED...................... 1:37AM 06 NOV 25
#             current_sim_time_ns = timestamp


#         #____________________________________________________________________________________________________________________________
#             # -- Market Data Logic first -
#             # 3. Process the historical event from the data feed

#             if event_type == "AddOrder" or event_type== "AddOrderWithMPIDAttribution":
#                 parsed_order = order_book.parse_payload_to_order(payload, event_type, timestamp) # Your parser
#                 if parsed_order:
#                     logging.info(f"{parsed_order}")
#                     trades = order_book.process_order(parsed_order,current_sim_time_ns)
#                     for trade in trades:
#                         logging.info(f"MARKET TRADE: {trade}")

#                     agent_b.update_inventory(trades) # even if no trade , it just checks

#             # just added "OrderExecutedWithPrice" in if condition , chck if needed later . 1:29AM  06 NOV 25..................................................1:30AM 06 NOV 25
#             elif event_type =="OrderExecuted" or event_type =="OrderExecutedWithPrice": # sometimes this order doesnot exist in the book , maybe already consumed by our agent B , so use some mech , i did , see in remove order and here below !!! god luck !
#                 order_id = payload["OrderReferenceNumber"]
#                 trade = order_book.remove_order(order_id,timestamp) # timestamp is imp / .remove() checks inside if this order exist in book , see logic , . if agent did smth ;) 
#                 if trade:
#                     trades = []
#                     trades.append(trade) # to help upate inventory , we do make list "trades"
#                     agent_b.update_inventory(trades)            
#                     logging.info(f"MARKET TRADE: {trade}")
#                 # if trade None , nothing needs to be done..... already may be done , read .remove() 

#         #_____________________________________________________________________________________________________________________________




#         #_____________________________________________________________________________________________________________________________
#             # 4. Let your agent react to the *new* market state
#             #    (e.g., check its own inventory, look at the order book)

#             agent_orders_to_submit = agent_b.decide_action(
#                 current_sim_time_ns, 
#                 order_book.get_best_bid(), 
#                 order_book.get_best_ask()
#             )
#         #_____________________________________________________________________________________________________________________________
#             # 5. Process agent's new orders
#             if agent_orders_to_submit:  # here , agetn rn return a single order , not list of order , so check it .......................2:13AM 06 NOV 25
#                 for agent_order in agent_orders_to_submit:
#                     logging.info(f"{agent_order}")
#                     agent_order.timestamp = current_sim_time_ns + 1
            
#                     trades = order_book.process_order(agent_order, current_sim_time_ns) # here 
#                     for trade in trades:
#                         logging.info(f"AGENT TRADE: {trade}")
                    
#                     agent_b.update_inventory(trades)
#         # ___________________________________________________________________________________________________________________________
    



#             # ... (ALL THE REST OF YOUR SIMULATION LOGIC IS 100% UNCHANGED) ...
#             # ... (parsing timestamp, event_type, payload...)
#             # ... (processing market data first...)
#             # ... (letting agent react...)
#             # ... (processing agent orders...)

# except FileNotFoundError:
#     logging.critical("FATAL: 'parsed_itch_data.jsonl' not found. Did you run the Go parser first?")
# except Exception as e:
#     logging.error(f"An uncaught error occurred: {e}", exc_info=True)

# # --- OLD LOOP (Keep it for later) ---
# # for line in sys.stdin:
# #   ... (all your old logic) ...

# #______________________________________________________________________________________________________________________________________________________

# logging.info("Simulation finished (data stream ended).")