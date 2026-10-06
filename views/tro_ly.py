# ĐTCL Coach v1.1 (2026-10-06) — trang Trợ lý ván đấu: bấm hình để nhập, đọc 4 dòng kết luận (luật trong code + AI diễn giải)
from collections import Counter

import streamlit as st

from core import coach, engine, ui
from core import plan as P

d = engine.data()
ui.header("Trợ lý ván đấu",
          "3 bước: ① chọn vòng, cấp, vàng, máu → ② bấm hình tướng và mảnh đồ đang có → ③ đọc 4 dòng kết luận. "
          "Muốn biết vì sao thì mở các thẻ bên dưới.")

ROUNDS = ["1-4"] + [f"{s}-{r}" for s in range(2, 8) for r in range(1, 8)]
champ_ids = [c[0] for c in ui.champ_options()]
emblem_ids = [e["id"] for e in d["trang_bi"]["an"]]
full_ids = [i["id"] for i in d["trang_bi"]["hoan_chinh"]]
augs = sorted(d["loi"], key=lambda a: (a["bac_so"], a["ten"]))
aug_ids = [a["id"] for a in augs]


def fmt_champ(cid):
    c = engine.champ(cid)
    return f"{c['ten']} · {c['gia']} vàng"


def fmt_aug(aid):
    a = d["aug"][aid]
    return f"{a['ten']} ({a['bac']})"


DEFAULTS = {"tl_round": "3-2", "tl_level": 6, "tl_gold": 30, "tl_hp": 70, "tl_streak": 0,
            "tl_units": [], "tl_items": [], "tl_augs": [], "tl_offer": []}
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)
for p in engine.COMPONENTS:
    st.session_state.setdefault(f"tl_p_{p}", 0)
for k in ("an_1", "an_2", "an_3"):
    st.session_state.setdefault(k, "— Không có —")


# ---------------------------------------------------------------- bấm hình (chạy trước khi vẽ lại trang)
def toggle_unit(cid):
    cur = list(st.session_state.tl_units)
    st.session_state.tl_units = [u for u in cur if u != cid] if cid in cur else cur + [cid]


def add_part(p):
    st.session_state[f"tl_p_{p}"] = min(9, int(st.session_state[f"tl_p_{p}"]) + 1)


def clear_parts():
    for p in engine.COMPONENTS:
        st.session_state[f"tl_p_{p}"] = 0


def clear_units():
    st.session_state.tl_units = []


def toggle_item(iid):
    cur = list(st.session_state.tl_items)
    st.session_state.tl_items = [i for i in cur if i != iid] if iid in cur else cur + [iid]


EMB_NAME = {engine.item_id(n): n for n in engine.emblem_names() if engine.item_id(n)}


def pick_emblem(iid):
    name = EMB_NAME.get(iid)
    if not name:
        return
    for k in ("an_1", "an_2", "an_3"):
        if st.session_state[k] == "— Không có —":
            st.session_state[k] = name
            return
    st.session_state["an_3"] = name


def clear_emblems():
    for k in ("an_1", "an_2", "an_3"):
        st.session_state[k] = "— Không có —"


tab1, tab2, tab3 = st.tabs(["Ván đấu", "Ấn → đội hình", "Lõi → cách đánh"])

