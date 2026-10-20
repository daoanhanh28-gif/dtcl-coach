# ĐTCL Coach v1.2 (2026-10-20) — cấu hình trung tâm
"""Đọc cấu hình từ st.secrets (Streamlit Cloud) hoặc biến môi trường (chạy local/test)."""
from __future__ import annotations

import json
import os
from contextlib import contextmanager
from functools import lru_cache, wraps
from pathlib import Path

APP_NAME = "ĐTCL Coach"
VERSION = "v1.2"
VERSION_DATE = "2026-10-20"
VERSION_LABEL = f"{VERSION} · {VERSION_DATE}"

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
LOCAL_LOG_DIR = DATA_DIR / "_logs"

# Bộ dữ liệu theo bản vá: bản mới nằm thẳng trong data/, bản cũ giữ trong data/ban/<bản>/ để xem song song.
# Thêm bản: chép data/*.json hiện tại vào data/ban/<bản cũ>/ rồi thêm một dòng ở đây (xem CAP_NHAT_META.md).
BO_DU_LIEU = {
    "18.5": (DATA_DIR, "Bản 18.5 · mới (số liệu 18.4b + thay đổi 18.5)"),
    "18.3b": (DATA_DIR / "ban" / "18.3b", "Bản 18.3b · cũ (file Excel v1.8)"),
}
BO_MAC_DINH = "18.5"


def get(key: str, default=None):
    """Ưu tiên st.secrets, sau đó biến môi trường."""
    try:
        import streamlit as st

        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.environ.get(key, default)


_BO_EP: str | None = None   # dùng trong kiểm thử / công cụ: ép một bộ dữ liệu


@contextmanager
def voi_bo(bo: str):
    """with config.voi_bo("18.3b"): ...  — chạy đoạn mã với bộ dữ liệu chỉ định (kiểm thử, công cụ)."""
    global _BO_EP
    cu, _BO_EP = _BO_EP, bo
    try:
        yield
    finally:
        _BO_EP = cu


def active_version() -> str:
    """Bộ dữ liệu đang xem — mỗi tab trình duyệt (mỗi phiên Streamlit) chọn riêng, mặc định bản mới."""
    if _BO_EP:
        return _BO_EP
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        if get_script_run_ctx() is None:
            return BO_MAC_DINH
        import streamlit as st

        v = st.session_state.get("bo")
        return v if v in BO_DU_LIEU else BO_MAC_DINH
    except Exception:
        return BO_MAC_DINH


@lru_cache(maxsize=None)
def _load(bo: str, name: str):
    with open(BO_DU_LIEU[bo][0] / name, encoding="utf-8") as f:
        return json.load(f)


def load_json(name: str, bo: str | None = None):
    return _load(bo or active_version(), name)


def theo_bo(fn):
    """Như lru_cache nhưng nhớ riêng cho từng bộ dữ liệu (18.5 / 18.3b)."""
    cached = lru_cache(maxsize=None)(lambda bo, *a: fn(*a))

    @wraps(fn)
    def wrapper(*a):
        return cached(active_version(), *a)

    wrapper.cache_clear = cached.cache_clear
    return wrapper
