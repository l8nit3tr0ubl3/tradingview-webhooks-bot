"""
Tradingview-webhooks-bot is a python bot that works with tradingview's webhook alerts!
This bot is not affiliated with tradingview and was created by @robswc

You can follow development on github at: github.com/robswc/tradingview-webhook-bot

I'll include as much documentation here and on the repo's wiki!  I
expect to update this as much as possible to add features as they become available!
Until then, if you run into any bugs let me know!
"""

from actions import send_order, parse_webhook, SendToTelegram
from auth import get_token
from flask import Flask, request, abort
import config as config
import ccxt

# Create Flask object called app.
app = Flask(__name__)


# Create root to easily let us know its on/working.
@app.route('/')
def root():
    return 'online'


@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        print('*'*60)
        # Parse the string data from tradingview into a python dict
        data = parse_webhook(request.get_data(as_text=True))[0]
        tail = parse_webhook(request.get_data(as_text=True))[1]
        if data['type'] != "Skip":
            # Check that the key is correct
            if get_token() == data['key']:
                print(' [Alert Received] ')
                print('POST Received:', data)
                for account, AccountInfo in config.Accounts.items():
                        exchange = ccxt.ftx({'apiKey': AccountInfo['EXCHANGEAPI'], 'secret': AccountInfo['EXCHANGESECRET'], 'enableRateLimit': True,})
                        send_order(data, tail, exchange, AccountInfo['Name'])
                SendToTelegram(tail)
                return '', 200
            else:
                #pass
                abort(403)
        else:
            print(' [ALERT ONLY - NO TRADE] ')
            print(tail)
            SendToTelegram(tail)
            return '', 200
    else:
        abort(400)
    print('*'*60, '/n')


if __name__ == '__main__':
    app.run()
