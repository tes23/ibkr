from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.common import *
from ibapi.contract import *
import threading
import time
from tabulate import tabulate

class IBkrApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.account_summary = []

    def updateAccountValue(self, key: str, val: str, currency: str, accountName: str):
        """Callback function to receive account values."""
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

    def error(self, reqId, errorCode, errorString, errorTime=None, advancedOrderRejectJson=""):
        """Handle errors from the API."""
        print(f"Error: ReqId={reqId}, Code={errorCode}, Msg={errorString}")

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

if __name__ == "__main__":
    # Initialize the app
    app = IBkrApp()

    # Connect to the IB Gateway or TWS
    app.connect("127.0.0.1", 4001, clientId=1)

    # Start the app in a separate thread
    api_thread = threading.Thread(target=run_loop, args=(app,), daemon=True)
    api_thread.start()

    # Wait for a short time to ensure connection
    time.sleep(2)

    # Request account updates
    account_name = "U19646020"  # Replace with your actual account name
    app.reqAccountUpdates(True, account_name)

    # Wait for updates to be received
    time.sleep(10)

    # Disconnect after retrieving portfolio data
    app.disconnect()

    # Print the final portfolio summary as a table
    if app.account_summary:
        print("\nFinal Portfolio Summary:")
        print(tabulate(app.account_summary, headers="keys", tablefmt="grid"))
    else:
        print("\nNo portfolio data received.")