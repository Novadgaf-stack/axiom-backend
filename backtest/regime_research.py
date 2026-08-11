"""
Regime Research & Feature Vector Extraction Module for NEXUS-7 Engine.

Extracts multidimensional market regime features for every trade executed during backtesting:
- 4H ADX, 4H EMA-50 Slope, 4H ATR, 4H Volatility Percentile
- 1H ADX, 1H EMA-21 Distance, 1H EMA-50 Distance, RSI, Volume Ratio
- Entry Session Hour, Trade Direction, Holding Time in Bars
- Gross Return %, Transaction Friction, Net PnL USD, R-Multiple, Outcome (WIN / LOSS)

Exports formatted dataset to CSV for Gemini 2.0 Flash AI analysis and quantitative regime discovery.
"""
import asyncio
import csv
import dataclasses
import math
import os
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from app.config import Settings
from app.indicators import _adx, _atr, _ema
from backtest.metrics import SimTrade
from backtest.mock_ai_analyst import MockAiAnalyst
from backtest.simulator import BacktestSimulator


def compute_regime_features(df_1h: pd.DataFrame) -> pd.DataFrame:
    """
    Computes 4H & 1H regime features aligned to 1H candles without lookahead bias.
    """
    df = df_1h.copy()
    dt_index = pd.to_datetime(df["ts"], unit="ms", utc=True)
    df_indexed = df.set_index(dt_index)

    # 1H Features
    ema_fast_1h = _ema(df["close"], 9)
    ema_slow_1h = _ema(df["close"], 21)
    ema_50_1h = _ema(df["close"], 50)
    adx_1h = _adx(df, 14)
    atr_1h = _atr(df, 14)
    vol_roll_1h = df["volume"].rolling(20).mean().replace(0, 1e-9)
    vol_ratio_1h = df["volume"] / vol_roll_1h

    df["1h_adx"] = adx_1h
    df["1h_dist_ema21_pct"] = (df["close"] - ema_slow_1h) / ema_slow_1h * 100.0
    df["1h_dist_ema50_pct"] = (df["close"] - ema_50_1h) / ema_50_1h * 100.0
    df["1h_volume_ratio"] = vol_ratio_1h

    # 4H Features resampled
    df_4h = df_indexed.resample("4h").agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
        "ts": "last",
    }).dropna()

    if len(df_4h) >= 55:
        ema_50_4h = _ema(df_4h["close"], 50)
        ema_200_4h = _ema(df_4h["close"], 200)
        adx_4h = _adx(df_4h, 14)
        atr_4h = _atr(df_4h, 14)

        # 4H EMA slope (% change over 5 4H bars = 20 hours)
        ema_50_slope_4h = (ema_50_4h - ema_50_4h.shift(5)) / ema_50_4h.shift(5) * 100.0

        # 4H Volatility Percentile (current ATR / 50-period rolling avg ATR)
        atr_4h_avg = atr_4h.rolling(50).mean().replace(0, 1e-9)
        vol_pct_4h = (atr_4h / atr_4h_avg) * 100.0

        df_4h["4h_adx"] = adx_4h
        df_4h["4h_ema50_slope_pct"] = ema_50_slope_4h
        df_4h["4h_volatility_pct"] = vol_pct_4h
        df_4h["4h_uptrend"] = (df_4h["close"] > ema_50_4h) & (ema_50_4h > ema_200_4h)

        # Reindex to 1H dataframe with shift by 1 4H bar to prevent lookahead
        df["4h_adx"] = adx_4h.shift(1).reindex(dt_index, method="ffill").fillna(0.0).values
        df["4h_ema50_slope_pct"] = ema_50_slope_4h.shift(1).reindex(dt_index, method="ffill").fillna(0.0).values
        df["4h_volatility_pct"] = vol_pct_4h.shift(1).reindex(dt_index, method="ffill").fillna(100.0).values
        df["4h_uptrend"] = df_4h["4h_uptrend"].shift(1).reindex(dt_index, method="ffill").fillna(False).values
    else:
        df["4h_adx"] = 0.0
        df["4h_ema50_slope_pct"] = 0.0
        df["4h_volatility_pct"] = 100.0
        df["4h_uptrend"] = True

    return df


