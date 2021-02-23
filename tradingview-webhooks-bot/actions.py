"""
All the reuired functions to run the background of the server.
"""
import ast
from time import sleep
import requests
import tweepy
import config
from selenium import webdriver

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

def post_tweet(tweet):
    """
    Takes api and Consumer keys generated on deleveoper.twitter.com
    to post an alert as a tweet.
    :param tweet: The alert message youd like sent through.
    """
    twitter_auth_keys = {
        "consumer_key"        : config.twitter['ConsumerKey'],
        "consumer_secret"     : config.twitter['Consumersecret'],
        "access_token"        : config.twitter['AccessToken'],
        "access_token_secret" : config.twitter['Accesssecret']
    }

    auth = tweepy.OAuthHandler(
            twitter_auth_keys['consumer_key'],
            twitter_auth_keys['consumer_secret']
            )
    auth.set_access_token(
            twitter_auth_keys['access_token'],
            twitter_auth_keys['access_token_secret']
            )
    api = tweepy.API(auth)
    try:
        status = api.update_status(status=tweet)
    except Exception as error:
        print(error, status)
    print('Tweet Sent')

def get_screen(url):
    """
    Uses selenium to take and save a screenshot of the chart making the alert.
    :param url: the url of the charts
    """
    driver = webdriver.Chrome()
    driver.get(url)
    sleep(1)
    driver.get_screenshot_as_file("screenshot.png")
    driver.quit()

def send_image(api, id):
    """
    Takes the saved image from get_screen() and sends it to telegram
    :param api: api keys generated by botFather on telegram.
    :param id: The public id of the channel youd like to post to. Add -100 as a prefix
    """
    url = "https://api.telegram.org/bot{0}/sendPhoto".format(api)
    files = {'photo': open('screenshot.png', 'rb')}
    data = {'chat_id' : id}
    r= requests.post(url, files=files, data=data)
    print(r.status_code, "ScreenShot Sent...")

def send_to_telegram(message, data):
    """
    Takes alert data and sends as a telegram channel message.
    Also, if enabled, uses get_screen and send_image.
    :param message: bottom half of TV alert, contains telegram message
    :param data: Top half of TV alert, contains order data, and decides whether to
    send or skip the telegram alert.
    :return "string" this is the telegram message for debugging
    """
    for bot, bot_info in config.TelegramAccounts.items():
        if bot_info['Name'] in data['TelegramName']:
            print("bot_info Name {0} MATCHES TelegramName {1}".format(bot_info['Name'],
            data['TelegramName']))
            string = ""
            if 'Chart=' in message:
                head, sep, tail = message.partition('Chart=')
                url = tail.strip('"')
                url = url.strip("'")
                try:
                    get_screen(url)
                    send_image(bot_info['api'], bot_info['id'])
                except Exception as e:
                    print(e)
                    get_screen(url)
                    send_image(bot_info['api'], bot_info['id'])
                url = "https://api.telegram.org/bot{0}/sendMessage?chat_id={1}&text={2}".format(
                bot_info['api'], bot_info['id'], head)
                string = head
            else:
                url = "https://api.telegram.org/bot{0}/sendMessage?chat_id={1}&text={2}".format(
                bot_info['api'], bot_info['id'], message)
                string = message
            r = requests.get(url)
            print(r)
            return string

def get_new_amount(data, exchange):
    """
    Used to allow the User to set order size in USD or as % of balance.
    :param data: Top section of TV alert, contains order information to open/close position
    :param exchange: Top level call to ccxt for pricing data
    :return Proper coin value for order size
    """
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

def get_stats(market, side, price):
    tracking_dict = {}
    with open('overall_stats.txt') as file:
        store_file = file.read()
        tracking_dict = eval(store_file)
        if market not in tracking_dict:
            tracking_dict[market] = {'side': None, 'price': price, 'wins': 0, 'losses': 0, 'accuracy': 0.0}
        file.close()
    return tracking_dict

def save_stats(tracking_dict):
    file = open('overall_stats.txt', 'w+')
    file.write(tracking_dict)
    file.close

def track_accuracy(market, side, price):
    tracking_dict = get_stats(market, side, price)
    if market in tracking_dict.keys():
        if side == 'buy':
            if tracking_dict[market]['side'] == 'sell' or tracking_dict[market]['side'] == None:
                tracking_dict[market]['side'] = side
                tracking_dict[market]['price'] = price
            
        elif side == 'sell':
            wins = tracking_dict[market]['wins']
            losses = tracking_dict[market]['losses']
            if tracking_dict[market]['side'] == 'buy' or tracking_dict[market]['side'] == None:
                if float(tracking_dict[market]['price']) < float(price):
                    wins += 1
                if float(tracking_dict[market]['price']) > float(price):
                    losses += 1
                    
                tracking_dict[market]['accuracy'] = (wins/(losses+wins))*100 if (wins > 0 and losses > 0) else 0.0
                tracking_dict[market]['side'] = side
                tracking_dict[market]['price'] = price
                tracking_dict[market]['wins'] = wins
                tracking_dict[market]['losses'] = losses
        save_stats(str(tracking_dict))

def send_order(data, tail, exchange, bot_id, Track):

    """
    This function sends the order to the exchange using ccxt.
    :param data: Top half of the TV alert, conntains information for opening position
    :param tail: bottom half of TV alert, contains post info for Tgram and Twitter
    :param exchange: Top level call to ccxt for market information
    :param: bot_id: Name of current working account (when using multiple)
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
                    print('*Sending:', bot_id, data['type'],
                    data['side'], trade_size , data['symbol'])
                    try:
                        order = exchange.create_order(data['symbol'],
                        data['type'], data['side'], trade_size, float(data['price']))
                    except Exception as error:
                        message = "ERROR IN OrderSend, CHECK bot /n {0} /n {1}".format(error,
                        message)
                        print(error, message)
    elif data['amount'] != 'close':
        new_amount = get_new_amount(data, exchange)
        print('*Sending:', bot_id, data['type'], data['side'],
        data['amount'], new_amount, data['symbol'])
        try:
            order = exchange.create_order(data['symbol'], data['type'],
            data['side'], float(new_amount), float(data['price']))
        except Exception as error:
            message = "ERROR IN OrderSend, CHECK bot /n {0} /n {1}".format(error, message)
            print(error, message)
    if (data['type'] != "Skip") and (Track == 'Yes'):
        try:
            wins, losses = track_accuracy(data['symbol'], data['side'], float(data['price']))
            print("Wins: {0}, Losses: {1}, Accuracy: {2}%".format(wins, losses, accuracy))
        except Exception as error:
            print(error)
