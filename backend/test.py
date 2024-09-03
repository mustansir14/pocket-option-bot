from pocketoptionapi.stable_api import PocketOption
import time

ssid=r"""42["auth",{"session":"bnflkl41qh6t0bpek0gnqv6847","isDemo":1,"uid":83224764,"platform":3}]""" 
# ssid = r"""42["auth",{"session":"a:4:{s:10:\"session_id\";s:32:\"301f139f486145a5ad502799df47a5b6\";s:10:\"ip_address\";s:15:\"175.107.203.149\";s:10:\"user_agent\";s:101:\"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36\";s:13:\"last_activity\";i:1725278743;}99d3a456818cc673f024d06a5c7642ea","isDemo":0,"uid":83224764,"platform":3}]"""
api=PocketOption(ssid)
api.connect()
while not api.check_connect():
    time.sleep(1)
print("connected")

ASSET = "#AXP_otc"
CANDLES_TO_CHECK = 2
TIMEFRAME = 30

prev_data = None
while True:
    data = None
    counter = 0
    while data is None:
        data = api.get_candles(ASSET, TIMEFRAME, None, TIMEFRAME*CANDLES_TO_CHECK)
        counter += 1
        if counter == 5:
            print("ERROR: Could not get candles")
            break
    if counter == 5:
        break

    print(data)
    
    if prev_data is not None and data["time"].iloc[-1] == prev_data["time"].iloc[-1]:
        prev_data = data
        time.sleep(1)
        continue

    prev_data = data

    print(f"Checking last {CANDLES_TO_CHECK} candles...")

    if all(data['close'] < data['open']):
        action = "call"
    elif all(data['close'] > data['open']):
        action = "put"
    else:
        action = ""

    if action:
        print(f'Creating order for {"buy" if action == "call" else "sell"}...')
        result = False
        counter = 0
        while not result:
            result, _ = api.buy(10, ASSET, action, 60)
            counter += 1
            if counter == 10:
                print("ERROR: Could not create order")
                break
        if counter == 10:
            continue

        print("Successfully created order")