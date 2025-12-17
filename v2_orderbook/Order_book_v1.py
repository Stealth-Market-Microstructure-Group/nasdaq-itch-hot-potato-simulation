class OrderBook:                                   # v1 of order book
    def __init__(self):
        self.buy_orders = []
        self.sell_orders = []

    def __repr__(self):
        return f' BUY Orders -> {self.buy_orders}  SELL Orders -> {self.sell_orders} '    

    
    def add_limit_order(self,Order):
        
        if Order.side == 'BUY':                    # BUY  <- TYPE
            self.buy_orders.append(Order)
        
        else :                                     # SELL <- TYPE
            self.sell_orders.append(Order)     


''''''


import matching_engine.v2_orderbook.Order_Class as Order_Class

odr1= Order_Class.Order('O12','1XYZ',210,10,'LIMIT','BUY','2025-07-15 12:00 IST')

Odr_book = OrderBook()

Odr_book.add_limit_order(odr1)

print(Odr_book)



#  order = qty , buy/sell -> market order   