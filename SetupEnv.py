from typing import List, Any, Optional
from pydantic import BaseModel


class EnvironmentVariable(BaseModel):
    KEY: str
    VALUE: str


class ChromeDriverConfig(BaseModel):
    """ChromeDriver configuration class.
    This class is used to store the configuration for the ChromeDriver.
    Populate it with your own values. Remove any keys you don't need.
    """

    # ChromeDriver configuration
    CHROME_DRIVER_PATH: Optional[str] = ""
    CHROME_DRIVER_REFRESH_DATE: Optional[str] = ""


class TelegramBotConfig(BaseModel):
    """Telegram Bot configuration class.
    This class is used to store the configuration for the Telegram Bot.
    Populate it with your own values. Remove any keys you don't need.
    """

    # Telegram Bot configuration
    TELEGRAM_BOT_TOKEN: str = "YOUR_TELEGRAM_BOT_TOKEN"
    TELEGRAM_CHAT_ID: str = "YOUR_TELEGRAM_CHAT_ID"
    TELEGRAM_BOT_USERNAME: str = "YOUR_TELEGRAM_BOT_USERNAME"


class ZerodhaAPIConfig(BaseModel):
    """Zerodha configuration class.
    This class is used to store the configuration for the Zerodha API.
    Populate it with your own values. Remove any keys you don't need.
    """

    # Zerodha API configuration
    ZERODHA_USER_ID: str = "YOUR_ZERODHA_USER_ID"
    ZERODHA_PASSWORD: str = "YOUR_ZERODHA_PASSWORD"
    ZERODHA_API_KEY: str = "YOUR_ZERODHA_API_KEY"
    ZERODHA_API_SECRET: str = "YOUR_ZERODHA_API_SECRET"
    ZERODHA_TOTP_SECRET: str = "YOUR_ZERODHA_TOTP_SECRET"
    ZERODHA_REDIRECT_URI: str = "YOUR_ZERODHA_REDIRECT_URI"
    ZERODHA_POSTBACK_URL: Optional[str] = ""


class UpstoxAPIConfig(BaseModel):
    """Upstox configuration class.
    This class is used to store the configuration for the Upstox API.
    Populate it with your own values. Remove any keys you don't need.
    """

    # Upstox API configuration
    UPSTOX_API_KEY: str = "YOUR_UPSTOX_API_KEY"
    UPSTOX_API_SECRET: str = "YOUR_UPSTOX_API_SECRET"
    UPSTOX_REDIRECT_URI: str = "YOUR_UPSTOX_REDIRECT_URI"
    UPSTOX_MOBILE_NUMBER: str = "YOUR_UPSTOX_MOBILE_NUMBER"
    UPSTOX_TOTP_SECRET: str = "YOUR_UPSTOX_TOTP_SECRET"
    UPSTOX_MPIN: str = "YOUR_UPSTOX_MPIN"
    UPSTOX_POSTBACK_URL: Optional[str] = ""
    UPSTOX_SANDBOX_ACCESS_TOKEN: Optional[str] = ""


class AngelOneAPIConfig(BaseModel):
    """Angel One configuration class.
    This class is used to store the configuration for the Angel One API.
    Populate it with your own values. Remove any keys you don't need.
    """

    # AngelOne API configuration
    ANGELONE_CLIENT_ID: str = "YOUR_ANGELONE_CLIENT_ID"
    ANGELONE_TRADING_API_KEY: str = "YOUR_ANGELONE_TRADING_API_KEY"
    ANGELONE_SECRET_KEY: str = "YOUR_ANGELONE_SECRET_KEY"
    ANGELONE_MPIN: str = "YOUR_ANGELONE_MPIN"
    ANGELONE_PASSWORD: str = "YOUR_ANGELONE_PASSWORD"
    ANGELONE_TOTP_SECRET: str = "YOUR_ANGELONE_TOTP_SECRET"
    ANGELONE_REDIRECT_URI: str = "YOUR_ANGELONE_REDIRECT_URI"
    ANGELONE_POSTBACK_URL: Optional[str] = ""


class SetupEnv:
    """SetupEnv class.
    This class is used to set up the environment variables for the application.
    It reads the configuration from the config file and writes it to the .env file.
    """

    def __init__(self):
        """
        Initializes the SetupEnv class.
        Remove any configurations you don't need.
        """
        self.chrome_driver_config = ChromeDriverConfig()
        self.telegram_bot_config = TelegramBotConfig()
        self.zerodha_api_config = ZerodhaAPIConfig()
        self.upstox_api_config = UpstoxAPIConfig()
        self.angel_one_api_config = AngelOneAPIConfig()

        self.configs = [
            self.chrome_driver_config,
            self.telegram_bot_config,
            self.zerodha_api_config,
            self.upstox_api_config,
            self.angel_one_api_config,
        ]

    def setup_env(self, env_file=".env"):
        """Sets up the environment variables for the application.
        Reads the configuration from the config file and writes it to the .env file.
        """
        env_variables = self.get_all_env_variables()
        self.write_env_variables(env_variables, env_file)

    def get_all_env_variables(self) -> List[EnvironmentVariable]:
        """Returns a list of environment variables.
        Remove any configurations you don't need."""
        env_variables = []

        # Iterate through each configuration and get the environment variables
        for config in self.configs:
            env_variables.extend(self.get_config_env_variables(config))
        return env_variables

    def get_config_env_variables(self, config: Any) -> List[EnvironmentVariable]:
        """Returns a list of environment variables."""
        env_variables = []
        for key, value in config:
            env_variable = EnvironmentVariable(KEY=key, VALUE=value)
            env_variables.append(env_variable)
        return env_variables

    def write_env_variables(
        self, env_variables: List[EnvironmentVariable], env_file=".env"
    ):
        """Writes or updates a key-value pair in the .env file."""
        lines = []
        updated = False

        # Read existing .env file if it exists
        try:
            with open(env_file, "r") as f:
                lines = f.readlines()
        except FileNotFoundError:
            print(f"File {env_file} not found. Creating a new one.")
            pass  # File doesn't exist yet

        # Update the existing key if found, otherwise add a new one
        with open(env_file, "w") as f:
            for env_variable in env_variables:
                key = env_variable.KEY
                value = env_variable.VALUE
                if value == "":
                    print(f"Skipping empty value for key: {key}")
                    continue
                for line in lines:
                    if line.startswith(f"{key}="):  # Update the existing key
                        f.write(f"{key}={value}\n")
                        updated = True
                    else:
                        f.write(line)

                if not updated:  # Add new key if it doesn't exist
                    f.write(f"{key}={value}\n")


if __name__ == "__main__":
    # Example usage
    SetupEnv().setup_env()
    print("Environment variables written to .env.demo")
