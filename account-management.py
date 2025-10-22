from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.common import *
from ibapi.contract import Contract
from ibapi.order import Order
import threading
import time
from tabulate import tabulate

class IBkrApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.account_summary = []
        self.nextOrderId = None
        self.market_data = {}
        self.accounts = []

    def managedAccounts(self, accountsList: str):
        """Callback to receive the list of managed accounts."""
        # Remove any empty strings from the account list
        self.accounts = [account for account in accountsList.split(",") if account.strip()]
        print("Available accounts:")
        for i, account in enumerate(self.accounts, start=1):
            print(f"{i}. {account}")

    def updateAccountValue(self, key: str, val: str, currency: str, accountName: str):
        print(f"Account: {accountName}, Key: {key}, Value: {val}, Currency: {currency}")
    
    def updatePortfolio(self, contract: Contract, position: float, marketPrice: float,
                    marketValue: float, averageCost: float, unrealizedPNL: float,
                    realizedPNL: float, accountName: str):
        """Callback function to receive portfolio updates."""
        colored_symbol = colorize_symbol(contract.symbol, unrealizedPNL)
        portfolio_item = {
            "Symbol": colored_symbol,
            "Position": position,
            "Market Price": marketPrice,
            "Market Value": marketValue,
            "Average Cost": averageCost,
            "Unrealized PNL": unrealizedPNL,
            "Realized PNL": realizedPNL,
            "Account Name": accountName
        }
        self.account_summary.append(portfolio_item)

    def nextValidId(self, orderId):
        self.nextOrderId = orderId

    def tickPrice(self, reqId, tickType, price, attrib):
        if tickType == 1:  # Bid price
            self.market_data["bid_price"] = price
        elif tickType == 2:  # Ask price
            self.market_data["ask_price"] = price
        elif tickType == 4:  # Last traded price
            self.market_data["last_price"] = price

    def error(self, reqId, errorCode, errorString, errorTime=None, advancedOrderRejectJson=""):
        """Handle errors from the API in a user-friendly format."""
        error_messages = {
            1100: "Connectivity between IB and TWS has been lost",
            1101: "Connectivity between IB and TWS has been restored",
            2100: "Market data farm connection is OK",
            2103: "A market data farm is disconnected",
            2104: "Market data farm connection is OK: data is delayed",
            2105: "HMDS (Historical Market Data Service) data farm connection is OK",
            2106: "A historical data farm is connected",
            2107: "HMDS (Historical Market Data Service) data farm is disconnected",
            2110: "Connectivity between IB and a data server is restored",
            2157: "Market data permissions are not available",
            2158: "Market depth data subscription is required",
            201: "Invalid order state",
            202: "Order canceled: Cannot modify",
            399: "Unknown order state",
            502: "Cannot connect to API server",
            504: "Server connection lost"
        }

        importance = "INFO"  # Default importance level
        if errorCode in [1100, 502]:
            importance = "ERROR"
        elif errorCode in [2100, 2103, 2104, 2105, 2106, 2110, 2157, 2158]:
            importance = "WARN"

        # Get the error message or fallback to the provided errorString
        message = error_messages.get(errorString, errorString)
        print(f"[{importance}]:[{errorString}]:[{message}]")

# Function to run the app in a separate thread
def run_loop(app):
    app.run()

def colorize_symbol(symbol, unrealized_pnl):
        """Returns a colorized symbol based on Unrealized PNL."""
        if unrealized_pnl < 0:
            return f"\033[91m{symbol}\033[0m"  # Red
        elif unrealized_pnl > 0:
            return f"\033[92m{symbol}\033[0m"  # Green
        return symbol  # Default (no color)
    
# Function to create a stock contract
def create_stock_contract(symbol):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = "STK"
    contract.currency = "USD"
    contract.exchange = "SMART"
    return contract

# Function to create a limit order
def create_limit_order(action, quantity, price):
    order = Order()
    order.action = action
    order.orderType = "LMT"
    order.totalQuantity = quantity
    order.lmtPrice = price
    return order

# Portfolio functionality
def view_portfolio(app):
    if not app.accounts:
        print("No accounts available or no connection with IB.\
             Please restart the application and ensure TWS/Gateway is connected to fetch accounts.")
        return

    print("\nSelect an account:")
    for i, account in enumerate(app.accounts, start=1):
        print(f"{i}. {account}")

    while True:
        try:
            choice = int(input("Enter the account number: ").strip())
            if 1 <= choice <= len(app.accounts):
                account_name = app.accounts[choice - 1]
                break
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Please enter a valid number.")

    app.reqAccountUpdates(True, account_name)
    time.sleep(5)  # Wait for updates
    app.reqAccountUpdates(False, account_name)
    if app.account_summary:
        print("\nPortfolio:")
        print(tabulate(app.account_summary, headers="keys", tablefmt="grid"))
    else:
        print("\nNo portfolio data received.")

# Buy functionality
def buy_stock(app):
    symbol = input("Enter the stock symbol to buy: ").strip().upper()
    max_price = float(input("Enter the maximum price to buy at: ").strip())
    quantity = int(input("Enter the quantity to buy: ").strip())

    contract = create_stock_contract(symbol)
    order = create_limit_order("BUY", quantity, max_price)

    while app.nextOrderId is None:
        time.sleep(0.1)

    app.placeOrder(app.nextOrderId, contract, order)
    print(f"Placed order to buy {quantity} shares of {symbol} at ${max_price}.")

# Sell functionality
def sell_stock(app):
    symbol = input("Enter the stock symbol to sell: ").strip().upper()
    min_price = float(input("Enter the minimum price to sell at: ").strip())
    quantity = int(input("Enter the quantity to sell: ").strip())

    contract = create_stock_contract(symbol)
    order = create_limit_order("SELL", quantity, min_price)

    while app.nextOrderId is None:
        time.sleep(0.1)

    app.placeOrder(app.nextOrderId, contract, order)
    print(f"Placed order to sell {quantity} shares of {symbol} at ${min_price}.")

if __name__ == "__main__":
    app = IBkrApp()
    app.connect("127.0.0.1", 4001, clientId=1)

    api_thread = threading.Thread(target=run_loop, args=(app,), daemon=True)
    api_thread.start()

    time.sleep(2)  # Wait for connection
    #app.reqManagedAccts()  # Request the list of managed accounts
    time.sleep(2)  # Wait for accounts to be received

    while True:
        print("\nChoose an option:")
        print("1. View Portfolio")
        print("2. Buy Stock")
        print("3. Sell Stock")
        print("4. Exit")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            view_portfolio(app)
        elif choice == "2":
            buy_stock(app)
        elif choice == "3":
            sell_stock(app)
        elif choice == "4":
            print("Exiting application...")
            break
        else:
            print("Invalid choice. Please try again.")

    app.disconnect()
