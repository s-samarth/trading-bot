# Trading Bot

An automated trading bot that integrates with multiple trading platforms including Upstox, Zerodha, and Angel One.

> **⚠️ Important Note**: Currently, only the Upstox API integration is fully functional and operational. Other platform integrations are under development.

## Features

- ✅ Upstox API integration (fully functional)
- ✅ Automated ChromeDriver management
- 🚧 Zerodha integration (coming soon)
- 🚧 Angel One integration (coming soon)
- Secure configuration management
- Telegram notifications
- Automated trading strategies

## Setup Instructions

### 1. Environment Setup

Create and activate a Python virtual environment:
```bash
conda create -n trading_env python=3.13.2
conda activate trading_env
pip install -r requirements.txt
```

### 2. Upstox Account Setup (Required)

Before proceeding with configuration, you must set up TOTP authentication in your Upstox account:

1. Log in to your Upstox account
2. Navigate to the security settings
3. Enable TOTP-based Authentication
4. **IMPORTANT**: When the TOTP QR code is displayed, look for the key shown below or next to the QR code
5. Save this key - this will be your `UPSTOX_TOTP_SECRET` in the configuration

Without completing this TOTP setup, the bot will not be able to authenticate with Upstox.

### 3. Configuration Setup

The project uses a secure configuration system that keeps sensitive data out of version control.

a) First, copy the template files:
```bash

# Copy template files
cp config/secrets/upstox.template.json config/secrets/upstox.json
```

b) Edit the Upstox configuration file with your credentials:

**Upstox Configuration** (`config/secrets/upstox.json`):
```json
{
    "api_key": "your_api_key",
    "api_secret": "your_api_secret",
    "redirect_uri": "your_redirect_uri",
    "mobile_number": "your_mobile",
    "totp_secret": "your_totp_secret",  # The key from TOTP QR setup
    "mpin": "your_mpin",
    "postback_url": "optional_postback_url",
    "sandbox_access_token": "optional_sandbox_token"
}
```

> **⚠️ Critical**: The `totp_secret` must be copied from the Upstox TOTP setup screen when enabling TOTP authentication. This key appears under or alongside the QR code.

### 4. Environment and ChromeDriver Setup

Run the setup script to:
- Configure environment variables
- Download and install the appropriate ChromeDriver version
- Cache the driver location
- Set up automatic driver updates
- Configure headless mode (default: enabled)

```bash
python SetupEnv.py
```

Note: You can also manually manage ChromeDriver if needed:
```bash
python ChromeDrivers/ChromeDrivers.py
```

### 5. Run the Bot

```bash
cd TradingStrategy
python demo.py
```

## Development Status

- **Upstox Integration**: ✅ Fully functional
  - Complete API integration
  - TOTP authentication support
  - Real-time data streaming
  - Order placement and management
  
- **Other Platforms**: 🚧 Under Development
  - Zerodha integration planned
  - Angel One integration planned

For examples and usage, refer to `TradingStrategy/demo.py`.

## Security Notes

1. Never commit actual credentials to git
2. The `.env` file and `config/secrets/*.json` files are gitignored
3. Only template files are committed to the repository

## Future Platform Support

While only Upstox is currently functional, we plan to add support for:

### Zerodha Setup (Coming Soon)
1. Create an API key from the Zerodha developer console
2. Enable TOTP if not already enabled
3. Configure the redirect URI in your Zerodha developer settings

### Angel One Setup (Coming Soon)
1. Register for API access in the Angel One developer portal
2. Generate your API credentials
3. Configure the redirect URI in your Angel One settings

### Telegram Setup (Optional)
1. Create a new bot using BotFather
2. Get your chat ID by sending a message to your bot and accessing https://api.telegram.org/bot<YourBOTToken>/getUpdates
3. Configure the bot token and chat ID in the telegram configuration

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

