#!/usr/bin/env python3

import websocket, json, pprint, talib, numpy
import config
from binance.client import Client
from binance.enums import *

socket = "wss://stream.binance.com:9443/ws/btcgbp@kline_1m"

rsi_period = 14
rsi_overbought = 70
rsi_oversold = 30

trade_symbol = 'BTCGBP'
trade_quantity = 0.0007

closes, highs, lows, real_port_value, investment = [], [], [], [], []
in_position = False

client = Client(config.API_KEY, config.API_SECRET, tld='com')

core_to_trade = True
core_quantity = 0
aroon_period = 2
amount = 20
money_end = amount
core_trade = amount*0.80
trade_amount = amount*0.20
portfolio = 0

def order(side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
    try:
        print("sending order")
        order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
        print(order)
    except Exception as e:
        return False

    return True

def on_open(ws):
    print('opened connection')

def on_close(ws):
    print('closed connection')

def on_message(ws, message):
    global closes, highs, lows, core_to_trade, core_quantity, money_end, portfolio, investment

    print('received message')
    json_message = json.loads(message)
    pprint.pprint(json_message)

    candle = json_message['k']
    is_candle_closed = candle['x']
    close = candle['c']
    high = candle['h']
    low = candle['l']



    if is_candle_closed:
        print("candle closed at {}".format(close))
        closes.append(float(close))
        highs.append(float(high))
        lows.append(float(low))
        print("closes")
        print(closes)
        print("highs")
        print(highs)
        print("lows")
        print(lows)
        last_price = closes[-1]


        
        aroon = talib.AROONOSC(numpy.array(highs), numpy.array(lows), aroon_period)
        last_aroon = round(aroon[-1],2)
        amt = last_aroon * trade_amount / 100
        port_value = portfolio * last_price - core_quantity * last_price
        trade_amt = amt - port_value
        mini_amt = amt / 25316.46

        rt_port_value = port_value + core_quantity * last_price + money_end
        real_port_value.append(float(rt_port_value))

        print(f'###########################################################################################')
        print(f'last aroon is "{last_aroon}" and exposure is "£{amt}"')

        if trade_amt > 0:
            if in_position:
                order_succeeded = order(side_buy, mini_amt, trade_symbol)

        if trade_amt < 0:
            if in_position:
                order_succeeded = order(side_sell, mini_amt, trade_symbol)


        if len(closes) > rsi_period:
            np_closes = numpy.array(closes)
            rsi = talib.RSI(np_closes, rsi_period)
            print("all rsi's calculated so far")
            print(rsi)
            last_rsi = rsi[-1]
            print("the current rsi is {}".format(last_rsi))

            if last_rsi > rsi_overbought:
                if in_position:
                    order_succeeded = order(side_sell, trade_quantity, trade_symbol)
                    if order_succeeded:
                        in_position = False
                else:
                    ("overbought but unowned")

            if last_rsi < rsi_oversold:
                if in_position:
                    print("oversold but owned")
                else:
                    order_succeeded = order(side_buy, trade_quantity, trade_symbol)
                    if order_succeeded:
                        in_position = True



ws = websocket.WebSocketApp(socket, on_open=on_open, on_close=on_close, on_message=on_message)

ws.run_forever()
