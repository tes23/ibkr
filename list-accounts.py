from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.common import *
from ibapi.contract import *
import threading
import time

class IBkrApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.accounts = []

    def managedAccounts(self, accountsList: str):
        """Callback function to receive the list of managed accounts."""
        self.accounts = accountsList.split(",")
        print("Accounts List:", self.accounts)

    def error(self, reqId, errorCode, errorString, errorTime=None, advancedOrderRejectJson=""):
        """Handle errors from the API."""
        print(f"Error: ReqId={reqId}, Code={errorCode}, Msg={errorString}")

# Function to run the app in a separate thread
def run_loop(app):
    app.run()

if __name__ == "__main__":
    # Initialize the app
    app = IBkrApp()

    # Connect to the IB Gateway or TWS
    # Replace '127.0.0.1' with your host and '7497' with your port if different
    app.connect("127.0.0.1", 4001, clientId=0)

    # Start the app in a separate thread
    api_thread = threading.Thread(target=run_loop, args=(app,), daemon=True)
    api_thread.start()

    # Wait for a short time to ensure connection
    time.sleep(2)

    # Disconnect after retrieving accounts
    time.sleep(5)
    app.disconnect()

    # Print the accounts
    print("Final Accounts List:", app.accounts)