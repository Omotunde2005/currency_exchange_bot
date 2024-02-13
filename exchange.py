import requests


class CurrencyExchange:

    def __init__(self, api_key):
        self.key = api_key
        self.codes = ["ARS", "AUD", "BCH", "BGN", "BNB", "BRL", "BTC", "CAD", "CHF", "CNY", "CZK", "DKK", "DOGE",
                      "DZD", "ETH", "EUR", "GBP", "HKD", "HRK", "HUF", "IDR", "ILS", "INR", "ISK", "JPY", "KRW",
                      "LTC", "MAD", "MXN", "MYR", "NOK", "NZD", "PHP", "PLN", "RON", "RUB", "SEK", "SGD", "THB",
                      "TRY", "TWD", "XRP", "ZAR", "USD"]

    def single_exchange(self, params):
        url = "https://exchange-rates.abstractapi.com/v1/convert"
        params['api_key'] = self.key
        res = requests.request("GET", url, params=params)
        return res.json()

    def multiple_exchange(self, params):
        url = "https://exchange-rates.abstractapi.com/v1/live"
        params['api_key'] = self.key
        res = requests.request("GET", url, params=params)
        return res.json()

    def is_valid_currency(self, currency):
        if currency in self.codes:
            return True
        else:
            return False

    def is_valid_currencies(self, currencies_list):
        if all(currency in self.codes for currency in currencies_list):
            return True
        else:
            return False