# ĐTCL Coach v1.0 (2026-10-06) — trang Luyện tập (10 câu tình huống ngẫu nhiên, chấm điểm, giải thích)
import random

import streamlit as st

from core import auth, db, engine, ui

ui.header("Luyện tập",
          "Mỗi lượt rút ngẫu nhiên 10 câu tình huống: chọn lõi, ghép đồ, đổi tướng hay lên cấp, kinh tế, xếp bàn. "
          "Nộp bài để xem điểm và giải thích từng câu.")

nhoms = sorted({q["nhom"] for q in engine.data()["cau_hoi"]["cau_hoi"]})
c1, c2 = st.columns([2, 1])
nhom = c1.selectbox("Chủ đề", ["Tất cả"] + nhoms, key="lt_nhom")
with c2:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    new = st.button("Lượt mới", type="primary", use_container_width=True)

if new or "lt_seed" not in st.session_state or st.session_state.get("lt_nhom_cur") != nhom:
    st.session_state["lt_seed"] = random.randint(1, 10**9)
    st.session_state["lt_nhom_cur"] = nhom
    st.session_state["lt_round"] = st.session_state.get("lt_round", 0) + 1
    st.session_state.pop("lt_result", None)

seed = st.session_state["lt_seed"]
qs = engine.quiz_pick(10, seed=seed, nhom=None if nhom == "Tất cả" else nhom)
rk = st.session_state["lt_round"]

with st.form(f"quiz_{rk}"):
    for i, q in enumerate(qs, 1):
        st.markdown(f"**Câu {i}.** {q['cau_hoi']}  \n<span style='color:var(--mute);font-size:.8rem'>{q['nhom']}</span>",
                    unsafe_allow_html=True)
        st.radio(f"Câu {i}", list(range(len(q["lua_chon"]))), format_func=lambda j, q=q: q["lua_chon"][j],
                 index=None, key=f"lt_{rk}_{q['id']}", label_visibility="collapsed")
    done = st.form_submit_button("Nộp bài", type="primary", use_container_width=True)

if done:
    answers = {q["id"]: st.session_state.get(f"lt_{rk}_{q['id']}") for q in qs}
    res = engine.quiz_score(qs, answers)
    st.session_state["lt_result"] = (res, answers)
    u = auth.current_user() or {}
    db.log("luyen_tap", {"nguoi_choi": u.get("name", ""), "chu_de": nhom, "dung": res["dung"], "tong": res["tong"],
                         "phan_tram": res["phan_tram"]})

if st.session_state.get("lt_result"):
    res, answers = st.session_state["lt_result"]
    st.markdown(f"<div class='dc-card hi'><div class='dc-big'>{res['dung']}/{res['tong']} câu đúng · {res['phan_tram']}%</div>"
                f"<p style='margin:6px 0 0'>{ui.esc(res['loi_nhan'])}</p></div>", unsafe_allow_html=True)
    for i, q in enumerate(qs, 1):
        ok = q["id"] in res["dung_ids"]
        chosen = answers.get(q["id"])
        mine = q["lua_chon"][chosen] if chosen is not None else "(bỏ trống)"
        st.markdown(f"<div class='dc-card' style='border-color:{'#2F6B4F' if ok else '#6B3B2F'}'>"
                    f"<b>Câu {i}: {'Đúng' if ok else 'Chưa đúng'}</b> — {ui.esc(q['cau_hoi'])}<br>"
                    f"<span style='color:var(--mute)'>Bạn chọn: {ui.esc(mine)} · Đáp án: <b>{ui.esc(q['lua_chon'][q['dap_an']])}</b></span>"
                    f"<p style='margin:6px 0 0'>{ui.esc(q['giai_thich'])}</p></div>", unsafe_allow_html=True)
    st.caption("Bấm “Lượt mới” để rút 10 câu khác.")
