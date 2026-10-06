# ĐTCL Coach v1.0 (2026-10-06) — trang Trợ lý ván đấu (luật trong code + AI diễn giải)
import streamlit as st

from core import coach, engine, ui

d = engine.data()
ui.header("Trợ lý ván đấu",
          "Nhập những gì đang có trong ván. Web tính sẵn: nên đi đội nào (kèm 2 dự phòng), lúc này lên cấp "
          "hay đổi tướng, chọn lõi nào, ghép mảnh đồ nào trước.")

ROUNDS = ["1-4"] + [f"{s}-{r}" for s in range(2, 8) for r in range(1, 8)]
champs = sorted(d["tuong"], key=lambda c: (c["gia"], c["ten"]))
champ_ids = [c["id"] for c in champs]
full_items = [i["id"] for i in d["trang_bi"]["hoan_chinh"]] + [e["id"] for e in d["trang_bi"]["an"]]
augs = sorted(d["loi"], key=lambda a: (a["bac_so"], a["ten"]))
aug_ids = [a["id"] for a in augs]


def fmt_champ(cid):
    c = engine.champ(cid)
    return f"{c['ten']} · {c['gia']} vàng"


def fmt_aug(aid):
    a = d["aug"][aid]
    return f"{a['ten']} ({a['bac']})"


DEFAULTS = {"tl_round": "3-2", "tl_level": 6, "tl_gold": 30, "tl_hp": 70, "tl_streak": 0}
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)
for p in engine.COMPONENTS:
    st.session_state.setdefault(f"tl_p_{p}", 0)

tab1, tab2, tab3 = st.tabs(["Ván đấu", "Ấn → đội hình", "Lõi → cách đánh"])

