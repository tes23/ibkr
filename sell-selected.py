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

    def nextValidId(self, orderId):
        """Callback to receive the next valid order ID."""
        self.nextOrderId = orderId
        print(f"Next valid order ID: {self.nextOrderId}")

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

# Function to create a limit sell order
def create_limit_sell_order(quantity, price):
    order = Order()
    order.action = "SELL"
    order.orderType = "LMT"
    order.totalQuantity = quantity
    order.lmtPrice = price
    return order

if __name__ == "__main__":
    # Initialize the app
    app = IBkrApp()

    # Connect to the IB Gateway or TWS
    app.connect("127.0.0.1", 4001, clientId=2)

    # Start the app in a separate thread
    api_thread = threading.Thread(target=run_loop, args=(app,), daemon=True)
    api_thread.start()

    # Wait for connection and next order ID
    time.sleep(2)

    # Get user input for stock and price
    symbol = input("Enter the stock/fund symbol you want to sell: ").strip().upper()
    min_price = float(input("Enter the minimum price you want to sell at: ").strip())
    quantity = int(input("Enter the quantity to sell: ").strip())

    # Create the contract and order
    contract = create_stock_contract(symbol)
    order = create_limit_sell_order(quantity, min_price)

    # Wait until nextOrderId is available
    while app.nextOrderId is None:
        time.sleep(0.1)

    # Place the order
    print(f"Placing order for {symbol}: {quantity} shares at ${min_price} minimum price.")
    app.placeOrder(app.nextOrderId, contract, order)

    # Allow time for order processing
    time.sleep(5)

    # Disconnect
    app.disconnect()
    print("Disconnected from IBKR.")