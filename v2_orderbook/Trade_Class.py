from datetime import datetime , timezone

class Trade:
    def __init__(self,price,qty,buyer_id,seller_id,timestamp):
        # self.trade_id = trade_id
        self.price = price
        self.qty = qty
        self.buyer_id = buyer_id
        self.seller_id = seller_id
        self.timestamp = timestamp # in ns
    
    def __repr__(self):
        price_str = f"{self.price:.2f}" if self.price is not None else "N/A"
        buyer_str = self.buyer_id if self.buyer_id is not None else "UNKNOWN"
        seller_str = self.seller_id if self.seller_id is not None else "UNKNOWN"

        return (
            f"[{self.timestamp}] "
            f"TRADE EXECUTED  @  {price_str:>7}  |  "
            f"qty = {self.qty:<5}  |  "
            f"MPIDs: {buyer_str:<8} ↔ {seller_str:<8}"
        )


    def show_trade_info(self):
        print(f"Trade {self.trade_id} executed at $ {self.exec_price} of quantity {self.traded_qty} shares made by buyer {self.buyer_id} and seller {self.seller_id} at {self.timestamp}")     

''''''

# trd_1 = Trade('1231',210,15,'1xyZ','trader_13',datetime.now(timezone.utc))

# print(trd_1)

