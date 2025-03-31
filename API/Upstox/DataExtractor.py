import os
import gzip
import shutil
import json
from typing import Dict

from Constants import Exchange

def generate_instrument_token(trading_symbol: str, exchange: Exchange):
    """
    Generates the instrument token for a given symbol and exchange.

    :param symbol: Trading symbol to look up.
    :param exchange: Exchange to look up.
    :return: Instrument token.
    """
    if exchange == Exchange.NSE:
        extractor = DataExtractor()
        trading_instrument = extractor.get_nse_trading_instrument_for_symbol(trading_symbol)
        return trading_instrument
            
    elif exchange == Exchange.BSE:
        raise NotImplementedError("BSE exchange is not supported yet.")
    
    elif exchange == Exchange.NFO:
        raise NotImplementedError("NFO exchange is not supported yet.")
    
    elif exchange == Exchange.BFO:
        raise NotImplementedError("BFO exchange is not supported yet.")
    
    elif exchange == Exchange.CDS:
        raise NotImplementedError("CDS exchange is not supported yet.")
    
    elif exchange == Exchange.BCD:
        raise NotImplementedError("BCD exchange is not supported yet.")
    
    elif exchange == Exchange.NSCOM:
        raise NotImplementedError("NSCOM exchange is not supported yet.")
    
    elif exchange == Exchange.MCX:
        raise NotImplementedError("MCX exchange is not supported yet.")
    
    else:
        raise ValueError(f"Unsupported exchange: {exchange}. Please provide a valid exchange.")

