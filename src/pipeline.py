from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from src.providers import ChinaMarketProvider, PublicMacroProvider, USMarketProvider
from src.utils import DATA_DIR, ensure_dirs, load_settings, read_csv_safe, write_csv_atomic, write_json

MACRO_PATH = DATA_DIR / "macro.csv"
MARKET_PATH = DATA_DIR / "market.csv"
VALUATION_PATH = DATA_DIR / "valuation.csv"
CROWDING_PATH = DATA_DIR / "crowding.csv"
STATUS_PATH = DATA_DIR / "status.json"


def _now_iso() -> str:
    return datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds")


def _merge_history(old: pd.DataFrame, new: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    if old.empty:
        merged = new.copy()
    elif new.empty:
        merged = old.copy()
    else:
        merged = pd.concat([old, new], ignore_index=True)
        merged = merged.drop_duplicates(keys, keep="last")
    return merged.sort_values(keys).reset_index(drop=True)


def _latest_value(df: pd.DataFrame, date_col: str) -> str | None:
    if df.empty or date_col not in df.columns:
        return None
    values = df[date_col].dropna().astype(str)
    return values.max() if not values.empty else None


def _run(name: str, fn: Callable[[], tuple[int, dict[str, Any]]]) -> dict[str, Any]:
    started = _now_iso()
    try:
        rows, metadata = fn()
        return {
            "status": "success" if rows > 0 else "partial",
            "rows": rows,
            "started_at": started,
            "finished_at": _now_iso(),
            **metadata,
        }
    except Exception as exc:
        return {
            "status": "failed",
            "rows": 0,
            "started_at": started,
            "finished_at": _now_iso(),
            "error": repr(exc),
        }


def update_macro(settings: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    provider = PublicMacroProvider()
    new, details = provider.fetch(settings["macro_start_month"])
    old = read_csv_safe(MACRO_PATH)
    merged = _merge_history(old, new, ["month"])
    write_csv_atomic(merged, MACRO_PATH)
    return len(new), {
        "latest_date": _latest_value(merged, "month"),
        "total_cached_rows": len(merged),
        "source_details": details,
    }


def update_market(settings: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    cn_provider = ChinaMarketProvider()
    frames: list[pd.DataFrame] = []
    per_symbol: dict[str, Any] = {}
    end_date = datetime.now().strftime("%Y%m%d")

    for item in settings["china_indices"]:
        try:
            frame = cn_provider.fetch_index(item, settings["market_start_date"], end_date)
            frames.append(frame)
            per_symbol[item["symbol"]] = {"status": "success", "rows": len(frame), "source": frame["source"].iloc[-1] if not frame.empty else None}
        except Exception as exc:
            per_symbol[item["symbol"]] = {"status": "failed", "error": repr(exc)}

    us_items = settings["us_leaders"]
    tickers = [x["ticker"] for x in us_items]
    names = {x["ticker"]: x["name"] for x in us_items}
    try:
        us = USMarketProvider().fetch(tickers, names, settings["market_start_date"])
        frames.append(us)
        for ticker in tickers:
            subset = us[us["symbol"] == ticker]
            per_symbol[ticker] = {"status": "success" if not subset.empty else "failed", "rows": len(subset), "source": subset["source"].iloc[-1] if not subset.empty else None}
    except Exception as exc:
        for ticker in tickers:
            per_symbol[ticker] = {"status": "failed", "error": repr(exc)}

    if not frames:
        raise RuntimeError("所有中美行情源均失败")
    new = pd.concat(frames, ignore_index=True)
    old = read_csv_safe(MARKET_PATH)
    merged = _merge_history(old, new, ["trade_date", "symbol"])
    write_csv_atomic(merged, MARKET_PATH)
    return len(new), {
        "latest_date": _latest_value(merged, "trade_date"),
        "total_cached_rows": len(merged),
        "symbols": per_symbol,
    }


def update_valuation(settings: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    provider = ChinaMarketProvider()
    frames: list[pd.DataFrame] = []
    per_index: dict[str, Any] = {}
    end_date = datetime.now().strftime("%Y%m%d")
    for item in settings["valuation_indices"]:
        try:
            frame = provider.fetch_valuation(item, settings["valuation_start_date"], end_date)
            frames.append(frame)
            per_index[item["symbol"]] = {"status": "success", "rows": len(frame), "source": frame["source"].iloc[-1] if not frame.empty else None}
        except Exception as exc:
            per_index[item["symbol"]] = {"status": "failed", "error": repr(exc)}
    if not frames:
        raise RuntimeError("所有估值源均失败")
    new = pd.concat(frames, ignore_index=True)
    old = read_csv_safe(VALUATION_PATH)
    merged = _merge_history(old, new, ["trade_date", "index_code"])
    write_csv_atomic(merged, VALUATION_PATH)
    return len(new), {
        "latest_date": _latest_value(merged, "trade_date"),
        "total_cached_rows": len(merged),
        "indices": per_index,
    }


def update_crowding(settings: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    now = datetime.now(ZoneInfo(settings.get("timezone", "Asia/Shanghai")))
    if now.weekday() >= 5 or (now.hour, now.minute) < (15, 20):
        old = read_csv_safe(CROWDING_PATH)
        return 0, {
            "latest_date": _latest_value(old, "trade_date"),
            "total_cached_rows": len(old),
            "skipped": True,
            "note": "交易拥挤度仅在北京时间交易日15:20后追加，避免把盘中成交额当作收盘数据。",
        }
    provider = ChinaMarketProvider()
    row = provider.fetch_crowding(float(settings["crowding"]["top_fraction"]))
    new = pd.DataFrame([row])
    old = read_csv_safe(CROWDING_PATH)
    merged = _merge_history(old, new, ["trade_date"])
    write_csv_atomic(merged, CROWDING_PATH)
    return 1, {
        "latest_date": row["trade_date"],
        "total_cached_rows": len(merged),
        "source": row.get("source"),
    }


def update_all() -> dict[str, Any]:
    ensure_dirs()
    settings = load_settings()
    status = {
        "app_version": settings["app"]["version"],
        "updated_at": _now_iso(),
        "datasets": {},
    }
    status["datasets"]["macro"] = _run("macro", lambda: update_macro(settings))
    status["datasets"]["market"] = _run("market", lambda: update_market(settings))
    status["datasets"]["valuation"] = _run("valuation", lambda: update_valuation(settings))
    status["datasets"]["crowding"] = _run("crowding", lambda: update_crowding(settings))

    successful = sum(1 for x in status["datasets"].values() if x["status"] in {"success", "partial"} and x.get("rows", 0) > 0)

    cache_map = {
        "macro": (MACRO_PATH, "month"),
        "market": (MARKET_PATH, "trade_date"),
        "valuation": (VALUATION_PATH, "trade_date"),
        "crowding": (CROWDING_PATH, "trade_date"),
    }
    cache_available = False
    for dataset, (path, date_col) in cache_map.items():
        cached = read_csv_safe(path)
        if not cached.empty:
            cache_available = True
            info = status["datasets"].setdefault(dataset, {})
            info.setdefault("cached_rows", len(cached))
            info.setdefault("latest_date", _latest_value(cached, date_col))
            if info.get("status") == "failed":
                info["serving_cached_data"] = True

    if successful == len(status["datasets"]):
        status["overall_status"] = "success"
    elif successful > 0:
        status["overall_status"] = "partial"
    elif cache_available:
        status["overall_status"] = "stale"
    else:
        status["overall_status"] = "failed"

    write_json(STATUS_PATH, status)
    if successful == 0 and not cache_available:
        raise RuntimeError(f"所有公开数据更新均失败且没有历史缓存: {status['datasets']}")
    return status


if __name__ == "__main__":
    print(update_all())
