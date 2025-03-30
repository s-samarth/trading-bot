from SmartApi import SmartConnect

class Data:
    def __init__(self, smart_api: SmartConnect):
        self.smart_api = smart_api

    def get_profile(self):
        """Get user profile"""
        pass

    def get_ltp(self, exchange, symbol, symbol_token):
        """Get the LTP of a symbol"""
        data = self.smart_api.ltpData(exchange, symbol, symbol_token)
        return data
    
    def get_ohlcv(self, exchange, symbol, symbol_token, interval, from_date, to_date):
        """Get OHLCV data for a symbol"""
        data = self.smart_api.getCandleData(exchange, symbol, symbol_token, interval, from_date, to_date)
        return data

