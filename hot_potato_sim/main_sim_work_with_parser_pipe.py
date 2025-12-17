import sys
import json
import logging
from matching_engine import OrderBook
from agents import newAgentB 



logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',stream=sys.stderr)
order_book = OrderBook()
agent_b = newAgentB('B')
current_sim_time_ns = 0


logging.info("Simulator alive, waiting for data from STDIN...")

#______________________________________________________________________________________________________________________________________________________

for line in sys.stdin:
    try:
        clean_line = line.strip() 
        if not clean_line: # Skip empty lines
            continue
        market_event = json.loads(clean_line)
    except json.JSONDecodeError:
        logging.warning(f"Skipping malformed JSON line: {clean_line}")
        continue

    

    timestamp = market_event.get('TimestampUTC')
    event_type = market_event.get('EventType')
    payload = market_event.get('Payload')

#------------------------------------------------------------------------------> check here 

    if not timestamp:
        continue # Skip events without time

    # Advance simulation time...........CHECK THIS , MIGHT BE A FLAW , IF THEN NEEDS TO ADJUST THE AGENT AND OTHER ORDER PROCESSING... UPDATE: CHECK COMPLETE , FLAWS FIXED...................... 1:37AM 06 NOV 25
    current_sim_time_ns = timestamp


#____________________________________________________________________________________________________________________________
    # -- Market Data Logic first -
    # 3. Process the historical event from the data feed

    if event_type == "AddOrder" or event_type== "AddOrderWithMPIDAttribution":
        parsed_order = order_book.parse_payload_to_order(payload, event_type, timestamp) # Your parser
        if parsed_order:
            logging.info(f"{parsed_order}")
            trades = order_book.process_order(parsed_order,current_sim_time_ns)
            for trade in trades:
                logging.info(f"MARKET TRADE: {trade}")

            agent_b.update_inventory(trades) # even if no trade , it just checks

    # just added "OrderExecutedWithPrice" in if condition , chck if needed later . 1:29AM  06 NOV 25..................................................1:30AM 06 NOV 25
    elif event_type =="OrderExecuted" or event_type =="OrderExecutedWithPrice": # sometimes this order doesnot exist in the book , maybe already consumed by our agent B , so use some mech , i did , see in remove order and here below !!! god luck !
        order_id = payload["OrderReferenceNumber"]
        trade = order_book.remove_order(order_id,timestamp) # timestamp is imp / .remove() checks inside if this order exist in book , see logic , . if agent did smth ;) 
        if trade:
            trades = []
            trades.append(trade) # to help upate inventory , we do make list "trades"
            agent_b.update_inventory(trades)            
            logging.info(f"MARKET TRADE: {trade}")
        # if trade None , nothing needs to be done..... already may be done , read .remove() 

#_____________________________________________________________________________________________________________________________




#_____________________________________________________________________________________________________________________________
    # 4. Let your agent react to the *new* market state
    #    (e.g., check its own inventory, look at the order book)

    agent_orders_to_submit = agent_b.decide_action(
        current_sim_time_ns, 
        order_book.get_best_bid(), 
        order_book.get_best_ask()
    )
#_____________________________________________________________________________________________________________________________
    # 5. Process agent's new orders
    if agent_orders_to_submit:  # here , agetn rn return a single order , not list of order , so check it .......................2:13AM 06 NOV 25
        for agent_order in agent_orders_to_submit:
            logging.info(f"{agent_order}")
            agent_order.timestamp = current_sim_time_ns + 1
    
            trades = order_book.process_order(agent_order, current_sim_time_ns) # here 
            for trade in trades:
                logging.info(f"AGENT TRADE: {trade}")
            
            agent_b.update_inventory(trades)
 # ___________________________________________________________________________________________________________________________



logging.info("Simulation finished (data stream ended).")
