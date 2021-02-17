import ccxt
import ast
import requests
import config as config
import requests
from selenium import webdriver
from time import sleep
from selenium.webdriver.firefox.options import Options as FirefoxOptions

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

def Get_Screen(URL):
    driver = webdriver.Chrome()
    driver.get(URL)
    sleep(1)
    driver.get_screenshot_as_file("screenshot.png")
    driver.quit()
    
def sendImage(API, ID):
    url = "https://api.telegram.org/bot{0}/sendPhoto".format(API);
    files = {'photo': open('screenshot.png', 'rb')}
    data = {'chat_id' : ID}
    r= requests.post(url, files=files, data=data)
    print(r.status_code, "ScreenShot Sent...")

def SendToTelegram(message, data):
    for Bot, BotInfo in config.TelegramAccounts.items():
        if BotInfo['Name'] in data['TelegramName']:
            print("BotInfo Name {0} MATCHES TelegramName {1}".format(BotInfo['Name'], data['TelegramName']))
            if 'Chart=' in message:
                head, sep, tail = message.partition('Chart=')
                URL = tail.strip('"')
                URL = URL.strip("'")
                try:
                    Get_Screen(URL)
                    sendImage(BotInfo['API'], BotInfo['ID'])
                except Exception as e:
                    print(e)
                    Get_Screen(URL)
                    sendImage(BotInfo['API'], BotInfo['ID'])
                url = "https://api.telegram.org/bot{0}/sendMessage?chat_id={1}&text={2}".format(BotInfo['API'], BotInfo['ID'], head)
            else:
                url = "https://api.telegram.org/bot{0}/sendMessage?chat_id={1}&text={2}".format(BotInfo['API'], BotInfo['ID'], message)
            r = requests.get(url)
            print(r)
        else:
            print("BotInfo Name {0} not match TelegramName {1}".format(BotInfo['Name'], data['TelegramName']))

def getNewAmount(data, exchange):
    ticker = exchange.fetch_ticker(data['symbol'])
    bid = ticker['bid']
    ask = ticker['ask']
    new_amount = 0.0
    if isinstance(data['amount'], str) == True:
        if "%" in data['amount']:
            new_amount = data['amount'].strip('%')
            balance = exchange.fetch_balance()
            balance = float(balance['free']['USD'])
            new_amount = balance * (float(new_amount)/100)
        if "U" in data['amount']:
            new_amount = data['amount'].strip('U')
        if data['side'] == 'sell':
            new_amount = float(new_amount) / ask
        if data['side'] == 'buy':
            new_amount = float(new_amount) / bid
    else:
        new_amount = data['amount']

    return new_amount

def send_order(data, tail, exchange, BotId):
    
    """
    This function sends the order to the exchange using ccxt.
    :param data: python dict, with keys as the API parameters.
    :return: the response from the exchange.
    """
    message = tail
    if data['amount'] == 'close':
        trades = exchange.private_get_positions()
        for trade in trades['result']:
            if data['symbol'] in trade['future']:
               if trade['size'] == 0.0:
                   message = "No trade open to close, trade not sent. {0}".format(message)
               else:
                   trade_size = trade['size']
                   print('*Sending:', BotId, data['type'], data['side'], trade_size , data['symbol'])
                   try:
                       order = exchange.create_order(data['symbol'], data['type'], data['side'], trade_size, float(data['price']))
                       print('Exchange Response: Symbol={0}, Trade Type={1}, Trade Side={2}, Trade Status={3} \n'.format(order['symbol'], order['type'], order['side'], order['status']))
                   except Exception as e:
                       message = "ERROR IN OrderSend, CHECK BOT /n {0} /n {1}".format(e, message)
                       print(e, message)
    elif data['amount'] != 'close':
        new_amount = getNewAmount(data, exchange)
        print('*Sending:', BotId, data['type'], data['side'], data['amount'], new_amount, data['symbol'])            
        try:
            order = exchange.create_order(data['symbol'], data['type'], data['side'], float(new_amount), float(data['price']))
            print('Exchange Response: Symbol={0}, Trade Type={1}, Trade Side={2}, Trade Status={3} \n'.format(order['symbol'], order['type'], order['side'], order['status']))
        except Exception as e:
            message = "ERROR IN OrderSend, CHECK BOT /n {0} /n {1}".format(e, message)
            print(e, message)

