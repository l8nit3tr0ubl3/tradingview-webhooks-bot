import ccxt
import ast


def parse_webhook(webhook_data):

    """
    This function takes the string from tradingview and turns it into a python dict.
    :param webhook_data: POST data from tradingview, as a string.
    :return: Dictionary version of string.
    """

    data = ast.literal_eval(webhook_data)
    return data


def calc_price(given_price):

    """
    Will use this function to calculate the price for limit orders.
    :return: calculated limit price
    """

    if given_price == None:
        price = given_price
    else:
        price = given_price
    return price


def SendToTelegram(message):
    API = "" #BotFather API Key
    ID = "-100"  #Name of Channel
    url = "https://api.telegram.org/bot{0}/sendMessage?chat_id={1}&text={2}".format(API, ID, message)
    r = requests.get(url)
    print(r)

def send_order(data):

    """
    This function sends the order to the exchange using ccxt.
    :param data: python dict, with keys as the API parameters.
    :return: the response from the exchange.
    """

    # Replace kraken with your exchange of choice.
    exchange = ccxt.ftx({
        # Inset your API key and secrets for exchange in question.
        'apiKey': '',
        'secret': '',
        'enableRateLimit': True,
    })

    # Send the order to the exchange, using the values from the tradingview alert.
    orderbook = exchange.fetch_order_book(data['symbol'])
    bid = orderbook['bids'][0][0] if len (orderbook['bids']) > 0 else None
    ask = orderbook['asks'][0][0] if len (orderbook['asks']) > 0 else None
    if "%" in data['amount']:
        balance = exchange.fetch_balance()
        balance = float(balance['free']['USD'])
        new_amount = data['amount'].strip('%')
        new_amount = balance * (float(new_amount)/100)
        print(balance, new_amount)
    if "U" in data['amount']:
        new_amount = data['amount'].strip('U')
    if data['side'] == 'sell':
        new_amount = float(new_amount) / ask
    if data['side'] == 'buy':
        new_amount = float(new_amount) / bid
    else:
        new_amount = data['amount']
    print('Sending:', data['symbol'], data['type'], data['side'], data['amount'], new_amount , calc_price(data['price']))
    order = exchange.create_order(data['symbol'], data['type'], data['side'], new_amount, calc_price(data['price']))
    # This is the last step, the response from the exchange will tell us if it made it and what errors pop up if not.
    print('Exchange Response:', order)
    message = """
Symbol:{0}
Side:{1}
Bid Price: {2}
Ask Price: {3}
Amount: {4}""".format(data['symbol'], data['side'], bid, ask, round(new_amount, 8))
    SendToTelegram(message)
