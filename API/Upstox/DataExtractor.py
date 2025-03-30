import os
import gzip
import shutil
import json

class DataExtractor:
    def __init__(self):
        pass

    def load_upstox_data(self, file_path) -> dict:
        """
        Loads Upstox data from a specified file path.

        :param file_path: Path to the Upstox data json file.
        :return: Loaded data as a dictionary.
        """
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
            print(f"✅ Loaded data from {file_path}")
            return data
        except FileNotFoundError:
            print(f"❌ File not found: {file_path}")
            return None
        except Exception as e:
            print(f"❌ Error loading data from {file_path}: {e}")
            return None
        


    def extract_gzip_file(self, gzip_file_path, output_file_path):
        """
        Extracts a gzip file and saves the output to a specified path.

        :param
        gzip_file_path: Path to the gzip file to be extracted.
        :param output_file_path: Path where the extracted file will be saved.
        """
        try:
            with gzip.open(gzip_file_path, 'rb') as f_in:
                with open(output_file_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            print(f"✅ Extracted {gzip_file_path} to {output_file_path}")
        except Exception as e:
            print(f"❌ Error extracting {gzip_file_path}: {e}")


if __name__ == "__main__":
    # Example usage
    extractor = DataExtractor()
    # extractor.extract_gzip_file("UpstoxData/complete.json.gz", "UpstoxData/complete.json")
    data = extractor.load_upstox_data("UpstoxData/complete.json")
    if data:
        print(f"Data: {data[0]}")
    else:
        print("Failed to load data.")
