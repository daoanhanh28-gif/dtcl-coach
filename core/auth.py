# ĐTCL Coach v1.0 (2026-10-06) — đăng nhập đơn giản bằng mã truy cập
"""
- Người chơi: nhập Tên + ACCESS_CODE (mã do chủ web đặt trong Secrets).
- Chủ web:    nhập Tên + ADMIN_CODE → xem được nhật ký của mọi người.
- Ghi nhớ đăng nhập: sau khi đăng nhập, trình duyệt giữ 1 cookie "dtcl_dn" có chữ ký HMAC
  (tên + quyền + hạn 90 ngày). Lần sau mở web tự vào thẳng. Đổi ACCESS_CODE / ADMIN_CODE trong Secrets
  → mọi ghi nhớ cũ tự hết hiệu lực. Đăng xuất → xoá cookie trên máy đó.
Mã lưu trong Secrets của Streamlit Cloud, không nằm trong code.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import unicodedata

import streamlit as st

from core import config


def _norm_name(name: str) -> str:
    name = " ".join(name.strip().split())
    return unicodedata.normalize("NFC", name).title()


def _match(a: str, b: str | None) -> bool:
    return bool(b) and hmac.compare_digest(a.strip().encode("utf-8"), str(b).strip().encode("utf-8"))


COOKIE = "dtcl_dn"
REMEMBER_DAYS = 90


def _secret() -> bytes:
    raw = "|".join(str(config.get(k, d)) for k, d in
                   (("ACCESS_CODE", "dtcl2026"), ("ADMIN_CODE", "admin2026"), ("COOKIE_SECRET", "")))
    return hashlib.sha256(("dtcl-coach|" + raw).encode("utf-8")).digest()


def make_token(user: dict, days: int = REMEMBER_DAYS) -> str:
    """Vé ghi nhớ: dữ liệu (base64) + chữ ký HMAC — không chứa mã truy cập, sửa tay là mất hiệu lực."""
    body = json.dumps({"n": user["name"], "a": bool(user["admin"]), "e": int(time.time()) + days * 86400},
                      ensure_ascii=False, separators=(",", ":"))
    data = base64.urlsafe_b64encode(body.encode("utf-8")).decode().rstrip("=")
    sig = hmac.new(_secret(), data.encode(), hashlib.sha256).hexdigest()[:40]
    return f"{data}.{sig}"


def read_token(tok: str | None) -> dict | None:
    try:
        data, sig = str(tok or "").split(".", 1)
        good = hmac.new(_secret(), data.encode(), hashlib.sha256).hexdigest()[:40]
        if not hmac.compare_digest(sig, good):
            return None
        d = json.loads(base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("utf-8"))
        if int(d["e"]) < time.time() or len(str(d["n"]).strip()) < 3:
            return None
        return {"name": str(d["n"]), "admin": bool(d["a"])}
    except (ValueError, KeyError, TypeError):
        return None


def restore_session() -> None:
    """Gọi đầu mỗi lượt chạy: chưa đăng nhập mà trình duyệt có vé hợp lệ → vào thẳng."""
    if st.session_state.get("user") or st.session_state.get("_da_dang_xuat"):
        return
    try:
        tok = st.context.cookies.get(COOKIE)
    except Exception:  # noqa: BLE001 — bản Streamlit cũ / chạy test
        tok = None
    u = read_token(tok)
    if u:
        st.session_state.user = u


def sync_cookie() -> None:
    """Ghi / xoá cookie ghi nhớ bằng 1 đoạn script ẩn (chạy 1 lần sau đăng nhập / đăng xuất)."""
    tok, drop = st.session_state.pop("_cookie_set", None), st.session_state.pop("_cookie_del", False)
    if not tok and not drop:
        return
    import streamlit.components.v1 as components
    val = f"{COOKIE}={tok}; Max-Age={REMEMBER_DAYS * 86400}" if tok else f"{COOKIE}=; Max-Age=0"
    js = (f"<script>(function(){{var c='{val}; Path=/; SameSite=Lax; Secure';"
          "try{window.parent.document.cookie=c;}catch(e){} try{document.cookie=c;}catch(e){}})();</script>")
    components.html(js, height=0)


def current_user() -> dict | None:
    return st.session_state.get("user")


def is_admin() -> bool:
    u = current_user()
    return bool(u and u.get("admin"))


def login_form():
    access = config.get("ACCESS_CODE", "dtcl2026")
    admin = config.get("ADMIN_CODE", "admin2026")
    with st.form("login", border=True):
        name = st.text_input("Tên hiển thị", placeholder="VD: Peach")
        code = st.text_input("Mã truy cập", type="password")
        nho = st.checkbox("Ghi nhớ đăng nhập trên máy này (90 ngày)", value=True)
        ok = st.form_submit_button("Vào ĐTCL Coach", type="primary", use_container_width=True)
    if ok:
        if len(name.strip()) < 3:
            st.error("Nhập tên (ít nhất 3 ký tự) để nhật ký ghi đúng người.")
        elif _match(code, admin) or _match(code, access):
            st.session_state.user = {"name": _norm_name(name), "admin": _match(code, admin)}
            st.session_state.pop("_da_dang_xuat", None)
            if nho:
                st.session_state["_cookie_set"] = make_token(st.session_state.user)
            st.rerun()
        else:
            st.error("Sai mã truy cập.")
    if not config.get("ACCESS_CODE"):
        st.caption("Đang dùng mã mặc định `dtcl2026` — "
                   "đổi trong Secrets trước khi chia sẻ link.")


def logout():
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.session_state["_da_dang_xuat"] = True     # không tự vào lại bằng cookie cũ trong phiên này
    st.session_state["_cookie_del"] = True
    st.rerun()
