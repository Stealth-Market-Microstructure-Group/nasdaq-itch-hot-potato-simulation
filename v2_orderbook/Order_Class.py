from datetime import datetime, timezone

from zoneinfo import ZoneInfo

class Order:
    def __init__(self ,order_id ,agent_id ,type ,side ,qty,symbol,price=None,timestamp = None):  # thinking of making 
        
        self.order_id = order_id
        self.agent_id = agent_id
        self.price = price
        self.qty = qty
        self.type = type  # LIMIT / MARKET type
        self.side = side  # BUY / SELL
        self.timestamp = timestamp # in ns (int)
        self.symbol = symbol
        self.order_status = 'Pending'

    # self refers the particluar instance of class...! 
    # def __repr__(self):
    #     # return f"[{self.timestamp}] {self.type} {self.side} {self.qty} of {self.symbol} @ {self.price} ORDER ID=({self.order_id})"
    #     if self.side =="BUY":
    #         return f"[{self.timestamp}] {self.type} BUY @ {self.price}   |  qty = {self.qty}     |  ORDER ID=({self.order_id})"
    #     if self.side =="SELL":
    #         return f"[{self.timestamp}] {self.type} SELL @ {self.price}  |  qty = {self.qty}     |  ORDER ID=({self.order_id})"


    def __repr__(self):
        price_str = f"{self.price:>7.2f}" if self.price is not None else " MKT   "
        return (
            f"[{self.timestamp}] "
            f"{self.type:<6} {self.side:<4} @ {price_str}  |  "
            f"qty = {self.qty:<5} |  "
            f"ORDER ID=({self.order_id})"
        )


    def show_order_info(self):
        print(self)     

''''''


# odr = Order('O1','1XYZ','LIMIT','BUY',10,210)

# # checking if it works 

# odr.show_order_info()

# # first task finished !

# print(odr.timestamp)






# Ignore now
# Understand this , Later !!

'''
def __repr__(self):
    return f"[{self.order_type}] {self.side} {self.qty} @ {self.price} by Agent {self.agent_id} (Status: {self.order_status})

'''