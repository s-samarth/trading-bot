# Trading Bot

An automated trading bot that integrates with multiple trading platforms. Currently, only Upstox API integration is fully functional.

## ⚠️ Critical Requirements

Before starting, ensure you have:
1. Enabled TOTP-based Authentication in your Upstox account
2. Saved the TOTP secret key (shown below/next to QR code during setup)
3. Enabled DDPI (Delivery vs Payment Instruction) in Upstox for automated selling
   - ⚠️ Read DDPI terms carefully as it involves risks
   - Required to avoid TPIN for selling securities
4. A valid HTTPS URL for REDIRECT_URI

## Quick Start

1. Set up Python environment:
```bash
conda create -n trading_env python=3.13.2
conda activate trading_env
pip install -r requirements.txt
```

2. Configure Upstox credentials:
```bash
cp config/secrets/upstox.template.json config/secrets/upstox.json
```

Edit `config/secrets/upstox.json`:
```json
{
    "api_key": "your_api_key",
    "api_secret": "your_api_secret",
    "redirect_uri": "your_redirect_uri",
    "mobile_number": "your_mobile",
    "totp_secret": "your_totp_secret",
    "mpin": "your_mpin",
    "postback_url": "optional_postback_url",
    "sandbox_access_token": "optional_sandbox_token"
}
```

3. Run setup:
```bash
python SetupEnv.py
```
```

4. Start the bot:
```bash
cd TradingStrategy
python demo.py
```

## Features

- ✅ Upstox API integration
- ✅ Automated ChromeDriver management
- 🚧 Zerodha integration (coming soon)
- 🚧 Angel One integration (coming soon)
- Secure configuration management
- Telegram notifications
- Automated trading strategies

## Security

- Never commit credentials to git
- `.env` and `config/secrets/*.json` are gitignored
- Only template files are committed

## License

MIT License - see LICENSE file for details

