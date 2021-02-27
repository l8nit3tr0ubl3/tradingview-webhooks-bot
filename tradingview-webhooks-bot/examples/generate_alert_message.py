from auth import get_token

"""
This function will take a lot of the tedious work out of generating alert messages!
Simply follow the onscreen input prompts, at the end a string with everything you need
will be output, allowing you to copy and paste into tradingview!
"""

#{"TelegramName": "L8nit3 Main Bot",
#"BotName": "L8nit3 Main Bot",
#"type": "market", "side": "buy",
#"amount": "15%", "price": "{{close}}",
#"symbol": "ADA-PERP",
#"key": ""}

def social():
    print('Are you sending a Telegram alert? Y or N?')
    telegram_name = input()
    if telegram_name == 'Y' or telegram_name == 'y':
        print('What is the name of the Telegram account in your config?')
        tg = input()
    return tg

def generate_alert_message():
    bot_name = "None"
    tg = "None"

    print('#OrderSend Information#')
    print('Enter Symbol To Trade:')
    symbol = input()
    print('Are you skipping ordersend, and only sending an alert?\nY or N?')
    type_of_order = input()
    if type_of_order == 'Y' or type_of_order == 'y':
        type_of_order = 'skip'
        print('#Social Alerts Information#')
        tg = social()
        output = {"TelegramName": tg,
                  "BotName": bot_name,
                  "type": type_of_order}
    else:
        print('Enter type: (limit, market)')
        type_of_order = input()
        print('Enter name of bot to send order.')
        botname = input()
        print("Are you closing an open order?\nY or N")
        close = input()
        if close =='Y' or close == 'y':
            amount = 'close'
        else:
            print("Please enter a trade  size (append U for USD, % for balance percent)")
            amount = input()
        print('Enter Side (buy or sell):')
        side = input()
        if type == 'limit':
            print('Enter limit price:')
            price = input()
        else:
            price = 'None'
        key = get_token()
        print('#Social Alerts Information#')
        tg = social()
        output = {"TelegramName": tg,
              "BotName": botname,
              "type": type_of_order,
              "side": side,
              "amount": amount,
              "symbol": symbol,
              "price": price,
              "key": key}
    
    print("Copy the below information into your TView alert:\n")
    print(str(output).replace('\'', '\"'))
    print('----')
    print('PLACE Telegram/Twitter ALERT INFO HERE')


generate_alert_message()
