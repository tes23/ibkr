from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
import threading
import time

class IBkrApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.nextOrderId = None
        self.market_data = {}

    def nextValidId(self, orderId):
        """Callback to receive the next valid order ID."""
        self.nextOrderId = orderId
        print(f"Next valid order ID: {self.nextOrderId}")

    def tickPrice(self, reqId, tickType, price, attrib):
        """Callback to receive market data prices."""
        if tickType == 1:  # Bid price
            self.market_data["bid_price"] = price
        elif tickType == 2:  # Ask price
            self.market_data["ask_price"] = price
        elif tickType == 4:  # Last traded price
            self.market_data["last_price"] = price
        print(f"Received tickPrice: reqId={reqId}, tickType={tickType}, price={price}")

    def error(self, reqId, errorCode, errorString, errorTime=None, advancedOrderRejectJson=""):
        """Handle errors from the API."""
        print(f"Error: ReqId={reqId}, Code={errorCode}, Msg={errorString}")

# Function to run the app in a separate thread
def run_loop(app):
    app.run()

# Function to create a stock contract
def create_stock_contract(symbol):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = "STK"
    contract.currency = "USD"
    contract.exchange = "SMART"
    return contract

# Function to create a limit buy order
def create_limit_buy_order(quantity, price):
    order = Order()
    order.action = "BUY"
    order.orderType = "LMT"
    order.totalQuantity = quantity
    order.lmtPrice = price
    return order

if __name__ == "__main__":
    # Initialize the app
    app = IBkrApp()

    # Connect to the IB Gateway or TWS
    app.connect("127.0.0.1", 4001, clientId=3)

    # Start the app in a separate thread
    api_thread = threading.Thread(target=run_loop, args=(app,), daemon=True)
    api_thread.start()

    # Wait for connection and next order ID
    time.sleep(2)

    while True:
        # Get user input for stock and price
        symbol = input("Enter the stock/fund symbol you want to buy: ").strip().upper()

        # Create the contract for the given symbol
        contract = create_stock_contract(symbol)

        # Request market data for the symbol
        app.market_data = {}  # Reset market data
        app.reqMktData(1, contract, "", False, True, [])

        # Wait to gather market data
        time.sleep(5)

        # Display the market data
        # Display the market data
        bid = app.market_data.get("bid_price", "N/A")
        ask = app.market_data.get("ask_price", "N/A")
        last = app.market_data.get("last_price", "N/A")
        print(f"\nMarket Data for {symbol}:")
        print(f"  Last Price: {last}")
        print(f"  Bid Price: {bid}")
        print(f"  Ask Price: {ask}")

        # Confirm if the user wants to continue
        proceed = input("Do you want to continue with the purchase? (y/n): ").strip().lower()
        if proceed != "y":
            break

        max_price = float(input("Enter the maximum price you want to buy at: ").strip())
        quantity = int(input("Enter the quantity to buy: ").strip())

        # Create the limit buy order
        order = create_limit_buy_order(quantity, max_price)

        # Wait until nextOrderId is available
        while app.nextOrderId is None:
            time.sleep(0.1)

        # Place the order
        print(f"Placing order for {symbol}: {quantity} shares at ${max_price} maximum price.")
        app.placeOrder(app.nextOrderId, contract, order)

        # Increment the order ID for the next transaction
        app.nextOrderId += 1

        # Ask if the user wants to make another transaction
        another = input("Do you want to make another transaction? (y/n): ").strip().lower()
        if another != "y":
            break

    # Allow time for final order processing
    time.sleep(5)

    # Disconnect
    app.disconnect()
    print("Disconnected from IBKR.")