# =============================================================================== VÁN ĐẤU
with tab1:
    with st.container(border=True):
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.selectbox("Vòng", ROUNDS, key="tl_round")
        c2.number_input("Cấp", min_value=1, max_value=10, step=1, key="tl_level")
        c3.number_input("Vàng", min_value=0, max_value=200, step=1, key="tl_gold")
        c4.number_input("Máu", min_value=1, max_value=100, step=1, key="tl_hp")
        c5.number_input("Chuỗi (+thắng / −thua)", min_value=-15, max_value=15, step=1, key="tl_streak",
                        help="Ví dụ đang thắng 3 trận liền nhập 3, thua 4 trận liền nhập −4.")
        st.multiselect("Tướng đang có (trên bàn + hàng chờ)", champ_ids, format_func=fmt_champ, key="tl_units",
                       placeholder="Gõ tên tướng…")
        st.markdown("**Mảnh đồ đang giữ**")
        cols = st.columns(5)
        for i, p in enumerate(engine.COMPONENTS):
            with cols[i % 5]:
                st.markdown(ui.item_icon(p, 22, True), unsafe_allow_html=True)
                st.number_input(engine.item_name(p), min_value=0, max_value=9, step=1, key=f"tl_p_{p}",
                                label_visibility="collapsed")
        st.multiselect("Đồ hoàn chỉnh / Ấn đã có", full_items, format_func=engine.item_name, key="tl_items",
                       placeholder="Gõ tên trang bị hoặc Ấn…")
        cc1, cc2 = st.columns(2)
        cc1.multiselect("Lõi đã chọn", aug_ids, format_func=fmt_aug, key="tl_augs", placeholder="Lõi đã lấy ở 2-1, 3-2…")
        cc2.multiselect("3 lõi đang hiện (nếu đang chọn lõi)", aug_ids, format_func=fmt_aug, key="tl_offer",
                        max_selections=3, placeholder="Chọn đúng 3 lõi trên màn hình")

    stage, rnd = engine.parse_round(st.session_state.tl_round)
    parts = []
    for p in engine.COMPONENTS:
        parts += [p] * int(st.session_state[f"tl_p_{p}"])
    state = engine.GameState(units=list(st.session_state.get("tl_units", [])), parts=parts,
                             items=list(st.session_state.get("tl_items", [])),
                             augments=list(st.session_state.get("tl_augs", [])),
                             offered=list(st.session_state.get("tl_offer", [])),
                             hp=int(st.session_state.tl_hp), gold=int(st.session_state.tl_gold),
                             level=int(st.session_state.tl_level), stage=stage, rnd=rnd,
                             streak=int(st.session_state.tl_streak))
    adv = engine.advise(state)

    if not (state.units or state.parts or state.items):
        ui.note("Chưa nhập tướng / đồ nên đội hình bên dưới chỉ xếp theo hạng meta. "
                "Nhập càng đủ, gợi ý càng sát ván của bạn.")

    # ---- 1. Hành động ngay
    r = adv["roll"]
    nh = adv["nhip"]
    row = nh["dong"] or {}
    st.markdown("## Lúc này nên làm gì")
    st.markdown(f"<div class='dc-card hi'><div class='dc-big'>{ui.esc(r['tieu_de'])}</div>"
                f"<ul class='dc-why'>{''.join(f'<li>{ui.esc(x)}</li>' for x in r['ly_do'])}</ul>"
                f"<div class='dc-stat'><div>Cấp mục tiêu<b>{ui.esc(row.get('cap', '—'))}</b></div>"
                f"<div>Vàng mục tiêu<b>{ui.esc(row.get('vang', '—'))}</b></div>"
                f"<div>Lãi vòng tới<b>+{nh['lai_vong_toi']} vàng</b></div>"
                f"<div>Cần thêm để lên mốc lãi<b>{ui.esc(nh['can_them'])}</b></div></div></div>",
                unsafe_allow_html=True)
    with st.expander(f"Lộ trình “{nh['loi_choi']}” ở vòng {state.stage}-{state.rnd} (theo Excel)", expanded=True):
        if row:
            st.markdown(f"- **Việc cần làm:** {row['viec']}\n- **Sự kiện vòng này:** {row['su_kien']}")
        st.markdown(f"- **Theo chuỗi ({nh['chuoi_ten']}):** {nh['chuoi']}\n"
                    f"- **Theo máu ({nh['mau_ten']}):** {nh['mau']}\n- **Kiểm tra vàng:** {nh['vang']}")
        odds = engine.shop_odds(state.level)
        st.markdown(ui.html_table(["Cấp", "1 vàng", "2 vàng", "3 vàng", "4 vàng", "5 vàng"],
                                  [[state.level] + [f"{x}%" for x in odds]]), unsafe_allow_html=True)

    # ---- 2. Đội hình
    st.markdown("## Nên đi đội nào")
    ranked = adv["doi_hinh"]
    if ranked:
        top = ranked[0]
        why = "".join(f"<li>{ui.esc(x)}</li>" for x in top["ly_do"]) or "<li>Đội mạnh nhất meta hiện tại</li>"
        ui.comp_card(top["comp"], highlight=True,
                     extra_html=f"<div style='margin-top:10px;color:var(--mute);font-size:.82rem'>Điểm khớp {top['diem']}</div>"
                                f"<ul class='dc-why'>{why}</ul>")
        st.markdown("**Hai phương án dự phòng**")
        cols = st.columns(2)
        for col, alt in zip(cols, ranked[1:3]):
            with col:
                c = alt["comp"]
                why = "".join(f"<li>{ui.esc(x)}</li>" for x in alt["ly_do"][:3])
                st.markdown(f"<div class='dc-card'><div class='dc-row' style='gap:10px'>{ui.tier_badge(c['hang'])}"
                            f"<div><b>{ui.esc(c['ten'])}</b><div style='color:var(--mute);font-size:.82rem'>"
                            f"{ui.esc(c['kieu_ten'])} · điểm {alt['diem']}</div></div></div>"
                            f"<div style='margin-top:10px'>{ui.champ_row(c['tuong'], 40, ui.roles_of(c))}</div>"
                            f"<ul class='dc-why'>{why}</ul></div>", unsafe_allow_html=True)

    # ---- 3. Lõi
    if adv["loi"]:
        st.markdown("## Chọn lõi nào")
        for i, x in enumerate(adv["loi"]):
            a = x["loi"]
            img = f"<img class='dc-ico' style='--s:40px' src='{a['anh']}' alt=''>" if a.get("anh") else ""
            st.markdown(f"<div class='dc-card{' hi' if i == 0 else ''}'><div class='dc-row' style='gap:12px'>{img}"
                        f"<div><b>{'Nên chọn: ' if i == 0 else ''}{ui.esc(a['ten'])}</b> "
                        f"<span style='color:var(--mute)'>· {ui.esc(a['bac'])} · {ui.esc(a['nhom'])}</span>"
                        f"<div style='font-size:.85rem;color:var(--mute)'>{ui.esc(a['mo_ta'])}</div></div></div>"
                        f"<ul class='dc-why'>{''.join(f'<li>{ui.esc(y)}</li>' for y in x['ly_do'])}</ul></div>",
                        unsafe_allow_html=True)

    # ---- 4. Đồ
    st.markdown("## Ghép mảnh đồ nào trước")
    plan = adv["do"]
    if plan["uu_tien"] or plan["du_phong"]:
        for x in plan["uu_tien"]:
            st.markdown(f"<div class='dc-row' style='margin:6px 0'>{ui.item_icon(x['do']['id'], 34)}"
                        f"<div><b>{ui.esc(x['do']['ten'])}</b> → {ui.esc(x['cho'])}<br><span style='color:var(--mute);font-size:.82rem'>"
                        f"{ui.esc(' + '.join(engine.item_name(m) for m in x['manh']))}</span></div></div>", unsafe_allow_html=True)
        for x in plan["du_phong"]:
            st.markdown(f"<div class='dc-row' style='margin:6px 0;opacity:.85'>{ui.item_icon(x['do']['id'], 30)}"
                        f"<div>{ui.esc(x['do']['ten'])} → {ui.esc(x['cho'])} <span style='color:var(--mute);font-size:.82rem'>"
                        f"(dự phòng an toàn)</span></div></div>", unsafe_allow_html=True)
    else:
        st.caption("Chưa ghép được món nào từ mảnh đang giữ.")
    if plan["con_lai"]:
        st.caption("Mảnh còn để dành: " + ", ".join(engine.item_name(p) for p in plan["con_lai"]))
    if plan["thu_tu_manh"]:
        st.caption(f"Thứ tự ưu tiên mảnh của đội: {plan['thu_tu_manh']}")

    # ---- 5. Ấn
    if adv["an"]:
        st.markdown("## Ấn của bạn hợp đội nào (công thức trang CHỌN ẤN)")
        for x in adv["an"]:
            c = x["doi_hinh"]
            lines = "".join(f"<li>{ui.esc(l['an'])}: {ui.esc(l['dien_giai'])}</li>" for l in x["an"])
            st.markdown(f"<div class='dc-card'><b>{ui.esc(c['ten'])}</b> <span style='color:var(--mute)'>· điểm {x['diem']:.1f} "
                        f"(ấn +{x['diem_an']:.1f})</span><ul class='dc-why'>{lines}</ul></div>", unsafe_allow_html=True)

    # ---- 6. Tộc hệ
    if adv["toc_he"]:
        st.markdown("## Tộc / hệ của tướng đang có")
        st.markdown("<div class='dc-row'>" + "".join(
            ui.trait_chip(t["id"], t["so"], t["kich_hoat"]) for t in adv["toc_he"]) + "</div>", unsafe_allow_html=True)

    # ---- 7. AI
    st.markdown("## Giải thích thêm")
    if st.button("Nhờ AI giải thích ngắn gọn", key="tl_ai"):
        with st.spinner("Đang hỏi AI…"):
            txt, online = coach.explain(state, adv)
        st.session_state["tl_ai_txt"] = (txt, online)
    if st.session_state.get("tl_ai_txt"):
        txt, online = st.session_state["tl_ai_txt"]
        st.markdown(txt)
        st.caption("AI chỉ diễn giải — kết luận do bộ luật của web tính." if online
                   else "Chưa bật AI (thiếu khoá Gemini) — đây là lời giải thích soạn sẵn.")

