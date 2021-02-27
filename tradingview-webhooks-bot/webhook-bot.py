"""
Tradingview-webhooks-bot is a python bot that works with tradingview's webhook alerts!
This bot is not affiliated with tradingview and was originally created by @robswc.
It has been modified for PERSONAL USE by l8nit3.
"""
from actions import send_order, parse_webhook, send_to_telegram, post_tweet, print_stats
from auth import get_token
from flask import Flask, request, abort
import config
import ccxt
from pynput import keyboard

def on_press(key):
    try:
        if key.char == 's':
            print_stats()
    except AttributeError:
        pass

listener = keyboard.Listener(on_press=on_press)
listener.start()
# Create Flask object called app.
app = Flask(__name__)

@app.route('/')
def root():
    """# Create root to easily let us know its on/working."""
    return 'online'

@app.route('/webhook', methods=['POST'])
def webhook():
    """Combine all functions in actions.py, and run flask server"""
    if request.method == 'POST':
        print('*'*60)
        # Parse the string data from tradingview into a python dict
        data = parse_webhook(request.get_data(as_text=True))[0]
        tail = parse_webhook(request.get_data(as_text=True))[1]
        message = tail
        if (data['type'] != "Skip") and (get_token() == data['key']):
            # Check that the key is correct
            print(' [Alert Received] ')
            print(tail)
            for account, account_info in config.Accounts.items():
                if account_info['Name'] in data['BotName']:
                    exchange = ccxt.ftx({'apiKey': account_info['exchangeapi'],
                    'secret': account_info['exchangesecret'],
                    'enableRateLimit': True,})
                    if account_info['Subaccount'] == 'Yes':
                        exchange.headers = {'FTX-SUBACCOUNT': account_info['SubName'],}
                    send_order(data, tail, exchange, account_info['Name'], account_info['Track'])
                    if account_info['UseTelegram'] == 'Yes':
                        send_to_telegram(tail, data)
                    if account_info['UseTwitter'] == 'Yes':
                        post_tweet(message)
                else:
                    pass
            return '', 200

        if data['type'] == "Skip":
            print(' [ALERT ONLY - NO TRADE] ')
            print(tail)
            for account, account_info in config.Accounts.items():
                if account_info['Name'] in data['BotName']:
                    if account_info['UseTelegram'] == 'Yes':
                        send_to_telegram(tail, data)
                    if account_info['UseTwitter'] == 'Yes':
                        post_tweet(message)
        print('*'*60, '/n')
        return '', 200
    else:
        abort(400)


if __name__ == '__main__':
    """Run app"""
    app.run()

listener.stop()
