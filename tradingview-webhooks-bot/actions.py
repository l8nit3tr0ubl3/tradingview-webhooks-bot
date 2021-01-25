import ccxt
import ast
import requests
import config as config
from ccxt.base.decimal_to_precision import ROUND, DECIMAL_PLACES

exchange = ccxt.ftx({
        # Inset your API key and secrets for exchange in question.
        'apiKey': config.EXCHANGEAPI,
        'secret': config.EXCHANGESECRET,
        'enableRateLimit': True,
    })

def parse_webhook(webhook_data):

    """
    This function takes the string from tradingview and turns it into a python dict.
    :param webhook_data: POST data from tradingview, as a string.
    :return: Dictionary version of string.
    """
    head, sep, tail = webhook_data.partition('----')
    data = ast.literal_eval(head)
    return data, tail

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
    url = "https://api.telegram.org/bot{0}/sendMessage?chat_id={1}&text={2}".format(config.API, config.ID, message)
    r = requests.get(url)
    print(r)

def getNewAmount(data):
    ticker = exchange.fetch_ticker(data['symbol'])
    bid = ticker['bid']
    ask = ticker['ask']
    new_amount = 0.0
    if "%" in data['amount']:
        balance = exchange.fetch_balance()
        balance = float(balance['free']['USD'])
        new_amount = data['amount'].strip('%')
        new_amount = balance * (float(new_amount)/100)
        if data['side'] == 'sell':
            new_amount = float(new_amount) / ask
        if data['side'] == 'buy':
            new_amount = float(new_amount) / bid
    if "U" in data['amount']:
        new_amount = data['amount'].strip('U')
        if data['side'] == 'sell':
            new_amount = float(new_amount) / ask
        if data['side'] == 'buy':
            new_amount = float(new_amount) / bid
    else:
        new_amount = data['amount']

    return new_amount

def send_order(data, tail):
    
    """
    This function sends the order to the exchange using ccxt.
    :param data: python dict, with keys as the API parameters.
    :return: the response from the exchange.
    """
    message = tail
    new_amount = getNewAmount(data)
    if data['amount'] == 'close':
        trades = exchange.private_get_positions()
        for trade in trades['result']:
            if data['symbol'] in trade['future']:
               if trade['size'] == 0.0:
                   message = "No trade open to close, trade not sent. {0}".format(message)
               else:
                   trade_size = trade['size']
                   print('*Sending:', data['symbol'], data['type'], data['side'], trade_size)
                   try:
                       order = exchange.create_order(data['symbol'], data['type'], data['side'], trade_size, float(data['price']))
                       print('Exchange Response: Symbol={0}, Trade Type={1}, Trade Side={2}, Trade Status={3} \n'.format(order['symbol'], order['type'], order['side'], order['status']))
                   except Exception as e:
                        message = "ERROR IN OrderSend, CHECK BOT /n {0} /n {1}".format(e, message)
                        print(e, message)

    elif data['amount'] != 'close':
        print('*Sending:', data['symbol'], data['type'], data['side'], float(data['amount']), new_amount)            
        try:
            order = exchange.create_order(data['symbol'], data['type'], data['side'], float(new_amount), float(data['price']))
            print('Exchange Response: Symbol={0}, Trade Type={1}, Trade Side={2}, Trade Status={3} \n'.format(order['symbol'], order['type'], order['side'], order['status']))
        except Exception as e:
            message = "ERROR IN OrderSend, CHECK BOT /n {0} /n {1}".format(e, message)
            print(e, message)
    # This is the last step, the response from the exchange will tell us if it made it and what errors pop up if not.
    #print(order)
    SendToTelegram(message)

