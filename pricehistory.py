import logging
import sys
import time
from datetime import datetime, timedelta

from pycoingecko import CoinGeckoAPI

logging.basicConfig(level=logging.INFO)

cg = CoinGeckoAPI()


def __calculate_price_change(prev_price_data: dict, curr_price_data: dict):
    prev_price = prev_price_data["price"]
    curr_price = curr_price_data["price"]
    # diff = abs(curr_price - prev_price)
    change = float(curr_price / prev_price)
    return {"date": curr_price_data["date"], "price": curr_price, "change": change}


def get_price_history(protocols: str, window=91):
    logging.info("============================ <Price History Starts> =====================================")
    coins = []
    try:
        if window <= 90:
            window = 91

        # get coin ids
        protocols = list(map(lambda t: t.strip().lower(), protocols.split(',')))
        coins = list(filter(lambda coin_info: coin_info['id'] in protocols, cg.get_coins_list()))
        logging.info(coins)

        if len(protocols) != len(coins):
            raise Exception(f"Cannot find one or more requested ticker in coin list. Requested protocols: {protocols}")

        end_date = datetime.now()
        start_date = end_date - timedelta(days=window)

        result = {}
        token_maps = []
        max_length = sys.maxsize
        max_length_ticker = ''
        count = 1
        for coin in coins:
            if count % 3 == 0:
                time.sleep(100)
            count += 1

            ticker = coin['symbol']
            logging.info(f"Getting price info for ticker: {ticker}")
            prices = cg.get_coin_market_chart_range_by_id(coin['id'], 'usd', int(start_date.timestamp()), int(end_date.timestamp()))

            # set price history
            # prices["prices"] => [[timestamp1, price1]....[timestampN, priceN]]
            result[ticker] = list(map(lambda price: {"date": price[0], "price": price[1]}, prices["prices"]))

            # calculate price change
            result[ticker] = [__calculate_price_change(result[ticker][i - 1], result[ticker][i]) for i in
                              range(1, len(result[ticker]) - 1)]

            size = len(result[ticker])
            if size < max_length:
                max_length = size
                max_length_ticker = ticker
            token_maps.append({coin['id']: ticker})

        # check lengths
        logging.info("Tickers: {}".format(protocols))
        logging.info("Coin Information: {}".format(coins))
        logging.info("Start Date: {}".format(start_date.strftime("%d/%m/%Y, %H:%M:%S")))
        logging.info("End Date: {}".format(end_date.strftime("%d/%m/%Y, %H:%M:%S")))
        logging.info("Max Length: {}".format(max_length))
        logging.info("Max Length Ticker: {}".format(max_length_ticker))
        logging.info("============================ <Price History Ends> =====================================\n")

        for k, v in result.items():
            result[k] = v[0:max_length]
        return result, token_maps
    except Exception as e:
        msg = "Error fetching price history for {}.\nCoin info: {}.\nError : {}".format(protocols, coins, e)
        logging.error(msg)
        logging.info("============================ <Price History Ends> =====================================\n")
        return {}, []
