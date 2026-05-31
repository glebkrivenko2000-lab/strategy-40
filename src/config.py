import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Credentials
    API_KEY = os.getenv('BYBIT_API_KEY', '')
    API_SECRET = os.getenv('BYBIT_API_SECRET', '')
    IS_TESTNET = os.getenv('IS_TESTNET', 'True').lower() == 'true'

    # Telegram Credentials
    TG_TOKEN = os.getenv('TG_TOKEN', '')
    TG_CHAT_ID = os.getenv('TG_CHAT_ID', '')

    # Trading Parameters
    TRADE_AMOUNT_USDT = 50.0
    MAX_POSITIONS = 2
    TOP_N_COINS = 40
    
    # Strategy Logic (Base Defaults)
    LOOKBACK_HOURS = 96
    STOP_LOSS_PCT = 0.05
    MIN_ER_THRESHOLD = 0.04

    # Path Settings
    STATE_FILE = 'data/bot_state.json'
