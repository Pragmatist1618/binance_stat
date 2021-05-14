import hashlib
import hmac
from datetime import datetime

import requests
from prettytable import PrettyTable

from settings import SECRET_KEY, API_KEY


# функция получения хэш-а
def create_sha256_signature(key, message):
    byte_key = bytes(key, 'UTF-8')
    message = message.encode()
    return hmac.new(byte_key, message, hashlib.sha256).hexdigest().upper()


# проверка статуса сервера
# print(get_status_api())
def get_status_api():
    url = 'https://binance.com/wapi/v3/systemStatus.html'
    response = requests.post(url)
    return [response.status_code, response.text]


# получение времени сервера
# print(get_server_time())
# print(round(datetime.now().timestamp()*1000))
def get_server_time():
    url = 'https://binance.com/api/v1/time'
    response = requests.post(url)
    return response.json()['serverTime']


# функция получения монет из кошелька
def get_my_many():
    url = 'https://binance.com/api/v3/account'
    headers = {"X-MBX-APIKEY": API_KEY,
               "Content-Type": "application/x-www-form-urlencoded"}
    timestamp = str(round(datetime.now().timestamp() * 1000))
    sign = create_sha256_signature(key=SECRET_KEY, message='timestamp=' + timestamp)
    data = {'timestamp': timestamp,
            'signature': sign}

    response = requests.get(url, headers=headers, params=data).json()
    many = {}

    for item in response['balances']:
        if float(item['free']) != 0:
            many[item['asset']] = item['free']

    return many


# пример запроса курса валюты
# print(get_price('XRPUSDT'))
def get_price(symbol):
    url = 'https://binance.com/api/v3/ticker/price'
    data = {"symbol": symbol}
    response = requests.post(url, params=data)
    return response.json()['price']


# функция получения историй обмена
def get_my_order(symbol):
    url = 'https://binance.com/api/v3/myTrades'
    headers = {"X-MBX-APIKEY": API_KEY,
               "Content-Type": "application/x-www-form-urlencoded"}
    timestamp = str(round(datetime.now().timestamp() * 1000))
    sign = create_sha256_signature(key=SECRET_KEY, message='timestamp=' + timestamp + '&symbol=' + symbol)
    data = {'timestamp': timestamp,
            'symbol': symbol,
            'signature': sign}

    response = requests.get(url, headers=headers, params=data).json()
    return response


def main():
    # получение текущего счета
    my_wallet = get_my_many()

    # общая стоимость кошелька
    wallet_total_cur = 0
    wallet_total_buy = 0

    # json кошелька
    wallet = {}

    # красивый вывод в консоль
    table = PrettyTable(['coin',
                         'quantity',
                         'current price',
                         'purchase price',
                         'total buy',
                         'total current',
                         'delta'])
    table.title = datetime.now().strftime('%d/%m/%y %H:%M')

    # получение информации по активным монетам
    # наименование - количество - сумма покупки - средняя стоимость одной купленной монеты - текущая стоимость
    for coin in my_wallet:
        if coin == 'RUB' or coin == 'USDT':
            continue
        else:
            orders = get_my_order(str(coin) + 'USDT')
            total_price_buy = 0
            total_cnt = 0

            if not orders:
                continue

            for order in orders:
                cnt = float(order['qty']) - float(order['commission'])
                if order['isBuyer']:
                    total_cnt += cnt
                    total_price_buy += float(order['price']) * cnt
                else:
                    total_cnt -= cnt
                    total_price_buy -= float(order['price']) * cnt

            price_cur = get_price(coin+'USDT')
            total_price_cur = float(price_cur) * total_cnt

            wallet[coin] = {
                            'total_cnt': total_cnt,
                            'price_cur': float(price_cur),
                            'price_buy': total_price_buy / total_cnt,
                            'total_price_buy': total_price_buy,
                            'total_price_cur': total_price_cur,
                            'delta_val': total_price_cur - total_price_buy,
                            'delta_percent': (total_price_cur - total_price_buy) / total_price_cur * 100
                            }

            table.add_row([coin,
                           round(wallet[coin]['total_cnt'], 3),
                           round(wallet[coin]['price_cur'], 3),
                           round(wallet[coin]['price_buy'], 3),
                           round(wallet[coin]['total_price_buy'], 3),
                           round(wallet[coin]['total_price_cur'], 3),
                           round(wallet[coin]['delta_val'], 3)])

        wallet_total_buy += total_price_buy
        wallet_total_cur += total_price_cur

    wallet['total_cur'] = wallet_total_cur
    wallet['total_buy'] = wallet_total_buy
    wallet['delta_val'] = wallet_total_cur - wallet_total_buy
    wallet['delta_percent'] = (wallet_total_cur - wallet_total_buy) / wallet_total_cur * 100

    # print(json.dumps(wallet, indent=4, sort_keys=True))
    
    table.add_row(['total',
                   '',
                   '',
                   '',
                   round(wallet['total_buy'], 3),
                   round(wallet['total_cur'], 3),
                   round(wallet['delta_val'], 3)])
    # print(table)

    with open(f"./log_binance/{str(round(datetime.now().timestamp()*1000))}.txt", 'w+') as f:
        # table.sortby
        f.write(table.get_string())


if __name__ == '__main__':
    main()