class DataExtractor:
    def __init__(self, gzip_file_path="UpstoxData/complete.json.gz", 
                 output_file_path="UpstoxData/complete.json", 
                 complete_data_upstox_path="UpstoxData/complete.json", 
                 nse_data_eq_path="UpstoxData/nse_eq.json", 
                 nse_trading_symbol_to_isin_path="UpstoxData/symbol_to_isin.json"):
        self.gzip_file_path = gzip_file_path
        self.output_file_path = output_file_path
        self.complete_data_upstox_path = complete_data_upstox_path
        self.nse_data_eq_path = nse_data_eq_path
        self.nse_trading_symbol_to_isin_path = nse_trading_symbol_to_isin_path
        
    def load_complete_upstox_data(self) -> dict:
        """
        Loads Upstox data from a specified file path.

        :param file_path: Path to the Upstox data json file.
        :return: Loaded data as a dictionary.
        """
        try:
            with open(self.complete_data_upstox_path, 'r') as file:
                data = json.load(file)
            print(f"✅ Loaded data from {self.complete_data_upstox_path}")
            return data
        except FileNotFoundError:
            print(f"❌ File not found: {self.complete_data_upstox_path}")
            return None
        except Exception as e:
            print(f"❌ Error loading data from {self.complete_data_upstox_path}: {e}")
            return None

    def extract_gzip_file(self):
        """
        Extracts a gzip file and saves the output to a specified path.

        :param
        gzip_file_path: Path to the gzip file to be extracted.
        :param output_file_path: Path where the extracted file will be saved.
        """
        try:
            with gzip.open(self.gzip_file_path, 'rb') as f_in:
                with open(self.output_file_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            print(f"✅ Extracted {self.gzip_file_path} to {self.output_file_path}")
        except Exception as e:
            print(f"❌ Error extracting {self.gzip_file_path}: {e}")

    def extract_nse_eq_data(self, save_data=True):
        """
        Extracts NSE_EQ data from the loaded data.

        :param data: file path to the Upstox data json file.
        :return: Filtered NSE_EQ data.
        """
        data = self.load_complete_upstox_data()
        if data is None:
            print("❌ Failed to load data.")
            return None
        # Filter the data for NSE_EQ segment
        nse_eq_data = [entry for entry in data if entry.get('segment') == 'NSE_EQ' and entry.get('exchange') == 'NSE' and entry.get('instrument_type') == 'EQ']
        if len(nse_eq_data) == 0:
            print("❌ No NSE_EQ data found.")
            return None
        print(f"✅ Extracted NSE_EQ data from {self.complete_data_upstox_path} with {len(nse_eq_data)} entries.")

        try: 
            symbols = {entry['trading_symbol'] for entry in nse_eq_data}
            assert len(nse_eq_data) == len(symbols), "Trading Symbols are not unique in NSE EQ data."
        except AssertionError as e:
            print(f"Assertion Error: {e}")
            print(f"Items in NSE_EQ Data: {len(nse_eq_data)}")
            print(f"Items in symbols: {len(symbols)}")
            return None
        
        if save_data:
            try:
                self.save_nse_eq_data(nse_eq_data)
                
            except Exception as e:
                print(f"❌ Error saving NSE_EQ data: {e}")
                return None

        return nse_eq_data
    
    def save_nse_eq_data(self, nse_eq_data: Dict):
        """
        Saves the extracted NSE_EQ data to a specified file path.

        :param nse_eq_data: Filtered NSE_EQ data.
        """
        
        if nse_eq_data is None:
            print("❌ Failed to extract NSE_EQ data.")
            return None
        try:
            with open(self.nse_data_eq_path, 'w') as file:
                json.dump(nse_eq_data, file)
            print(f"✅ Saved NSE_EQ data to {self.nse_data_eq_path}")
        except Exception as e:
            print(f"❌ Error saving NSE_EQ data to {self.nse_data_eq_path}: {e}")

    def load_nse_eq_data(self):
        """
        Loads NSE_EQ data from a specified file path.

        :param nse_data_eq_path: Path to the NSE_EQ data json file.
        :return: Loaded NSE_EQ data as a dictionary.
        """
        try:
            with open(self.nse_data_eq_path, 'r') as file:
                data = json.load(file)
            print(f"✅ Loaded NSE_EQ data from {self.nse_data_eq_path}")
            return data
        except FileNotFoundError:
            print(f"❌ File not found: {self.nse_data_eq_path}")
            return None
        except Exception as e:
            print(f"❌ Error loading NSE_EQ data from {self.nse_data_eq_path}: {e}")
            return None

    def get_nse_trading_symbol_to_isin_map(self): 
        """
        Maps trading symbols to ISINs from the NSE_EQ data.
        ISIN are International Securities Identification Number.

        :return: Dictionary mapping trading symbols to ISINs.
        """
        nse_eq_data = self.load_nse_eq_data()
        symbol_to_isin = {entry['trading_symbol']: entry['isin'] for entry in nse_eq_data}
        print(f"✅ Mapped {len(symbol_to_isin)} trading symbols to ISINs.")
        self.save_nse_trading_symbol_to_isin_map(symbol_to_isin)
        return symbol_to_isin
    
    def save_nse_trading_symbol_to_isin_map(self, symbol_to_isin):
        """
        Saves the trading symbol to ISIN mapping to a specified file path.

        :param symbol_to_isin: Dictionary mapping trading symbols to ISINs.
        """
        try:
            with open(self.nse_trading_symbol_to_isin_path, 'w') as file:
                json.dump(symbol_to_isin, file)
            print(f"✅ Saved trading symbol to ISIN mapping to {self.nse_trading_symbol_to_isin_path}")
        except Exception as e:
            print(f"❌ Error saving trading symbol to ISIN mapping: {e}")
        return None
    
    def load_nse_trading_symbol_to_isin_map(self) -> Dict:
        """
        Loads the trading symbol to ISIN mapping from a specified file path.

        :return: Dictionary mapping trading symbols to ISINs.
        """
        with open(self.nse_trading_symbol_to_isin_path, 'r') as file:
            symbol_to_isin = json.load(file)
        return symbol_to_isin

    
    def get_nse_trading_instrument_for_symbol(self, symbol):
        """
        Retrieves the trading instrument for a given symbol.

        :param symbol: Trading symbol to look up.
        :return: Dictionary containing trading instrument details.
        """
        try: 
            symbol_to_isin = self.load_nse_trading_symbol_to_isin_map()
        except Exception as e:
            print(f"❌ Error loading trading symbol to ISIN mapping: {e}")
            symbol_to_isin = self.get_nse_trading_symbol_to_isin_map()

        if symbol in symbol_to_isin.keys():
            isin = symbol_to_isin[symbol]
            trading_instrument = f"NSE_EQ|{isin}"
            # print(f"✅ Found trading instrument for symbol {symbol}: {trading_instrument}")
            return trading_instrument
        else:
            raise ValueError(f"❌ Symbol {symbol} not found in NSE_EQ data.")
        

if __name__ == "__main__":
    # Example usage
    extractor = DataExtractor()
    # nse_eq_data = extractor.extract_nse_eq_data()
    # nse_eq_data = extractor.load_nse_eq_data()
    trading_symbol = "RELIANCE"
    trading_instrument = extractor.get_nse_trading_instrument_for_symbol(trading_symbol)
    print(f"Trading instrument for {trading_symbol}: {trading_instrument}")