def extract_regime_dataset(candles_15m: list, symbol: str, base_settings: Settings, out_csv_path: str = "./backtest_results/regime_trade_dataset.csv") -> pd.DataFrame:
    """
    Simulates trades and attaches rich multidimensional regime feature vectors to every trade.
    """
    df_15m = pd.DataFrame(candles_15m, columns=["ts", "open", "high", "low", "close", "volume"])
    dt_idx = pd.to_datetime(df_15m["ts"], unit="ms", utc=True)
    df_1h = df_15m.set_index(dt_idx).resample("1h").agg({
        "ts": "first", "open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"
    }).dropna().reset_index(drop=True)

    df_featured = compute_regime_features(df_1h)
    candles_1h = df_1h[["ts", "open", "high", "low", "close", "volume"]].values.tolist()

    cand_settings = dataclasses.replace(
        base_settings,
        timeframe="1h",
        min_volume_ratio=0.7,
        min_confidence_score=90,
    )
    analyst = MockAiAnalyst(mode="ai_mirror", seed=42)

    sim = BacktestSimulator(
        candles=candles_1h,
        symbol=symbol,
        analyst=analyst,
        settings_obj=cand_settings,
        initial_equity=10000.0,
        fee_pct=0.02,
        slippage_pct=0.00,
        execution_mode="maker",
        enable_4h_trend_filter=True,
        enable_4h_chop_filter=True,
    )
    trades = asyncio.run(sim.run())

    trade_rows = []
    for i, t in enumerate(trades):
        idx = t.entry_index
        if idx >= len(df_featured):
            continue

        feat_row = df_featured.iloc[idx]
        entry_dt = datetime.fromtimestamp(t.entry_time_ms / 1000, tz=timezone.utc)

        holding_bars = (t.exit_index - t.entry_index) if t.exit_index else 0
        outcome = "WIN" if t.pnl_usd > 0 else "LOSS"

        trade_rows.append({
            "trade_id": i + 1,
            "entry_time_utc": entry_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "symbol": t.symbol,
            "direction": "LONG",
            "entry_price": round(t.entry_price, 2),
            "exit_price": round(t.exit_price, 2) if t.exit_price else 0.0,
            "stop_loss": round(t.stop_loss, 2),
            "take_profit": round(t.take_profit, 2),
            "outcome": outcome,
            "net_pnl_usd": round(t.pnl_usd, 2),
            "r_multiple": round(t.r_multiple, 2),
            "fees_usd": round(t.fees_usd, 2),
            "holding_bars": holding_bars,
            "4h_adx": round(float(feat_row.get("4h_adx", 0.0)), 2),
            "4h_ema50_slope_pct": round(float(feat_row.get("4h_ema50_slope_pct", 0.0)), 3),
            "4h_volatility_pct": round(float(feat_row.get("4h_volatility_pct", 100.0)), 2),
            "4h_uptrend": bool(feat_row.get("4h_uptrend", True)),
            "1h_adx": round(float(feat_row.get("1h_adx", 0.0)), 2),
            "1h_dist_ema21_pct": round(float(feat_row.get("1h_dist_ema21_pct", 0.0)), 3),
            "1h_dist_ema50_pct": round(float(feat_row.get("1h_dist_ema50_pct", 0.0)), 3),
            "1h_volume_ratio": round(float(feat_row.get("1h_volume_ratio", 1.0)), 2),
            "session_hour_utc": entry_dt.hour,
            "ai_confidence": t.ai_confidence or 0,
        })

    dataset_df = pd.DataFrame(trade_rows)
    os.makedirs(os.path.dirname(out_csv_path), exist_ok=True)
    dataset_df.to_csv(out_csv_path, index=False)
    print(f"Exported {len(dataset_df)} trade feature records to: {out_csv_path}")
    return dataset_df


