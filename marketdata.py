import time
import logging
import requests
from requests.exceptions import Timeout, RequestException

# Configure logging
#logging.basicConfig(level=logging.DEBUG)
#logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.DEBUG)

def get_hashname(item, skin, wear, stat):
    item = item.replace(" ", "%20")
    skin = skin.replace(" ", "%20")
    float_map = {
        1: "%20%28Factory%20New%29",
        2: "%20%28Minimal%20Wear%29",
        3: "%20%28Field-Tested%29",
        4: "%20%28Well-Worn%29",
        5: "%20%28Battle-Scarred%29"
    }
    wear = float_map.get(wear, "")
    if stat == 1:
        item = "StatTrak™%20" + item
    hashname = item + "%20%7C%20" + skin + wear
    logging.debug(f"Generated hashname: {hashname}")
    return hashname


def make_request_with_retry(url, max_retries=5, backoff_factor=16, current_sleep_time=[0]):
    # Use current_sleep_time as a mutable default argument to preserve state

    #print(f"Current sleepTime: {current_sleep_time[0]:.2f} seconds...")

    for retry in range(max_retries):
        try:
            time.sleep(current_sleep_time[0])
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            if current_sleep_time[0] < 5.16:
                current_sleep_time[0] += 5.16
            return response
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                wait_time = backoff_factor * (1.51 ** retry)
                logging.warning(f"Rate limit exceeded, retrying in {wait_time:.2f} seconds...")

                time.sleep(wait_time)
            else:
                logging.error(f"HTTP error occurred: {e}")
                break
        except requests.exceptions.RequestException as e:
            logging.error(f"Error making request: {e}")
            break
        finally:
            current_sleep_time[0] = max(current_sleep_time[0], 0)

    return None

def get_nameid(hashname):
    url = f"https://steamcommunity.com/market/listings/730/{hashname}"
    response = make_request_with_retry(url)
    if response:
        try:
            html = response.text
            logging.debug(f"HTML response received for {hashname}: {html[:5000]}...")  # Log more of the response
            if 'Market_LoadOrderSpread(' in html:
                nameid = html.split('Market_LoadOrderSpread( ')[1].split(' ')[0]
                return int(nameid)
            else:
                logging.error("Pattern 'Market_LoadOrderSpread(' not found in HTML")
        except IndexError as e:
            logging.error(f"IndexError parsing nameid from HTML: {e}")
        except Exception as e:
            logging.error(f"Error parsing nameid: {e}")
    else:
        logging.error("Failed to get a valid response from Steam Community Market")
    return None


def get_steam_market_price(item_name):
    api_key = "C73EC1F4A6A0DBBFCA6C67C0E7384EA9"
    app_id = 730
    currency = 6
    
    try:
        url = f'https://api.steampowered.com/ISteamEconomy/GetAssetPrices/v1/?key={api_key}&appid={app_id}&currency={currency}&language=en&format=json'
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        if response.status_code == 200:
            data = response.json()
            price_data = data['result']['assets'][0]['prices']['PLN']
            logging.debug(f"Fetched price data: {price_data}")
            return price_data
        else:
            logging.error(f"Error: Failed to retrieve data (Status code: {response.status_code})")
    except Timeout:
        logging.error("Timeout error: The request timed out.")
    except RequestException as e:
        logging.error(f"Error fetching market price: {e}")
    except Exception as e:
        logging.error(f"Other error fetching market price: {e}")
    
    return None

def item_data(hashname):
    nameid = get_nameid(hashname)
    out = {}
    
    if not nameid:
        logging.error("NameID is None")
        return out
    
    try:
        lowest_price = get_steam_market_price(hashname)
        if lowest_price:
            out["lowest_price"] = lowest_price
        else:
            out["lowest_price"] = "Price data not available"
        
        url = f"https://steamcommunity.com/market/itemordershistogram?country=US&currency=6&language=english&two_factor=0&item_nameid={nameid}"
        response = make_request_with_retry(url)
        if response and response.status_code == 200:
            order_data = response.json()
            if isinstance(order_data, dict):
                out["buy_req"] = int(order_data.get('highest_buy_order', 0)) / 100
                out["nameid"] = nameid
            else:
                logging.error(f"Unexpected order_data format: {order_data}")
                out["order_data_error"] = "Unexpected format"
        else:
            logging.error(f"Failed to fetch order data: {response.status_code if response else 'No response'}")
    except Timeout:
        logging.error("Timeout error: The request timed out.")
    except RequestException as e:
        logging.error(f"Error fetching item data: {e}")
    except Exception as e:
        logging.error(f"Other error fetching item data: {e}")
    
    return out
