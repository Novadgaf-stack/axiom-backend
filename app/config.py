"""
Central configuration. Everything sensitive comes from environment variables —
nothing is ever hardcoded here. Copy .env.example to .env for local dev;
on Render, set these in the service's Environment settings.
"""
import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


def _proxy(name: str) -> Optional[str]:
    val = os.getenv(name)
    if not val:
        val = os.getenv("PROXY_URL")
    return val if val else None


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
    # --- Exchange ---
    data_exchange_id: str = field(default_factory=lambda: os.getenv("DATA_EXCHANGE_ID", "bybit"))
    execution_exchange_id: str = field(default_factory=lambda: os.getenv("EXECUTION_EXCHANGE_ID", "binance"))
    http_proxy: Optional[str] = field(default_factory=lambda: _proxy("HTTP_PROXY"))
    https_proxy: Optional[str] = field(default_factory=lambda: _proxy("HTTPS_PROXY"))
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

    # --- Decision gating & filters ---
    min_confidence_score: int = field(default_factory=lambda: _int("AI_MIN_CONFIDENCE", _int("MIN_CONFIDENCE_SCORE", 88)))
    require_technical_confirmation: bool = field(
        default_factory=lambda: _bool("REQUIRE_TECHNICAL_CONFIRMATION", True)
    )
    min_adx: float = field(default_factory=lambda: _float("MIN_ADX", 20.0))
    enable_session_filter: bool = field(default_factory=lambda: _bool("ENABLE_SESSION_FILTER", False))
    session_start_hour: int = field(default_factory=lambda: _int("SESSION_START_HOUR", 12))  # UTC
    session_end_hour: int = field(default_factory=lambda: _int("SESSION_END_HOUR", 20))      # UTC

    # --- Risk management & Position Sizing ---
    risk_per_trade_pct: float = field(default_factory=lambda: _float("RISK_PER_TRADE_PCT", 0.5))  # % of equity risked per trade
    confidence_scaling_enabled: bool = field(default_factory=lambda: _bool("CONFIDENCE_SCALING_ENABLED", True))
    enable_multi_stage_exits: bool = field(default_factory=lambda: _bool("ENABLE_MULTI_STAGE_EXITS", True))
    t1_tp_multiplier: float = field(default_factory=lambda: _float("T1_TP_MULTIPLIER", 1.5))
    t2_tp_multiplier: float = field(default_factory=lambda: _float("T2_TP_MULTIPLIER", 3.0))
    max_position_pct: float = field(default_factory=lambda: _float("MAX_POSITION_PCT", 10.0))  # cap notional as % of equity
    max_open_positions: int = field(default_factory=lambda: _int("MAX_OPEN_POSITIONS", 3))
    max_daily_loss_pct: float = field(default_factory=lambda: _float("MAX_DAILY_LOSS_PCT", 3.0))
    atr_period: int = field(default_factory=lambda: _int("ATR_PERIOD", 14))
    atr_sl_multiplier: float = field(default_factory=lambda: _float("ATR_SL_MULTIPLIER", 1.2))
    atr_tp_multiplier: float = field(default_factory=lambda: _float("ATR_TP_MULTIPLIER", 3.0))
    min_volume_ratio: float = field(default_factory=lambda: _float("MIN_VOLUME_RATIO", 0.8))
    cooldown_minutes_after_loss: int = field(default_factory=lambda: _float("COOLDOWN_MINUTES_AFTER_LOSS", 30))
    max_slippage_pct: float = field(default_factory=lambda: _float("MAX_SLIPPAGE_PCT", 0.15))
    max_price_staleness_pct: float = field(default_factory=lambda: _float("MAX_PRICE_STALENESS_PCT", 1.0))
    min_trade_notional_usd: float = field(default_factory=lambda: _float("MIN_TRADE_NOTIONAL_USD", 10.0))

    # --- Safety switches ---
    trading_enabled: bool = field(default_factory=lambda: _bool("TRADING_ENABLED", True))
    dry_run: bool = field(default_factory=lambda: _bool("DRY_RUN", False))

    # --- API / infra ---
    api_auth_token: str = field(
        default_factory=lambda: os.getenv("ENGINE_TOKEN") or os.getenv("API_AUTH_TOKEN", "")
    )
    allowed_origins: list[str] = field(
        default_factory=lambda: _list(
            "ALLOWED_ORIGINS",
            [
                "https://nexus-7-weex-terminal.vercel.app",
                "http://localhost:3000",
                "http://localhost:3001",
                "http://localhost:5173",
                "http://localhost:5174",
                "http://localhost:8080",
                "http://localhost:4173",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173",
                "http://127.0.0.1:5174",
                "http://127.0.0.1:10000",
                "http://localhost:10000",
            ],
        )
    )
    database_path: str = field(default_factory=lambda: os.getenv("DATABASE_PATH", "./data/engine.db"))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    port: int = field(default_factory=lambda: _int("PORT", 10000))

    @property
    def ENGINE_TOKEN(self) -> str:
        return self.api_auth_token

    @property
    def ALLOWED_ORIGINS(self) -> list[str]:
        return self.allowed_origins

    @property
    def GEMINI_API_KEY(self) -> str:
        return self.gemini_api_key

    @property
    def AI_MIN_CONFIDENCE(self) -> int:
        return self.min_confidence_score

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

    def get_frozen_config_snapshot(self) -> dict:
        """Returns an immutable dictionary of the frozen strategy baseline parameters."""
        return {
            "ema_trend": 50,
            "rsi_long_range": (45, 68),
            "rsi_short_range": (32, 55),
            "min_volume_ratio": self.min_volume_ratio,
            "min_adx": self.min_adx,
            "atr_period": self.atr_period,
            "atr_sl_multiplier": self.atr_sl_multiplier,
            "t1_tp_multiplier": self.t1_tp_multiplier,
            "t2_tp_multiplier": self.t2_tp_multiplier,
            "position_split": "50% / 50%",
            "session_utc": f"{self.session_start_hour:02d}:00-{self.session_end_hour:02d}:00",
            "session_filter_enabled": self.enable_session_filter,
            "risk_per_trade_pct": self.risk_per_trade_pct,
            "max_daily_loss_pct": self.max_daily_loss_pct,
            "max_position_pct": self.max_position_pct,
            "max_open_positions": self.max_open_positions,
            "min_confidence_score": self.min_confidence_score,
        }


settings = Settings()

