"""Add nitrate, phosphate and silicate to the core HAB dataset.

Pulls no3, po4 and si from the Copernicus global biogeochemistry reanalysis
(cmems_mod_glo_bgc_my_0.25deg_P1D-m, daily, 1993 to Aug 2026, surface level)
for each record in hab_model_dataset_initial.csv and saves the result to
hab_model_dataset_bgc.csv.

Features per nutrient, all ending the day before the event:
    <var>_mean7, <var>_mean30   mean over the last 7 / 30 days
    <var>_chg14/30/60          change over the last 14 / 30 / 60 days
Features are left empty when the needed days fall outside the dataset.

Values are averaged over a box around each site: +/-0.5 deg, widened if the box
is all land (temperature/salinity use +/-1.0 deg).
"""

import argparse
import json
import logging
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
import copernicusmarine as cm

logging.getLogger("copernicusmarine").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data/processed/hab_model_dataset_initial.csv"
OUTPUT = ROOT / "data/processed/hab_model_dataset_bgc.csv"
# Per-record download cache. 
CACHE = ROOT / "data/interim/bgc_cache_v2"
ERRORS = ROOT / "data/interim/bgc_errors.csv"

DATASET_ID = "cmems_mod_glo_bgc_my_0.25deg_P1D-m"
NUTRIENTS = ["no3", "po4", "si"]
DATA_START, DATA_END = pd.Timestamp("1993-01-01"), pd.Timestamp("2026-08-31")
BUFFERS = [0.5, 1.0, 1.5]  # degrees; the 0.25 deg grid is coarse near coasts
WINDOW_DAYS = 61           # covers the 60-day change plus the reference day
FEATURE_SUFFIXES = ("_mean7", "_mean30", "_chg14", "_chg30", "_chg60")


def feature_names():
    return [f"{v}{s}" for v in NUTRIENTS for s in FEATURE_SUFFIXES]


def box_mean(lat, lon, start, end):
    """Daily spatial mean over the smallest box around (lat, lon) with ocean cells."""
    for buf in BUFFERS:
        ds = cm.open_dataset(
            dataset_id=DATASET_ID,
            variables=NUTRIENTS,
            minimum_latitude=lat - buf,
            maximum_latitude=lat + buf,
            minimum_longitude=lon - buf,
            maximum_longitude=lon + buf,
            start_datetime=start,
            end_datetime=end,
            minimum_depth=0.5,
            maximum_depth=0.51,
        )
        df = ds.mean(["latitude", "longitude"], skipna=True).load().to_dataframe()
        df = df.reset_index().set_index("time")[NUTRIENTS]
        if df["no3"].notna().any():
            return df, buf
    return df, np.nan


def summarise(daily, event_date):
    """Lagged features ending the day before the event."""
    ref = event_date - pd.Timedelta(days=1)
    daily = daily[daily.index <= ref]  # never use the event day or later
    f = {}
    for v in NUTRIENTS:
        s = daily[v] if v in daily else pd.Series(dtype=float)
        has_ref = ref in s.index and pd.notna(s.get(ref))
        last7 = s[s.index > ref - pd.Timedelta(days=7)]
        last30 = s[s.index > ref - pd.Timedelta(days=30)]
        f[f"{v}_mean7"] = last7.mean() if has_ref and last7.notna().sum() >= 5 else np.nan
        f[f"{v}_mean30"] = last30.mean() if has_ref and last30.notna().sum() >= 21 else np.nan
        for lag in (14, 30, 60):
            back = ref - pd.Timedelta(days=lag)
            ok = has_ref and back in s.index and pd.notna(s.get(back))
            f[f"{v}_chg{lag}"] = s[ref] - s[back] if ok else np.nan
    return f


def process(row):
    out = CACHE / f"{row.record_id}.json"
    keep = set(feature_names()) | {"record_id", "bgc_buffer_degrees", "bgc_days_found"}
    if out.exists():
        cached = json.loads(out.read_text())
        if all(k in cached for k in feature_names()):
            return {k: v for k, v in cached.items() if k in keep}

    date = pd.Timestamp(row.observation_date)
    start = max(date - pd.Timedelta(days=WINDOW_DAYS), DATA_START)
    end = min(date - pd.Timedelta(days=1), DATA_END)
    if end < start:
        daily, buf = pd.DataFrame(columns=NUTRIENTS), np.nan
    else:
        daily, buf = box_mean(row.latitude, row.longitude,
                              start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
    feats = summarise(daily, date)
    feats = {k: (None if pd.isna(v) else float(v)) for k, v in feats.items()}
    feats.update(record_id=row.record_id,
                 bgc_buffer_degrees=None if pd.isna(buf) else float(buf),
                 bgc_days_found=int(len(daily)))
    out.write_text(json.dumps(feats))
    return feats


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, help="only process the first N records (test)")
    p.add_argument("--workers", type=int, default=8)
    args = p.parse_args()

    CACHE.mkdir(parents=True, exist_ok=True)
    core = pd.read_csv(INPUT)
    todo = core.head(args.limit) if args.limit else core

    rows, errors = [], []
    with ThreadPoolExecutor(args.workers) as pool:
        futures = {pool.submit(process, r): r.record_id for r in todo.itertuples()}
        for i, fut in enumerate(as_completed(futures), 1):
            try:
                rows.append(fut.result())
            except Exception as exc:  # keep going; failures are listed at the end
                errors.append({"record_id": futures[fut], "error": repr(exc)[:300]})
            if i % 50 == 0 or i == len(futures):
                print(f"{i}/{len(futures)} done, {len(errors)} errors", flush=True)

    if errors:
        pd.DataFrame(errors).to_csv(ERRORS, index=False)
        print(f"{len(errors)} errors written to {ERRORS}")

    if not rows:
        raise SystemExit(f"No records were processed; see {ERRORS} for the errors.")
    feats = pd.DataFrame(rows)
    if args.limit:
        print(feats.set_index("record_id").T)
        return

    merged = core.merge(feats, on="record_id", how="left")
    merged.to_csv(OUTPUT, index=False)
    cols = feature_names()
    print(f"wrote {OUTPUT} ({len(merged)} rows, {len(cols)} nutrient features)")
    print("records with any missing nutrient feature:",
          int(merged[cols].isna().any(axis=1).sum()))
    print(merged[[f"{v}_mean30" for v in NUTRIENTS]].describe().T.round(3))


if __name__ == "__main__":
    main()