# =============================================================================== ẤN → ĐỘI HÌNH
with tab2:
    an = d["hd_an"]
    st.markdown("Chọn tối đa 3 Ấn bạn đang có (từ lõi, Tinh Linh, vòng đi chợ hoặc tự ghép Xẻng / Chảo) "
                "và loại đồ bạn cầm nhiều nhất. Chọn 2 Ấn giống nhau = có 2 Ấn cùng loại.")
    names = ["— Không có —"] + engine.emblem_names()
    c1, c2, c3 = st.columns(3)
    e1 = c1.selectbox("Ấn thứ 1", names, key="an_1")
    e2 = c2.selectbox("Ấn thứ 2", names, key="an_2")
    e3 = c3.selectbox("Ấn thứ 3", names, key="an_3")
    lean = st.selectbox("Đồ bạn đang có nghiêng về", an["loai_do"], key="an_lean")
    sel = [e for e in (e1, e2, e3) if e != "— Không có —"]
    for e in dict.fromkeys(sel):
        info = engine.emblem_info(e)
        if info:
            st.caption(f"{e}: {info['cong_thuc']} · {info['hieu_ung']}")
    res = engine.emblem_rank(sel, an["loai_do"].index(lean))
    for i, x in enumerate(res[:3]):
        c = x["doi_hinh"]
        medal = ["Top 1", "Top 2", "Top 3"][i]
        lines = "".join(f"<li>{ui.esc(l['an'])}: {ui.esc(l['dien_giai'])} · +{l['diem']:.1f} điểm</li>" for l in x["an"])
        ids = [cid for cid in (engine.champ_id(n) for n in c["tuong"]) if cid]
        roles = {}
        for k in ("chu_luc", "chu_luc_phu", "do_don"):
            cid = engine.champ_id(c[k]["tuong"])
            if cid:
                roles[cid] = [i2 for i2 in (engine.item_id(n) for n in c[k]["do"]) if i2]
        st.markdown(f"<div class='dc-card{' hi' if i == 0 else ''}'><div style='color:var(--mute);font-size:.82rem'>{medal} · "
                    f"điểm {x['diem']:.1f} (ấn +{x['diem_an']:.1f})</div><div style='font-weight:700;font-size:1.05rem'>"
                    f"{ui.esc(c['ten'])}</div><div style='font-size:.85rem;color:var(--mute)'>{ui.esc(c['so_lieu_vn'])} · "
                    f"{ui.esc(c['ban_moi'])}</div><div style='margin:10px 0'>{ui.champ_row(ids, 44, roles)}</div>"
                    f"<div style='font-size:.88rem'>Chủ lực chính: <b>{ui.esc(c['chu_luc']['tuong'])}</b> ({ui.esc(c['chu_luc']['kieu'])}) · "
                    f"Chủ lực phụ: <b>{ui.esc(c['chu_luc_phu']['tuong'])}</b> ({ui.esc(c['chu_luc_phu']['kieu'])}) · "
                    f"Đỡ đòn: <b>{ui.esc(c['do_don']['tuong'])}</b></div>"
                    f"<ul class='dc-why'>{lines or '<li>Chưa chọn Ấn — xếp theo sức mạnh đội.</li>'}</ul>"
                    f"<div style='font-size:.85rem'>Lên cấp: {ui.esc(c['len_cap'])}</div></div>", unsafe_allow_html=True)
    with st.expander("Bảng xếp hạng tất cả đội với Ấn đã chọn"):
        st.markdown(ui.html_table(["#", "Đội hình", "Tổng điểm", "Từ ấn", "Chủ lực chính", "Bản 18.4"],
                                  [[i + 1, x["doi_hinh"]["ten"], f"{x['diem']:.1f}", f"{x['diem_an']:.1f}",
                                    f"{x['doi_hinh']['chu_luc']['tuong']} ({x['doi_hinh']['chu_luc']['kieu']})",
                                    x["doi_hinh"]["ban_moi"]] for i, x in enumerate(res)]), unsafe_allow_html=True)
    with st.expander("Bảng tra 21 Ấn — công thức, hiệu ứng, ai đeo tốt nhất"):
        st.markdown(ui.html_table(["Ấn", "Công thức / nguồn", "Hiệu ứng riêng", "Đeo tốt nhất (hạng TB)", "Hạng TB"],
                                  [[e["ten"], e["cong_thuc"], e["hieu_ung"], e["deo_tot_nhat"], e["hang_tb"]] for e in an["an"]]),
                    unsafe_allow_html=True)
    st.caption(an["cach_tinh"])

