from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.utils import DATA_DIR, ensure_dirs, load_settings, write_csv_atomic, write_json  # noqa: E402

rng = np.random.default_rng(42)
settings = load_settings()
ensure_dirs()

months = pd.period_range("2015-01", datetime.now().strftime("%Y-%m"), freq="M")
n = len(months)
m2 = 120 + np.cumsum(rng.normal(1.2, 0.35, n))
m1 = 45 + np.cumsum(rng.normal(0.35, 0.25, n))
m1_yoy = 7 + 4 * np.sin(np.linspace(0, 10, n)) + rng.normal(0, 0.6, n)
m2_yoy = 8 + 2 * np.sin(np.linspace(1, 8, n)) + rng.normal(0, 0.35, n)
sf = np.clip(rng.normal(2.5, 0.9, n), 0.3, None)
pmi = 50 + 1.7 * np.sin(np.linspace(0, 15, n)) + rng.normal(0, 0.45, n)
cpi = 1.8 + 1.2 * np.sin(np.linspace(0, 8, n)) + rng.normal(0, 0.25, n)
macro = pd.DataFrame({
    "month": months.strftime("%Y%m"),
    "m1_trillion": m1,
    "m2_trillion": m2,
    "m1_yoy_pct": m1_yoy,
    "m2_yoy_pct": m2_yoy,
    "m1_m2_gap_pp": m1_yoy - m2_yoy,
    "m1_m2_mechanical_sum_trillion": m1 + m2,
    "sf_increment_trillion": sf,
    "sf_increment_yoy_pct": pd.Series(sf).pct_change(12) * 100,
    "sf_12m_trillion": pd.Series(sf).rolling(12).sum(),
    "sf_12m_yoy_pct": pd.Series(sf).rolling(12).sum().pct_change(12) * 100,
    "sf_stock_trillion": 180 + np.cumsum(sf),
    "sf_stock_yoy_pct": 9.5 + 1.6 * np.sin(np.linspace(0, 9, n)) + rng.normal(0, 0.25, n),
    "pmi_manufacturing": pmi,
    "pmi_non_manufacturing": pmi + rng.normal(1.2, 0.5, n),
    "cpi_yoy_pct": cpi,
    "cpi_mom_pct": rng.normal(0.15, 0.25, n),
    "updated_at": datetime.now().isoformat(timespec="seconds"),
})
write_csv_atomic(macro, DATA_DIR / "macro.csv")

trade_dates = pd.bdate_range("2023-01-02", datetime.now())
market_rows = []
all_assets = [(x["symbol"], x.get("short_name", x["name"]), "CN_INDEX") for x in settings["china_indices"]]
all_assets += [(x["ticker"], x["name"], "US_EQUITY") for x in settings["us_leaders"]]
for idx, (symbol, name, market) in enumerate(all_assets):
    returns = rng.normal(0.00045 + idx * 0.00003, 0.014 + idx * 0.0004, len(trade_dates))
    close = (1000 if market == "CN_INDEX" else 100) * np.exp(np.cumsum(returns))
    frame = pd.DataFrame({
        "trade_date": trade_dates.strftime("%Y%m%d"),
        "symbol": symbol,
        "name": name,
        "market": market,
        "close": close,
        "pct_change": pd.Series(close).pct_change() * 100,
        "volume": rng.integers(1_000_000, 20_000_000, len(trade_dates)),
        "amount": np.nan,
        "source": "演示数据",
    })
    market_rows.append(frame)
write_csv_atomic(pd.concat(market_rows, ignore_index=True), DATA_DIR / "market.csv")

valuation_dates = pd.bdate_range("2015-01-02", datetime.now())
valuation_rows = []
for idx, item in enumerate(settings["valuation_indices"]):
    base = 12 + idx * 3
    pe = np.clip(base + 4 * np.sin(np.linspace(0, 12, len(valuation_dates))) + rng.normal(0, 1.2, len(valuation_dates)), 4, None)
    pb = np.clip(1.2 + idx * 0.25 + 0.45 * np.sin(np.linspace(0, 10, len(valuation_dates))) + rng.normal(0, 0.12, len(valuation_dates)), 0.4, None)
    valuation_rows.append(pd.DataFrame({
        "trade_date": valuation_dates.strftime("%Y%m%d"),
        "index_code": item["symbol"],
        "index_name": item["name"],
        "pe_ttm": pe,
        "pb": pb,
        "source": "演示数据",
    }))
write_csv_atomic(pd.concat(valuation_rows, ignore_index=True), DATA_DIR / "valuation.csv")

crowding_dates = pd.bdate_range("2024-01-02", datetime.now())
crowding = pd.DataFrame({
    "trade_date": crowding_dates.strftime("%Y%m%d"),
    "top_fraction": 0.05,
    "stock_count": 5100,
    "top_count": 255,
    "top_amount_trillion": 0.48 + rng.normal(0, 0.08, len(crowding_dates)),
    "total_amount_trillion": 1.15 + rng.normal(0, 0.18, len(crowding_dates)),
    "source": "演示数据",
})
crowding["crowding_pct"] = crowding["top_amount_trillion"] / crowding["total_amount_trillion"] * 100
write_csv_atomic(crowding, DATA_DIR / "crowding.csv")

status = {
    "app_version": settings["app"]["version"],
    "updated_at": datetime.now().isoformat(timespec="seconds"),
    "overall_status": "demo",
    "datasets": {
        "macro": {"status": "demo", "rows": len(macro), "latest_date": macro["month"].max()},
        "market": {"status": "demo", "rows": sum(len(x) for x in market_rows), "latest_date": trade_dates.max().strftime("%Y%m%d")},
        "valuation": {"status": "demo", "rows": sum(len(x) for x in valuation_rows), "latest_date": valuation_dates.max().strftime("%Y%m%d")},
        "crowding": {"status": "demo", "rows": len(crowding), "latest_date": crowding["trade_date"].max()},
    },
}
write_json(DATA_DIR / "status.json", status)
print(json.dumps(status, ensure_ascii=False, indent=2))
