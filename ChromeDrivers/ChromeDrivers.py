import os
import time
from datetime import datetime, timedelta

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class ChromeDrivers:
    """
    A class to manage the Chrome WebDriver instance with caching.
    """
    def __init__(self):
        load_dotenv()
        self.driver_path = os.getenv("CHROMEDRIVER_PATH")
        self.refresh_date = os.getenv("CHROMEDRIVER_REFRESH_DATE")
        self.cache_valid = self.is_cache_valid()
        self.headless = True

    def is_cache_valid(self):
        """
        Check if the cached ChromeDriver is still valid based on the refresh date.
        """
        if self.refresh_date:
            refresh_date = datetime.strptime(self.refresh_date, "%Y-%m-%d")
            return datetime.now() < refresh_date + timedelta(days=30)
        return False

    def refresh_cache(self):
        """
        Refresh the cached ChromeDriver and update the refresh date in the .env file.
        """
        try:
            start_time = time.time()
            driver_path = ChromeDriverManager().install()
            end_time = time.time()
            self.time_installation(start_time, end_time)
            self.driver_path = driver_path
            self.refresh_date = datetime.now().strftime("%Y-%m-%d")
            self._write_env_variable("CHROMEDRIVER_PATH", self.driver_path)
            self._write_env_variable("CHROMEDRIVER_REFRESH_DATE", self.refresh_date)
            print(f"✅ ChromeDriver refreshed and cached at: {driver_path} on {self.refresh_date}")
            
        except Exception as e:
            print(f"❌ Error refreshing ChromeDriver: {e}")

    def set_options(self):
        """
        Set up Chrome options for the WebDriver.
        """
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
        return options

    def get_chromedriver(self):
        """
        Initializes and returns a Chrome WebDriver instance with caching.

        :param headless: Run Chrome in headless mode (default: False)
        :return: Selenium WebDriver instance
        """
        try:
            # Set up Chrome options
            options = self.set_options()
            
            if not self.cache_valid:
                print("Cache is invalid. Refreshing ChromeDriver.")
                self.refresh_cache()

            # Set up ChromeDriver service
            service = Service(self.driver_path)
            driver = webdriver.Chrome(service=service, options=options)

            return driver
        except Exception as e:
            print(f"❌ Error initializing ChromeDriver: {e}")
            return None
        
    def _write_env_variable(self, key, value, env_file="../.env"):
        """Writes or updates a key-value pair in the .env file."""
        lines = []
        updated = False

        # Read existing .env file if it exists
        try:
            with open(env_file, "r") as f:
                lines = f.readlines()
        except FileNotFoundError:
            pass  # File doesn't exist yet

        # Update the existing key if found, otherwise add a new one
        with open(env_file, "w") as f:
            for line in lines:
                if line.startswith(f"{key}="):  # Update the existing key
                    f.write(f"{key}={value}\n")
                    updated = True
                else:
                    f.write(line)

            if not updated:  # Add new key if it doesn't exist
                f.write(f"{key}={value}\n")

    @staticmethod
    def time_installation(start_time, end_time):
        """
        Calculate the time taken for installation.
        """
        elapsed_time = end_time - start_time
        duration_minutes = elapsed_time // 60
        remaining_seconds = elapsed_time % 60
        print(f"Installation took {int(duration_minutes)} min {remaining_seconds:.2f} seconds.")

# Example Usage:
if __name__ == "__main__":
    chrome_driver_manager = ChromeDrivers()
    driver = chrome_driver_manager.get_chromedriver()