# =============================================================================== LÕI → CÁCH ĐÁNH
with tab3:
    hl = d["hd_loi"]
    st.markdown("Chọn lõi vừa nhận cho bạn cái gì + bậc + vòng + máu → kế hoạch lên cấp, đổi tướng, đội hình hợp nhất.")
    c1, c2, c3, c4 = st.columns(4)
    loai = c1.selectbox("Lõi cho bạn cái gì?", [x["ten"] for x in hl["loai_loi"]], key="lc_loai")
    bac = c2.selectbox("Bậc lõi", ["Bạc", "Vàng", "Kim Cương"], index=1, key="lc_bac")
    vong = c3.selectbox("Nhận ở vòng", ["2-1", "3-2", "4-2"], key="lc_vong")
    mau = c4.selectbox("Máu hiện tại", [m["ten"] for m in hl["theo_mau"]], key="lc_mau")
    p = engine.aug_plan(loai, bac, vong, mau)
    if p:
        rows = [("Bạn nhận được", p["nhan"]), ("Lõi loại này (xếp hạng)", p["vi_du"]), ("Theo bậc lõi", p["theo_bac"]),
                ("Theo vòng nhận", p["theo_vong"]), ("Theo máu", p["theo_mau"]), ("Nhịp lên cấp", p["len_cap"]),
                ("Đổi tướng", p["doi_tuong"]), ("Chuỗi thắng / thua", p["chuoi"]),
                ("Đội hình hợp nhất", " · ".join(p["doi_hinh"])), ("Lõi tiếp theo nên tìm", p["loi_sau"]),
                ("Sai lầm cần tránh", p["tranh"])]
        st.markdown("<div class='dc-card'>" + "".join(
            f"<p style='margin:6px 0'><b style='color:var(--gold)'>{ui.esc(k)}.</b> {ui.esc(v)}</p>" for k, v in rows)
            + "</div>", unsafe_allow_html=True)
    st.caption(hl["quy_tac_chung"])

ui.source_note()
