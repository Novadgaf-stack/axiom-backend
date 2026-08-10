"""
Central configuration. Everything sensitive comes from environment variables —
nothing is ever hardcoded here. Copy .env.example to .env for local dev;
on Render, set these in the service's Environment settings.
"""
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


def _bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


def _float(name: str, default: float) -> float:
    val = os.getenv(name)
    return float(val) if val not in (None, "") else default


def _int(name: str, default: int) -> int:
    val = os.getenv(name)
    return int(val) if val not in (None, "") else default


def _list(name: str, default: list[str], upper: bool = False) -> list[str]:
    val = os.getenv(name)
    if not val:
        return default
    parts = [p.strip() for p in val.split(",") if p.strip()]
    return [p.upper() for p in parts] if upper else parts


@dataclass(frozen=True)
class Settings:
    # --- Exchange (Binance) ---
    binance_api_key: str = field(default_factory=lambda: os.getenv("BINANCE_API_KEY", ""))
    binance_api_secret: str = field(default_factory=lambda: os.getenv("BINANCE_API_SECRET", ""))
    # Hard safety default: TRUE. Flipping this to run on mainnet must be a
    # deliberate, explicit act — never a default.
    binance_testnet: bool = field(default_factory=lambda: _bool("BINANCE_TESTNET", True))

    # --- Gemini ---
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    gemini_model: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-2.0-flash"))

    # --- Trading universe ---
    trading_pairs: list[str] = field(default_factory=lambda: _list("TRADING_PAIRS", ["BTC/USDT", "ETH/USDT"], upper=True))
    timeframe: str = field(default_factory=lambda: os.getenv("TIMEFRAME", "15m"))
    ohlcv_lookback: int = field(default_factory=lambda: _int("OHLCV_LOOKBACK", 200))
    poll_interval_seconds: int = field(default_factory=lambda: _int("POLL_INTERVAL_SECONDS", 60))

    # --- Decision gating ---
    min_confidence_score: int = field(default_factory=lambda: _int("MIN_CONFIDENCE_SCORE", 85))
    require_technical_confirmation: bool = field(
        default_factory=lambda: _bool("REQUIRE_TECHNICAL_CONFIRMATION", True)
    )

    # --- Risk management ---
    risk_per_trade_pct: float = field(default_factory=lambda: _float("RISK_PER_TRADE_PCT", 0.5))  # % of equity risked per trade
    max_position_pct: float = field(default_factory=lambda: _float("MAX_POSITION_PCT", 10.0))  # cap notional as % of equity
    max_open_positions: int = field(default_factory=lambda: _int("MAX_OPEN_POSITIONS", 3))
    max_daily_loss_pct: float = field(default_factory=lambda: _float("MAX_DAILY_LOSS_PCT", 3.0))
    atr_period: int = field(default_factory=lambda: _int("ATR_PERIOD", 14))
    atr_sl_multiplier: float = field(default_factory=lambda: _float("ATR_SL_MULTIPLIER", 1.5))
    atr_tp_multiplier: float = field(default_factory=lambda: _float("ATR_TP_MULTIPLIER", 3.0))
    min_volume_ratio: float = field(default_factory=lambda: _float("MIN_VOLUME_RATIO", 0.7))
    cooldown_minutes_after_loss: int = field(default_factory=lambda: _int("COOLDOWN_MINUTES_AFTER_LOSS", 30))
    max_slippage_pct: float = field(default_factory=lambda: _float("MAX_SLIPPAGE_PCT", 0.15))
    max_price_staleness_pct: float = field(default_factory=lambda: _float("MAX_PRICE_STALENESS_PCT", 1.0))
    min_trade_notional_usd: float = field(default_factory=lambda: _float("MIN_TRADE_NOTIONAL_USD", 10.0))

    # --- Safety switches ---
    trading_enabled: bool = field(default_factory=lambda: _bool("TRADING_ENABLED", True))
    dry_run: bool = field(default_factory=lambda: _bool("DRY_RUN", False))

    # --- API / infra ---
    api_auth_token: str = field(default_factory=lambda: os.getenv("API_AUTH_TOKEN", ""))
    allowed_origins: list[str] = field(
        default_factory=lambda: _list("ALLOWED_ORIGINS", ["http://localhost:3000"])
    )
    database_path: str = field(default_factory=lambda: os.getenv("DATABASE_PATH", "./data/engine.db"))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    port: int = field(default_factory=lambda: _int("PORT", 10000))

    def validate(self) -> list[str]:
        """Returns a list of human-readable problems. Empty list = OK to start."""
        problems = []
        if not self.binance_api_key or not self.binance_api_secret:
            problems.append("BINANCE_API_KEY / BINANCE_API_SECRET are not set.")
        if not self.gemini_api_key:
            problems.append("GEMINI_API_KEY is not set.")
        if not self.api_auth_token:
            problems.append("API_AUTH_TOKEN is not set (control endpoints would be unprotected).")
        if not self.binance_testnet:
            problems.append(
                "BINANCE_TESTNET is False — this engine would place REAL orders on mainnet. "
                "This must be a deliberate choice, not an accident."
            )
        if not (0 <= self.min_confidence_score <= 100):
            problems.append("MIN_CONFIDENCE_SCORE must be between 0 and 100.")
        return problems


settings = Settings()