def run_regime_bucket_analysis(df_dataset: pd.DataFrame) -> str:
    """
    NEXUS-7 v3.1 Regime Hypothesis Bucket Test.
    Evaluates trade stability across predefined, non-curve-fitted feature buckets:
    - 4H ADX: <30, 30-40, >40
    - 1H ADX: <35, 35-40, >40
    - 4H Volatility %: <90%, 90-110%, >110%
    - Combined Hypothesis: 4H ADX > 1H ADX (Strong 4H Trend + Cooling 1H Pullback)
    """
    if df_dataset.empty:
        return "Dataset is empty — cannot compute regime bucket analysis."

    def compute_bucket_stats(subset: pd.DataFrame, bucket_label: str) -> dict:
        n = len(subset)
        if n == 0:
            return {
                "bucket": bucket_label, "trades": 0, "win_rate": "0.00%", "pf": "0.00",
                "gross_pnl": "$0.00", "friction": "$0.00", "net_pnl": "$0.00",
                "expectancy": "$0.00", "avg_r": "0.00R",
            }
        wins = subset[subset["outcome"] == "WIN"]
        losses = subset[subset["outcome"] == "LOSS"]

        win_pnl = wins["net_pnl_usd"].sum() if not wins.empty else 0.0
        loss_pnl = abs(losses["net_pnl_usd"].sum()) if not losses.empty else 0.0

        pf = (win_pnl / loss_pnl) if loss_pnl > 0 else (99.0 if win_pnl > 0 else 0.0)
        net_pnl = subset["net_pnl_usd"].sum()
        friction = subset["fees_usd"].sum()
        gross_pnl = net_pnl + friction
        win_rate = (len(wins) / n * 100.0)
        expectancy = net_pnl / n
        avg_r = subset["r_multiple"].mean()

        return {
            "bucket": bucket_label,
            "trades": n,
            "win_rate": f"{win_rate:.2f}%",
            "pf": f"{pf:.2f}",
            "gross_pnl": f"${gross_pnl:+.2f}",
            "friction": f"${friction:.2f}",
            "net_pnl": f"${net_pnl:+.2f}",
            "expectancy": f"${expectancy:.2f}",
            "avg_r": f"{avg_r:+.2f}R",
        }

    rows = []

    # 1. 4H ADX Buckets
    rows.append(compute_bucket_stats(df_dataset[df_dataset["4h_adx"] < 30], "4H ADX < 30 (Weak/Ranging)"))
    rows.append(compute_bucket_stats(df_dataset[(df_dataset["4h_adx"] >= 30) & (df_dataset["4h_adx"] <= 40)], "4H ADX 30-40 (Moderate Trend)"))
    rows.append(compute_bucket_stats(df_dataset[df_dataset["4h_adx"] > 40], "4H ADX > 40 (Strong Trend)"))

    # 2. 1H ADX Buckets
    rows.append(compute_bucket_stats(df_dataset[df_dataset["1h_adx"] < 35], "1H ADX < 35 (Cooling Pullback)"))
    rows.append(compute_bucket_stats(df_dataset[(df_dataset["1h_adx"] >= 35) & (df_dataset["1h_adx"] <= 40)], "1H ADX 35-40 (Moderate 1H)"))
    rows.append(compute_bucket_stats(df_dataset[df_dataset["1h_adx"] > 40], "1H ADX > 40 (Local Momentum Spike)"))

    # 3. 4H Volatility Percentile Buckets
    rows.append(compute_bucket_stats(df_dataset[df_dataset["4h_volatility_pct"] < 90.0], "4H Volatility < 90% (Low/Compressing)"))
    rows.append(compute_bucket_stats(df_dataset[(df_dataset["4h_volatility_pct"] >= 90.0) & (df_dataset["4h_volatility_pct"] <= 110.0)], "4H Volatility 90-110% (Normal)"))
    rows.append(compute_bucket_stats(df_dataset[df_dataset["4h_volatility_pct"] > 110.0], "4H Volatility > 110% (High Expansion)"))

    # 4. Combined Structural Regime Hypothesis
    combined_subset = df_dataset[(df_dataset["4h_adx"] > df_dataset["1h_adx"]) & (df_dataset["4h_volatility_pct"] >= 90.0)]
    rows.append(compute_bucket_stats(combined_subset, "Combined Hypothesis: 4H ADX > 1H ADX & Normal Vol"))

    report_md = []
    report_md.append("# NEXUS-7 v3.1 — REGIME BUCKET HYPOTHESIS REPORT\n")
    report_md.append(f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  ")
    report_md.append(f"**Total Trade Sample Size:** {len(df_dataset):,} trades\n")
    report_md.append("---\n")
    report_md.append("## Predefined Feature Bucket Performance Matrix\n")
    report_md.append("| Feature Bucket | Trades ($N$) | Win Rate % | Profit Factor | Gross PnL ($) | Friction ($) | Net PnL ($) | Expectancy ($/tr) | Avg R |")
    report_md.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")

    for r in rows:
        report_md.append(
            f"| **{r['bucket']}** | {r['trades']} | {r['win_rate']} | {r['pf']} | {r['gross_pnl']} | {r['friction']} | {r['net_pnl']} | {r['expectancy']} | {r['avg_r']} |"
        )

    report_md.append("\n---\n")
    report_md.append("## Structural Regime Findings & Discipline Reminders\n")
    report_md.append("1. **4H ADX vs 1H ADX Structural Signature**: Pullbacks occurring when `4H ADX > 1H ADX` represent macro trend continuation with temporary lower-timeframe cooling.\n")
    report_md.append("2. **Zero Curve-Fitting Rule**: Do NOT tune exact numeric thresholds based on sample maximums; test stable structural relationships across unseen temporal holdouts.\n")

    return "\n".join(report_md)


def evaluate_regime_hypothesis_oos(candles_15m: list, symbol: str, base_settings: Settings) -> str:
    """
    Evaluates the Combined Regime Hypothesis (4H ADX > 1H ADX & 4H Volatility >= 90%)
    across strict 70/30 Temporal In-Sample (Development) vs Out-of-Sample (OOS) Holdout.
    Proves whether the structural market regime signature survives on unseen data.
    """
    df_15m = pd.DataFrame(candles_15m, columns=["ts", "open", "high", "low", "close", "volume"])
    dt_idx = pd.to_datetime(df_15m["ts"], unit="ms", utc=True)
    df_1h = df_15m.set_index(dt_idx).resample("1h").agg({
        "ts": "first", "open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"
    }).dropna().reset_index(drop=True)

    df_featured = compute_regime_features(df_1h)
    candles_1h = df_1h[["ts", "open", "high", "low", "close", "volume"]].values.tolist()

    split_idx = int(len(candles_1h) * 0.70)
    is_candles = candles_1h[:split_idx]
    oos_candles = candles_1h[split_idx:]

    cand_settings = dataclasses.replace(
        base_settings,
        timeframe="1h",
        min_volume_ratio=0.7,
        min_confidence_score=90,
    )
    analyst = MockAiAnalyst(mode="ai_mirror", seed=42)

    def run_split(c_list: list, enable_regime_filter: bool = False):
        sim = BacktestSimulator(
            candles=c_list,
            symbol=symbol,
            analyst=analyst,
            settings_obj=cand_settings,
            initial_equity=10000.0,
            fee_pct=0.02,
            slippage_pct=0.00,
            execution_mode="maker",
            enable_4h_trend_filter=True,
            enable_4h_chop_filter=True,
        )
        trades = asyncio.run(sim.run())
        if not enable_regime_filter:
            return trades

        # Filter trades by structural regime hypothesis: (4H ADX > 1H ADX) & (4H Volatility >= 90%)
        df_sub_featured = compute_regime_features(
            pd.DataFrame(c_list, columns=["ts", "open", "high", "low", "close", "volume"])
        )
        filtered_trades = []
        for t in trades:
            idx = t.entry_index
            if idx < len(df_sub_featured):
                row = df_sub_featured.iloc[idx]
                if row.get("4h_adx", 0.0) > row.get("1h_adx", 0.0) and row.get("4h_volatility_pct", 0.0) >= 90.0:
                    filtered_trades.append(t)
        return filtered_trades

    def metrics(t_list: list) -> dict:
        n = len(t_list)
        if n == 0:
            return {"trades": 0, "win_rate": "0.00%", "pf": "0.00", "net_pnl": "$0.00", "expectancy": "$0.00"}
        wins = [t for t in t_list if t.pnl_usd > 0]
        losses = [t for t in t_list if t.pnl_usd <= 0]

        win_pnl = sum(t.pnl_usd for t in wins)
        loss_pnl = abs(sum(t.pnl_usd for t in losses))

        pf = (win_pnl / loss_pnl) if loss_pnl > 0 else (99.0 if win_pnl > 0 else 0.0)
        net_pnl = sum(t.pnl_usd for t in t_list)
        win_rate = (len(wins) / n * 100.0)
        expectancy = net_pnl / n

        return {
            "trades": n,
            "win_rate": f"{win_rate:.2f}%",
            "pf": f"{pf:.2f}",
            "net_pnl": f"${net_pnl:+.2f}",
            "expectancy": f"${expectancy:.2f}",
        }

    # Baseline Benchmark v1
    is_base = metrics(run_split(is_candles, enable_regime_filter=False))
    oos_base = metrics(run_split(oos_candles, enable_regime_filter=False))

    # Regime-Conditioned Strategy
    is_regime = metrics(run_split(is_candles, enable_regime_filter=True))
    oos_regime = metrics(run_split(oos_candles, enable_regime_filter=True))

    report_md = []
    report_md.append("# NEXUS-7 v3.1 — FROZEN OUT-OF-SAMPLE REGIME VALIDATION REPORT\n")
    report_md.append(f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  ")
    report_md.append(f"**Dataset Split:** {len(is_candles):,} In-Sample Bars (70%) | {len(oos_candles):,} Out-of-Sample Bars (30%)\n")
    report_md.append("---\n")
    report_md.append("## Structural Regime Hypothesis OOS Evaluation Matrix\n")
    report_md.append("| Candidate Configuration | Temporal Dataset | Trades ($N$) | Win Rate % | Profit Factor | Net PnL ($) | Expectancy ($/tr) |")
    report_md.append("| :--- | :--- | :---: | :---: | :---: | :---: | :---: |")
    report_md.append(f"| **Benchmark v1 (Unfiltered)** | In-Sample (Dev) | {is_base['trades']} | {is_base['win_rate']} | **{is_base['pf']}** | {is_base['net_pnl']} | {is_base['expectancy']} |")
    report_md.append(f"| **Benchmark v1 (Unfiltered)** | Out-of-Sample (Holdout) | {oos_base['trades']} | {oos_base['win_rate']} | **{oos_base['pf']}** | {oos_base['net_pnl']} | {oos_base['expectancy']} |")
    report_md.append(f"| **Regime v3.1 (4H ADX > 1H ADX)** | In-Sample (Dev) | {is_regime['trades']} | {is_regime['win_rate']} | **{is_regime['pf']}** | {is_regime['net_pnl']} | {is_regime['expectancy']} |")
    report_md.append(f"| **Regime v3.1 (4H ADX > 1H ADX)** | Out-of-Sample (Holdout) | {oos_regime['trades']} | {oos_regime['win_rate']} | **{oos_regime['pf']}** | {oos_regime['net_pnl']} | {oos_regime['expectancy']} |")

    report_md.append("\n---\n")
    report_md.append("## Verdict & Empirical Interpretation\n")
    if float(oos_regime["pf"]) > float(oos_base["pf"]):
        report_md.append("**[SUCCESS] REGIME GENERALIZATION**: The `4H ADX > 1H ADX` structural regime hypothesis improved Out-of-Sample Profit Factor relative to Benchmark v1.\n")
    else:
        report_md.append("**[DEGRADED] REGIME HYPOTHESIS**: The `4H ADX > 1H ADX` relationship did not improve OOS performance, indicating sample-specific noise.\n")

    return "\n".join(report_md)


