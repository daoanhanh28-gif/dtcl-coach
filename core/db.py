# ĐTCL Coach v1.1 (2026-10-06) — lưu nhật ký ván đấu vào Google Sheets (miễn phí)
"""
Database = 1 file Google Sheets, truy cập qua Google Apps Script Web App
(file apps_script/Code.gs). Không cần service account, không tốn server.

Nếu chưa cấu hình SHEETS_WEBAPP_URL → tự lưu CSV cục bộ (chỉ để chạy thử;
trên Streamlit Cloud file cục bộ sẽ mất khi app khởi động lại).
"""
from __future__ import annotations

import csv
from datetime import datetime, timezone, timedelta

import pandas as pd
import requests

from core import config

VN_TZ = timezone(timedelta(hours=7))
SHEETS = {
    "nhat_ky": "NhatKy",          # nhật ký ván đấu
    "luyen_tap": "LuyenTap",      # điểm các lượt luyện tập
}
CELL_LIMIT = 45000  # Google Sheets giới hạn 50.000 ký tự / ô


def now_str() -> str:
    return datetime.now(VN_TZ).strftime("%Y-%m-%d %H:%M:%S")


def _url():
    return config.get("SHEETS_WEBAPP_URL")


def backend() -> str:
    return "Google Sheets" if _url() else "CSV cục bộ (chạy thử)"


def log(kind: str, row: dict) -> bool:
    sheet = SHEETS[kind]
    row = {"thoi_gian": now_str(), "phien_ban_app": config.VERSION_LABEL, **row}
    row = {k: (str(v)[:CELL_LIMIT] if isinstance(v, str) else v) for k, v in row.items()}
    url = _url()
    if url:
        try:
            r = requests.post(url, timeout=30, json={
                "token": config.get("SHEETS_TOKEN", ""), "action": "append",
                "sheet": sheet, "row": row})
            ok = r.status_code == 200 and '"ok":true' in r.text.replace(" ", "")
            if ok:
                read.clear()
            return ok
        except requests.RequestException:
            return False
    config.LOCAL_LOG_DIR.mkdir(parents=True, exist_ok=True)
    path = config.LOCAL_LOG_DIR / f"{sheet}.csv"
    existing = pd.read_csv(path).columns.tolist() if path.exists() else []
    cols = existing + [k for k in row if k not in existing]
    if existing and cols != existing:  # thêm cột mới → ghi lại cả file
        df = pd.read_csv(path)
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)[cols]
        df.to_csv(path, index=False)
    else:
        with open(path, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            if not existing:
                w.writeheader()
            w.writerow(row)
    read.clear()
    return True


def _cache(fn):
    try:
        import streamlit as st
        return st.cache_data(ttl=60, show_spinner=False)(fn)
    except Exception:  # chạy test ngoài streamlit
        fn.clear = lambda: None
        return fn


@_cache
def read(kind: str) -> pd.DataFrame:
    sheet = SHEETS[kind]
    url = _url()
    if url:
        try:
            r = requests.get(url, timeout=30, params={
                "token": config.get("SHEETS_TOKEN", ""), "action": "read", "sheet": sheet})
            data = r.json()
            return pd.DataFrame(data.get("rows", []))
        except (requests.RequestException, ValueError):
            return pd.DataFrame()
    path = config.LOCAL_LOG_DIR / f"{sheet}.csv"
    return pd.read_csv(path) if path.exists() else pd.DataFrame()
