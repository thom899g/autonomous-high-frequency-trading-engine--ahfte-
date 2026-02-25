"""
Configuration Management for AHFTE
Centralized configuration with environment variable support
"""
import os
import json
import logging
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class TradingConfig:
    """Trading-specific configuration"""
    # Exchange settings
    exchange_id: str = "binance"
    trading_pair: str = "BTC/USDT"
    timeframe: str = "1m"
    
    # Trading parameters
    initial_capital: float = 10000.0
    max_position_size: float = 0.1  # 10% of capital
    max_daily_loss: float = 0.02  # 2% daily stop loss
    
    # Risk management
    stop_loss_pct: float = 0.01  # 1%
    take_profit_pct: float = 0.02  # 2%
    max_open_positions: int = 3
    
    # Model parameters
    lookback_period: int = 100
    prediction_horizon: int = 5
    model_update_frequency: int = 3600  # seconds
    
    # Execution
    order_timeout: int = 30  # seconds
    max_slippage: float = 0.001  # 0.1%
    
    def validate(self) -> bool:
        """Validate configuration values"""
        if self.initial_capital <= 0:
            raise ValueError("Initial capital must be positive")
        if not 0 < self.max_position_size <= 1:
            raise ValueError("Max position size must be between 0 and 1")
        if self.stop_loss_pct <= 0:
            raise ValueError("Stop loss must be positive")
        return True

@dataclass
class FirebaseConfig:
    """Firebase configuration"""
    project_id: str = os.getenv("FIREBASE_PROJECT_ID", "")
    credentials_path: str = os.getenv("FIREBASE_CREDENTIALS_PATH", "")
    database_url: str = os.getenv("FIREBASE_DATABASE_URL", "")
    
    def validate(self) -> bool:
        """Validate Firebase configuration"""
        required = ["project_id", "credentials_path", "database_url"]
        for field in required:
            if not getattr(self, field):
                raise ValueError(f"Firebase {field} is required")
        return True

@dataclass
class APIConfig:
    """API credentials configuration"""
    exchange_api_key: str = os.getenv("EXCHANGE_API_KEY", "")
    exchange_api_secret: str = os.getenv("EXCHANGE_API_SECRET", "")
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")
    
    def validate(self) -> bool:
        """Validate API credentials"""
        if not self.exchange_api_key or not self.exchange_api_secret:
            logging.warning("Exchange API credentials not configured")
        return True

class ConfigManager:
    """Central configuration manager with validation"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/trading_config.json"
        self.trading = TradingConfig()
        self.firebase = FirebaseConfig()
        self.api = APIConfig()
        self._load_from_file()
        self._validate_all()
        
    def _load_from_file(self) -> None:
        """Load configuration from JSON file if exists"""
        try:
            if Path(self.config_path).exists():
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    self.trading = TradingConfig(**data.get('trading', {}))
                    self.firebase = FirebaseConfig(**data.get('firebase', {}))
                    self.api = APIConfig(**data.get('api', {}))
                logging.info(f"Configuration loaded from {self.config_path}")
        except Exception as e:
            logging.warning(f"Failed to load config file: {e}")
    
    def _validate_all(self) -> None:
        """Validate all configuration sections"""
        try:
            self.trading.validate()
            self.firebase.validate()
            self.api.validate()
            logging.info("All configurations validated successfully")
        except Exception as e:
            logging.error(f"Configuration validation failed: {e}")
            raise
    
    def save(self) -> None:
        """Save current configuration to file"""
        try:
            Path(self.config_path).parent.mkdir(exist_ok=True)
            data = {
                'trading': asdict(self.trading),
                'firebase': asdict(self.firebase),
                'api