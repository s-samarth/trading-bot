# trading-bot
I Aim to make a completely automated trading bot which is going to make a lot of money.

Currently Only Upstox API is fully functional and Up and Running.
You will need to enable TOPT based Authentication in Upstox first and then
you can fetch the UPSTOX_TOTP_SECRET(click for key under the TOTP QR while enabling)
REDIRECT_URI can be set to any valid HTTPS link.
To ensure selling of Delivery Based Securities Automatically in Upstox, Enable 
DDPI(read the terms and conditions first as it is risky) to avoid selling using TPIN.

Refer to TradingStrategy/demo.py for now

Clone this Repo and follow the below instructions

### Running Instructions
1) Setup the environment for running
```bash
conda create -n trading_env python=3.13.2
pip install -r requirements.txt
```

2) Setup Environment Variables, Enter your environment variables in SetupEnv.py and run
```python
python SetupEnv.py
``` 

3) Run python main.py
```
python main.py
```