# =============================================================================== VÁN ĐẤU
with tab1:
    with st.container(border=True):
        st.markdown("<div class='dc-step'>① Tình hình hiện tại</div>", unsafe_allow_html=True)
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.selectbox("Vòng", ROUNDS, key="tl_round")
        c2.number_input("Cấp", min_value=1, max_value=10, step=1, key="tl_level")
        c3.number_input("Vàng", min_value=0, max_value=200, step=1, key="tl_gold")
        c4.number_input("Máu", min_value=1, max_value=100, step=1, key="tl_hp")
        c5.number_input("Chuỗi (+thắng / −thua)", min_value=-15, max_value=15, step=1, key="tl_streak",
                        help="Đang thắng 3 trận liền nhập 3, thua 4 trận liền nhập −4.")

    with st.container(border=True):
        st.markdown("<div class='dc-step'>② Bấm hình tướng đang có (bấm lại để bỏ)</div>", unsafe_allow_html=True)
        sel = set(st.session_state.tl_units)
        cost_tabs = st.tabs([f"{g} vàng" for g in range(1, 6)])
        for g, t in zip(range(1, 6), cost_tabs):
            with t:
                ui.pick_grid(f"u{g}", [o for o in ui.champ_options() if engine.champ(o[0])["gia"] == g], sel, toggle_unit,
                             per_row=8)
        cA, cB = st.columns([4, 1])
        cA.multiselect("Hoặc gõ tên tướng", champ_ids, format_func=fmt_champ, key="tl_units", placeholder="Gõ tên tướng…")
        cB.button("Bỏ hết tướng", key="tl_clear_u", on_click=clear_units, use_container_width=True)

        st.markdown("<div class='dc-step'>Mảnh đồ đang giữ (mỗi lần bấm +1)</div>", unsafe_allow_html=True)
        cnt = {p: int(st.session_state[f"tl_p_{p}"]) for p in engine.COMPONENTS}
        ui.pick_grid("p", ui.item_options(engine.COMPONENTS), set(), add_part, per_row=10, names=False, counts=cnt)
        cA, cB = st.columns([4, 1])
        with cA.expander("Sửa số lượng mảnh"):
            cols = st.columns(5)
            for i, p in enumerate(engine.COMPONENTS):
                with cols[i % 5]:
                    st.number_input(engine.item_name(p), min_value=0, max_value=9, step=1, key=f"tl_p_{p}")
        cB.button("Xoá mảnh", key="tl_clear_p", on_click=clear_parts, use_container_width=True)

        st.markdown("<div class='dc-step'>Đồ hoàn chỉnh / Ấn đã có</div>", unsafe_allow_html=True)
        with st.expander("Bấm hình Ấn và trang bị"):
            have = set(st.session_state.tl_items)
            st.caption("Ấn")
            ui.pick_grid("e", ui.item_options(emblem_ids), have, toggle_item, per_row=10, names=False)
            st.caption("Trang bị hoàn chỉnh")
            ui.pick_grid("i", ui.item_options(full_ids), have, toggle_item, per_row=10, names=False)
        st.multiselect("Hoặc gõ tên đồ / Ấn", full_ids + emblem_ids, format_func=engine.item_name, key="tl_items",
                       placeholder="Gõ tên trang bị hoặc Ấn…")

        st.markdown("<div class='dc-step'>Lõi</div>", unsafe_allow_html=True)
        cc1, cc2 = st.columns(2)
        cc1.multiselect("Lõi đã chọn", aug_ids, format_func=fmt_aug, key="tl_augs", placeholder="Lõi đã lấy ở 2-1, 3-2…")
        cc2.multiselect("3 lõi đang hiện (nếu đang chọn lõi)", aug_ids, format_func=fmt_aug, key="tl_offer",
                        max_selections=3, placeholder="Chọn đúng 3 lõi trên màn hình")
        chips = "".join(ui.aug_chip(a) for a in st.session_state.tl_augs + st.session_state.tl_offer)
        if chips:
            st.markdown(f"<div class='dc-row'>{chips}</div>", unsafe_allow_html=True)

    stage, rnd = engine.parse_round(st.session_state.tl_round)
    parts = []
    for p in engine.COMPONENTS:
        parts += [p] * int(st.session_state[f"tl_p_{p}"])
    state = engine.GameState(units=list(st.session_state.tl_units), parts=parts,
                             items=list(st.session_state.tl_items), augments=list(st.session_state.tl_augs),
                             offered=list(st.session_state.tl_offer), hp=int(st.session_state.tl_hp),
                             gold=int(st.session_state.tl_gold), level=int(st.session_state.tl_level), stage=stage,
                             rnd=rnd, streak=int(st.session_state.tl_streak))
    adv = engine.advise(state)
    ranked = adv["doi_hinh"]
    top = ranked[0]["comp"] if ranked else None
    r = adv["roll"]
    plan = adv["do"]

    # ---- ③ KẾT LUẬN 4 DÒNG
    st.markdown("<div class='dc-step' style='margin-top:14px'>③ Kết luận</div>", unsafe_allow_html=True)
    if not (state.units or state.parts or state.items):
        ui.note("Chưa bấm tướng / đồ nên đội hình chỉ xếp theo hạng meta. Bấm càng đủ, gợi ý càng sát ván của bạn.")
    lines = []
    if top:
        carries = [x["tuong"] for x in top["chu_luc"]]
        lines.append(("🎯", f"Đi <b>{ui.esc(top['ten'])}</b> {ui.tier_badge(top['hang'])} — chủ lực "
                            + "".join(ui.champ_tile(c, 30, name=False) for c in carries)
                            + f" <span style='color:var(--mute);font-size:.85rem'>({ui.esc(top['kieu_ten'])})</span>"))
    lines.append(("💰", f"Lúc này: <b>{ui.esc(r['tieu_de'])}</b> <span style='color:var(--mute);font-size:.85rem'>"
                        f"(lãi vòng tới +{adv['nhip']['lai_vong_toi']} vàng)</span>"))
    if plan["uu_tien"]:
        x = plan["uu_tien"][0]
        lines.append(("🧩", f"Ghép ngay {ui.item_icon(x['do']['id'], 26)} <b>{ui.esc(x['do']['ten'])}</b> cho "
                            f"{ui.rich(x['cho'])}"))
    elif plan["du_phong"]:
        x = plan["du_phong"][0]
        lines.append(("🧩", f"Ghép {ui.item_icon(x['do']['id'], 26)} <b>{ui.esc(x['do']['ten'])}</b> (đồ dự phòng an toàn)"))
    else:
        lines.append(("🧩", "Chưa ghép được gì — giữ mảnh, " + ui.esc(plan["thu_tu_manh"] or "ưu tiên mảnh cho chủ lực")))
    if adv["loi"]:
        a = adv["loi"][0]["loi"]
        lines.append(("✨", f"Chọn lõi {ui.aug_icon(a['id'], 26)} <b>{ui.esc(a['ten'])}</b>"))
    elif top and top.get("loi_hop"):
        lines.append(("✨", "Lõi nên tìm: " + " ".join(ui.aug_chip(x) for x in top["loi_hop"][:3])))
    st.markdown("<div class='dc-card hi'><div class='dc-ans'>"
                + "".join(f"<div class='k'>{k}</div><div class='v'>{v}</div>" for k, v in lines) + "</div></div>",
                unsafe_allow_html=True)

    t_why, t_comp, t_aug, t_item, t_an, t_ai = st.tabs(["Vì sao", "Đội hình & form", "Lõi", "Ghép đồ", "Ấn & tộc hệ",
                                                         "AI giải thích"])
    nh = adv["nhip"]
    row = nh["dong"] or {}
    with t_why:
        st.markdown("## Lúc này nên làm gì")
        st.markdown(f"<div class='dc-card'><div class='dc-big'>{ui.esc(r['tieu_de'])}</div>"
                    f"<ul class='dc-why'>{''.join(f'<li>{ui.esc(x)}</li>' for x in r['ly_do'])}</ul>"
                    f"<div class='dc-stat'><div>Cấp mục tiêu<b>{ui.esc(row.get('cap', '—'))}</b></div>"
                    f"<div>Vàng mục tiêu<b>{ui.esc(row.get('vang', '—'))}</b></div>"
                    f"<div>Lãi vòng tới<b>+{nh['lai_vong_toi']} vàng</b></div>"
                    f"<div>Cần thêm để lên mốc lãi<b>{ui.esc(nh['can_them'])}</b></div></div></div>",
                    unsafe_allow_html=True)
        if row:
            st.markdown(f"- **Việc cần làm (lộ trình “{nh['loi_choi']}”):** {row['viec']}\n- **Sự kiện vòng này:** {row['su_kien']}")
        st.markdown(f"- **Theo chuỗi ({nh['chuoi_ten']}):** {nh['chuoi']}\n"
                    f"- **Theo máu ({nh['mau_ten']}):** {nh['mau']}\n- **Kiểm tra vàng:** {nh['vang']}")
        odds = engine.shop_odds(state.level)
        st.markdown(ui.html_table(["Cấp", "1 vàng", "2 vàng", "3 vàng", "4 vàng", "5 vàng"],
                                  [[state.level] + [f"{x}%" for x in odds]]), unsafe_allow_html=True)

    with t_comp:
        st.markdown("## Nên đi đội nào")
        if ranked:
            why = "".join(f"<li>{ui.rich(x)}</li>" for x in ranked[0]["ly_do"]) or "<li>Đội mạnh nhất meta hiện tại</li>"
            emb_have = [i for i in state.items if engine.item(i).get("loai") == "an"]
            ui.comp_card(top, highlight=True, show_plan=False,
                         extra_html=f"<div style='margin-top:10px;color:var(--mute);font-size:.82rem'>Điểm khớp {ranked[0]['diem']}</div>"
                                    f"<ul class='dc-why'>{why}</ul>")
            st.markdown("**Form theo vòng của đội này** (ai cầm Ấn bạn đang có, tướng tạm, vị trí đứng)")
            ui.stage_view(top, emb_have or None)
            st.markdown("**Hai phương án dự phòng**")
            cols = st.columns(2)
            for col, alt in zip(cols, ranked[1:3]):
                with col:
                    c = alt["comp"]
                    why = "".join(f"<li>{ui.rich(x)}</li>" for x in alt["ly_do"][:3])
                    st.markdown(f"<div class='dc-card'><div class='dc-row' style='gap:10px'>{ui.tier_badge(c['hang'])}"
                                f"<div><b>{ui.esc(c['ten'])}</b><div style='color:var(--mute);font-size:.82rem'>"
                                f"{ui.esc(c['kieu_ten'])} · điểm {alt['diem']}</div></div></div>"
                                f"<div style='margin-top:10px'>{ui.champ_row(c['tuong'], 40, ui.roles_of(c))}</div>"
                                f"<ul class='dc-why'>{why}</ul></div>", unsafe_allow_html=True)

    with t_aug:
        st.markdown("## Chọn lõi nào")
        if adv["loi"]:
            for i, x in enumerate(adv["loi"]):
                a = x["loi"]
                st.markdown(f"<div class='dc-card{' hi' if i == 0 else ''}'><div class='dc-row' style='gap:12px'>"
                            f"{ui.aug_icon(a['id'], 40)}<div><b>{'Nên chọn: ' if i == 0 else ''}{ui.esc(a['ten'])}</b> "
                            f"<span style='color:var(--mute)'>· {ui.esc(a['bac'])} · {ui.esc(a['nhom'])}</span>"
                            f"<div style='font-size:.85rem;color:var(--mute)'>{ui.esc(a['mo_ta'])}</div></div></div>"
                            f"<ul class='dc-why'>{''.join(f'<li>{ui.esc(y)}</li>' for y in x['ly_do'])}</ul></div>",
                            unsafe_allow_html=True)
        else:
            st.caption("Khi màn hình đang cho chọn lõi, nhập 3 lõi vào ô “3 lõi đang hiện” ở bước ②.")
        if top and top.get("loi_hop"):
            st.markdown(f"**Lõi hợp {ui.esc(top['ten'])}:**", unsafe_allow_html=True)
            st.markdown("<div class='dc-row'>" + "".join(ui.aug_chip(x) for x in top["loi_hop"]) + "</div>",
                        unsafe_allow_html=True)

    with t_item:
        st.markdown("## Ghép mảnh đồ nào trước")
        if plan["uu_tien"] or plan["du_phong"]:
            for x in plan["uu_tien"]:
                st.markdown(f"<div class='dc-row' style='margin:6px 0'>{ui.item_icon(x['do']['id'], 34)}"
                            f"<div><b>{ui.esc(x['do']['ten'])}</b> → {ui.rich(x['cho'])}<br>"
                            f"<span style='font-size:.82rem'>{' + '.join(ui.item_icon(m, 20) for m in x['manh'])} "
                            f"{ui.esc(' + '.join(engine.item_name(m) for m in x['manh']))}</span></div></div>",
                            unsafe_allow_html=True)
            for x in plan["du_phong"]:
                st.markdown(f"<div class='dc-row' style='margin:6px 0;opacity:.85'>{ui.item_icon(x['do']['id'], 30)}"
                            f"<div>{ui.esc(x['do']['ten'])} → {ui.esc(x['cho'])} <span style='color:var(--mute);font-size:.82rem'>"
                            f"(dự phòng an toàn)</span></div></div>", unsafe_allow_html=True)
        else:
            st.caption("Chưa ghép được món nào từ mảnh đang giữ.")
        if plan["con_lai"]:
            st.markdown("Mảnh còn để dành: " + "".join(ui.item_icon(p, 24) for p in plan["con_lai"]), unsafe_allow_html=True)
        if plan["thu_tu_manh"]:
            st.caption(f"Thứ tự ưu tiên mảnh của đội: {plan['thu_tu_manh']}")

    with t_an:
        if adv["an"]:
            st.markdown("## Ấn của bạn hợp đội nào (công thức trang CHỌN ẤN)")
            for x in adv["an"]:
                c = x["doi_hinh"]
                lines_an = "".join(f"<li>{ui.rich(l['an'])}: {ui.esc(l['dien_giai'])}</li>" for l in x["an"])
                st.markdown(f"<div class='dc-card'><b>{ui.esc(c['ten'])}</b> <span style='color:var(--mute)'>· điểm {x['diem']:.1f} "
                            f"(ấn +{x['diem_an']:.1f})</span><ul class='dc-why'>{lines_an}</ul></div>", unsafe_allow_html=True)
            st.caption("Chi tiết ai đeo, mốc tộc hệ, thay tướng nào để lên mốc cao hơn: thẻ “Ấn → đội hình”.")
        st.markdown("## Tộc / hệ của tướng đang có")
        if adv["toc_he"]:
            st.markdown("<div class='dc-row'>" + "".join(
                ui.trait_chip(t["id"], t["so"], t["kich_hoat"]) for t in adv["toc_he"]) + "</div>", unsafe_allow_html=True)
        else:
            st.caption("Bấm tướng ở bước ② để xem tộc / hệ đang kích hoạt.")

    with t_ai:
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
    st.markdown("Bấm tối đa 3 Ấn bạn đang có (từ lõi, Tinh Linh, vòng đi chợ hoặc tự ghép Siêu Xẻng / Chảo Vàng). "
                "Bấm 2 lần cùng một Ấn = có 2 Ấn cùng loại. Web xếp đội hợp nhất, chỉ ai đeo, mốc tộc/hệ đạt được ở "
                "cấp 8 và 9, thay tướng nào để lên mốc cao hơn, và giai đoạn đầu ai cầm Ấn.")
    names = ["— Không có —"] + engine.emblem_names()
    ui.pick_grid("an", ui.item_options([i for i in EMB_NAME]), set(), pick_emblem, per_row=10, names=False,
                 counts=dict(Counter(engine.item_id(st.session_state[k]) for k in ("an_1", "an_2", "an_3")
                                     if st.session_state[k] != "— Không có —")))
    c1, c2, c3, c4 = st.columns([1, 1, 1, 0.6])
    e1 = c1.selectbox("Ấn thứ 1", names, key="an_1")
    e2 = c2.selectbox("Ấn thứ 2", names, key="an_2")
    e3 = c3.selectbox("Ấn thứ 3", names, key="an_3")
    with c4:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        st.button("Xoá Ấn", key="an_clear", on_click=clear_emblems, use_container_width=True)
    lean = st.selectbox("Đồ bạn đang có nghiêng về", an["loai_do"], key="an_lean")
    sel = [e for e in (e1, e2, e3) if e != "— Không có —"]
    sel_ids = [i for i in (engine.item_id(e) for e in sel) if i]
    for e in dict.fromkeys(sel):
        info = engine.emblem_info(e)
        if info:
            st.markdown(f"<div style='font-size:.85rem'>{ui.rich(e)}: {ui.esc(info['cong_thuc'])} · {ui.esc(info['hieu_ung'])}</div>",
                        unsafe_allow_html=True)
    res = engine.emblem_rank(sel, an["loai_do"].index(lean))
    for i, x in enumerate(res[:3]):
        c = x["doi_hinh"]
        units, core = P.an_comp_units(c)
        medal = ["Top 1", "Top 2", "Top 3"][i]
        lines_an = "".join(f"<li>{ui.rich(l['an'])}: {ui.esc(l['dien_giai'])} · +{l['diem']:.1f} điểm</li>" for l in x["an"])
        roles = {}
        for k in ("chu_luc", "chu_luc_phu", "do_don"):
            cid = engine.champ_id(c[k]["tuong"])
            if cid:
                roles[cid] = [i2 for i2 in (engine.item_id(n) for n in c[k]["do"]) if i2]
        st.markdown(f"<div class='dc-card{' hi' if i == 0 else ''}'><div style='color:var(--mute);font-size:.82rem'>{medal} · "
                    f"điểm {x['diem']:.1f} (ấn +{x['diem_an']:.1f})</div><div style='font-weight:700;font-size:1.05rem'>"
                    f"{ui.esc(c['ten'])}</div><div style='font-size:.85rem;color:var(--mute)'>{ui.esc(c['so_lieu_vn'])} · "
                    f"{ui.esc(c['ban_moi'])}</div><div style='margin:10px 0'>{ui.champ_row(units, 44, roles)}</div>"
                    f"<ul class='dc-why'>{lines_an or '<li>Chưa chọn Ấn — xếp theo sức mạnh đội.</li>'}</ul>"
                    f"<div style='font-size:.85rem'>Lên cấp: {ui.rich(c['len_cap'])}</div></div>", unsafe_allow_html=True)
        if not sel_ids:
            continue
        with st.expander(f"Tối ưu mốc tộc/hệ với Ấn — {c['ten']}", expanded=i == 0):
            cols = st.columns(2)
            for col, lv in zip(cols, (8, 9)):
                ep = P.emblem_plan(units, sel_ids, core, lv)
                with col:
                    tags = {u: "Ấn" for u in ep["nguoi_deo"].values()}
                    st.markdown(f"**Cấp {lv}**")
                    st.markdown(ui.champ_row(ep["doi"], 40, tags=tags), unsafe_allow_html=True)
                    out = []
                    for a in ep["an"]:
                        if a["khong_ai_deo"]:
                            out.append(f"{engine.item_name(a['an'])}: cả đội đều đã có {P.trait_name(a['toc_he'])} — "
                                       f"Ấn này chỉ còn chỉ số, nên bán / đổi hướng.")
                            continue
                        who = engine.champ(a["nguoi_deo"])["ten"]
                        s = f"{engine.item_name(a['an'])} → {who}: {P.trait_name(a['toc_he'])} {a['truoc']} → {a['sau']}"
                        if a["len_moc"]:
                            s += f" (đạt mốc {a['moc_dat']})"
                        elif a["moc_dat"]:
                            s += f" (giữ mốc {a['moc_dat']})"
                        else:
                            s += " (chưa đủ mốc)"
                        if a["moc_tiep"]:
                            s += f" · mốc tiếp theo {a['moc_tiep']} cần thêm {a['moc_tiep'] - a['sau']} tướng"
                        out.append(s)
                    st.markdown("<ul class='dc-why'>" + "".join(f"<li>{ui.rich(o)}</li>" for o in out) + "</ul>",
                                unsafe_allow_html=True)
                    st.markdown("<div class='dc-row'>" + "".join(ui.trait_chip(t["id"], t["so"]) for t in ep["toc_he"])
                                + "</div>", unsafe_allow_html=True)
                    if ep["goi_y"]:
                        st.markdown("<div style='margin-top:8px;font-weight:700'>Đổi 1 tướng để lên mốc cao hơn</div>",
                                    unsafe_allow_html=True)
                        for g in ep["goi_y"]:
                            act = (f"Thay {ui.champ_tile(g['bo'], 30, name=False)} {ui.esc(engine.champ(g['bo'])['ten'])} → "
                                   if g["bo"] else "Thêm ")
                            st.markdown(f"<div class='dc-row' style='margin:4px 0'>{act}{ui.champ_tile(g['them'], 30, name=False)} "
                                        f"<b>{ui.esc(engine.champ(g['them'])['ten'])}</b> "
                                        f"<span style='font-size:.82rem;color:var(--mute)'>({engine.champ(g['them'])['gia']} vàng)</span>"
                                        f"<span style='font-size:.85rem'>· {ui.rich('; '.join(g['doi']))}</span></div>",
                                        unsafe_allow_html=True)
                    else:
                        st.caption("Đã là cách xếp tốt nhất cho mốc tộc/hệ — không cần đổi tướng.")
            early = P.emblem_holder_early(c, sel_ids)
            if early:
                st.markdown("**Giai đoạn đầu: ai cầm Ấn tạm**")
                for g in early:
                    tags = {u: "tạm" for u in g["tam"]}
                    for a in g["an"]:
                        if a["nguoi_deo"]:
                            tags[a["nguoi_deo"]] = "Ấn"
                    txt = []
                    for a in g["an"]:
                        if not a["nguoi_deo"]:
                            txt.append(f"{engine.item_name(a['an'])}: cất chờ {engine.champ(a['chuyen_cho'])['ten']}")
                            continue
                        who = engine.champ(a["nguoi_deo"])["ten"]
                        t = f"{engine.item_name(a['an'])} cho {who} ({P.trait_name(a['toc_he'])} {a['sau']}"
                        t += ", mở mốc)" if a["len_moc"] else ")"
                        if a["tam"] and a["chuyen_cho"]:
                            t += f" → sau chuyển cho {engine.champ(a['chuyen_cho'])['ten']}"
                        txt.append(t)
                    st.markdown(f"<div class='dc-row' style='margin:6px 0;align-items:center'>"
                                f"<b style='width:70px'>{ui.esc(g['ten'])}</b>{ui.champ_row(g['tuong'], 34, tags=tags, dim=set(g['tam']))}"
                                f"<span style='font-size:.85rem'>{ui.rich('; '.join(txt))}</span></div>", unsafe_allow_html=True)
                st.caption("Bán tướng thì đồ trên người tự về hàng chờ — cứ đeo Ấn ngay cho tướng đang trên bàn để có mốc tộc/hệ sớm.")
    with st.expander("Bảng xếp hạng tất cả đội với Ấn đã chọn"):
        st.markdown(ui.html_table(["#", "Đội hình", "Tổng điểm", "Từ ấn", "Chủ lực chính", "Bản 18.4"],
                                  [[i + 1, x["doi_hinh"]["ten"], f"{x['diem']:.1f}", f"{x['diem_an']:.1f}",
                                    f"{x['doi_hinh']['chu_luc']['tuong']} ({x['doi_hinh']['chu_luc']['kieu']})",
                                    x["doi_hinh"]["ban_moi"]] for i, x in enumerate(res)], rich_text=True), unsafe_allow_html=True)
    with st.expander("Bảng tra 21 Ấn — công thức, hiệu ứng, ai đeo tốt nhất"):
        st.markdown(ui.html_table(["Ấn", "Công thức / nguồn", "Hiệu ứng riêng", "Đeo tốt nhất (hạng TB)", "Hạng TB"],
                                  [[e["ten"], e["cong_thuc"], e["hieu_ung"], e["deo_tot_nhat"], e["hang_tb"]] for e in an["an"]],
                                  rich_text=True), unsafe_allow_html=True)
    st.caption(an["cach_tinh"] + " Tối ưu mốc: đếm lại tộc/hệ khi Ấn đeo cho tướng chưa có tộc đó; mốc càng cao càng được "
               "tính nhiều điểm; không bao giờ đổi mất mốc của tộc/hệ chính hay tộc của Ấn.")

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
            f"<p style='margin:6px 0'><b style='color:var(--gold)'>{ui.esc(k)}.</b> {ui.rich(v)}</p>" for k, v in rows)
            + "</div>", unsafe_allow_html=True)
    st.caption(hl["quy_tac_chung"])

ui.source_note()
