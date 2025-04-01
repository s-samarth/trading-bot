from typing import Dict, List, Any, Optional, TypeVar
from pathlib import Path
import json
from pydantic import BaseModel
from ChromeDrivers.ChromeDrivers import ChromeDrivers


class EnvironmentVariable(BaseModel):
    key: str
    value: str

    class Config:
        frozen = True


T = TypeVar('T', bound=BaseModel)


class ChromeDriverConfig(BaseModel):
    """ChromeDriver configuration settings."""
    chrome_driver_path: Optional[str] = ""
    chrome_driver_refresh_date: Optional[str] = ""

    @classmethod
    def from_chrome_driver(cls) -> 'ChromeDriverConfig':
        """Initialize configuration from ChromeDrivers."""
        chrome_driver = ChromeDrivers()
        if not chrome_driver.cache_valid:
            print("Initializing/Updating ChromeDriver...")
            chrome_driver.refresh_cache()
        
        return cls(
            chrome_driver_path=chrome_driver.driver_path or "",
            chrome_driver_refresh_date=chrome_driver.refresh_date or ""
        )


class TelegramBotConfig(BaseModel):
    """Telegram Bot configuration settings."""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    telegram_bot_username: str = ""

    @classmethod
    def from_json(cls, file_path: Path) -> 'TelegramBotConfig':
        if not file_path.exists():
            return cls()
        data = json.loads(file_path.read_text())
        return cls(
            telegram_bot_token=data.get('bot_token', ''),
            telegram_chat_id=data.get('chat_id', ''),
            telegram_bot_username=data.get('bot_username', '')
        )


class ZerodhaAPIConfig(BaseModel):
    """Zerodha API configuration settings."""
    zerodha_user_id: str = ""
    zerodha_password: str = ""
    zerodha_api_key: str = ""
    zerodha_api_secret: str = ""
    zerodha_totp_secret: str = ""
    zerodha_redirect_uri: str = ""
    zerodha_postback_url: Optional[str] = ""

    @classmethod
    def from_json(cls, file_path: Path) -> 'ZerodhaAPIConfig':
        if not file_path.exists():
            return cls()
        data = json.loads(file_path.read_text())
        return cls(
            zerodha_user_id=data.get('user_id', ''),
            zerodha_password=data.get('password', ''),
            zerodha_api_key=data.get('api_key', ''),
            zerodha_api_secret=data.get('api_secret', ''),
            zerodha_totp_secret=data.get('totp_secret', ''),
            zerodha_redirect_uri=data.get('redirect_uri', ''),
            zerodha_postback_url=data.get('postback_url', '')
        )


class UpstoxAPIConfig(BaseModel):
    """Upstox API configuration settings."""
    upstox_api_key: str = ""
    upstox_api_secret: str = ""
    upstox_redirect_uri: str = ""
    upstox_mobile_number: str = ""
    upstox_totp_secret: str = ""
    upstox_mpin: str = ""
    upstox_postback_url: Optional[str] = ""
    upstox_sandbox_access_token: Optional[str] = ""

    @classmethod
    def from_json(cls, file_path: Path) -> 'UpstoxAPIConfig':
        if not file_path.exists():
            return cls()
        data = json.loads(file_path.read_text())
        return cls(
            upstox_api_key=data.get('api_key', ''),
            upstox_api_secret=data.get('api_secret', ''),
            upstox_redirect_uri=data.get('redirect_uri', ''),
            upstox_mobile_number=data.get('mobile_number', ''),
            upstox_totp_secret=data.get('totp_secret', ''),
            upstox_mpin=data.get('mpin', ''),
            upstox_postback_url=data.get('postback_url', ''),
            upstox_sandbox_access_token=data.get('sandbox_access_token', '')
        )


class AngelOneAPIConfig(BaseModel):
    """Angel One API configuration settings."""
    angelone_client_id: str = ""
    angelone_trading_api_key: str = ""
    angelone_secret_key: str = ""
    angelone_mpin: str = ""
    angelone_password: str = ""
    angelone_totp_secret: str = ""
    angelone_redirect_uri: str = ""
    angelone_postback_url: Optional[str] = ""

    @classmethod
    def from_json(cls, file_path: Path) -> 'AngelOneAPIConfig':
        if not file_path.exists():
            return cls()
        data = json.loads(file_path.read_text())
        return cls(
            angelone_client_id=data.get('client_id', ''),
            angelone_trading_api_key=data.get('trading_api_key', ''),
            angelone_secret_key=data.get('secret_key', ''),
            angelone_mpin=data.get('mpin', ''),
            angelone_password=data.get('password', ''),
            angelone_totp_secret=data.get('totp_secret', ''),
            angelone_redirect_uri=data.get('redirect_uri', ''),
            angelone_postback_url=data.get('postback_url', '')
        )


def model_to_env_variables(config: BaseModel) -> List[EnvironmentVariable]:
    """Convert a Pydantic model to a list of environment variables.
    
    Args:
        config: A Pydantic model instance
        
    Returns:
        List of EnvironmentVariable instances
    """
    return [
        EnvironmentVariable(key=key.upper(), value=str(value))
        for key, value in config.model_dump().items()
    ]


def read_env_file(env_file: Path) -> Dict[str, str]:
    """Read and parse an environment file.
    
    Args:
        env_file: Path to the environment file
        
    Returns:
        Dictionary of environment variables
    """
    if not env_file.exists():
        return {}
    
    env_vars = {}
    content = env_file.read_text().splitlines()
    
    for line in content:
        line = line.strip()
        if line and not line.startswith('#'):
            try:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
            except ValueError:
                continue
    
    return env_vars


def write_env_file(env_vars: Dict[str, str], env_file: Path) -> None:
    """Write environment variables to a file.
    
    Args:
        env_vars: Dictionary of environment variables
        env_file: Path to write the environment file
    """
    content = '\n'.join(f"{key}={value}" for key, value in sorted(env_vars.items()))
    env_file.write_text(content + '\n')


def update_env_vars(
    current_vars: Dict[str, str],
    new_vars: List[EnvironmentVariable]
) -> Dict[str, str]:
    """Update environment variables, preserving existing non-empty values.
    
    Args:
        current_vars: Existing environment variables
        new_vars: New environment variables to add/update
        
    Returns:
        Updated dictionary of environment variables
    """
    result = current_vars.copy()
    
    for var in new_vars:
        if var.value or var.key not in result:
            if var.value:  # Only update if new value is non-empty
                result[var.key] = var.value
                
    return result


class EnvironmentManager:
    """Manages environment variable configuration and persistence."""
    
    def __init__(self, secrets_dir: str = "config/secrets"):
        self.secrets_dir = Path(secrets_dir)
        self.configs = [
            ChromeDriverConfig.from_chrome_driver(), 
            TelegramBotConfig.from_json(self.secrets_dir / "telegram.json"),
            ZerodhaAPIConfig.from_json(self.secrets_dir / "zerodha.json"),
            UpstoxAPIConfig.from_json(self.secrets_dir / "upstox.json"),
            AngelOneAPIConfig.from_json(self.secrets_dir / "angelone.json"),
        ]

    def setup_env(self, env_file: str = ".env") -> None:
        """Set up environment variables from configurations.
        
        Args:
            env_file: Path to the environment file
        """
        env_path = Path(env_file)
        
        # Convert all configs to environment variables
        all_vars = [
            var for config in self.configs
            for var in model_to_env_variables(config)
        ]
        
        # Read existing variables
        current_vars = read_env_file(env_path)
        
        # Update with new variables
        updated_vars = update_env_vars(current_vars, all_vars)
        
        # Write back to file
        write_env_file(updated_vars, env_path)


def main():
    """Main entry point for environment setup."""
    env_manager = EnvironmentManager()
    env_manager.setup_env()
    print("Environment variables have been updated in .env")


if __name__ == "__main__":
    main()
