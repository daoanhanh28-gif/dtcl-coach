# ĐTCL Coach v1.1 (2026-10-06) — trang Trang bị & Ấn
import streamlit as st

from core import engine, ui
from core import plan as P

d = engine.data()
kt = d["hd_kien_thuc"]
ui.header("Trang bị & Ấn",
          "Bấm 2 mảnh để xem món ghép ra, ai nên cầm, đội nào dùng. Kèm bảng ghép đầy đủ, đồ khởi đầu → hướng đội hình, "
          "Ấn và Tạo Tác.")

tab1, tab6, tab2, tab3, tab4, tab5 = st.tabs(["Ghép đồ", "Đồ theo tướng", "Bảng ghép", "Đồ khởi đầu → đội", "Ấn",
                                              "Tạo Tác & nguyên tắc"])
comp_ids = engine.COMPONENTS
st.session_state.setdefault("td_a", "BFSword")
st.session_state.setdefault("td_b", "SparringGloves")
st.session_state.setdefault("td_next", "td_a")


def pick_part(p):
    k = st.session_state.td_next
    st.session_state[k] = p
    st.session_state.td_next = "td_b" if k == "td_a" else "td_a"


def pick_champ(cid):
    st.session_state.td_champ = cid


with tab1:
    st.caption("Bấm 2 mảnh liên tiếp (mảnh 1 rồi mảnh 2), hoặc chọn trong 2 ô bên dưới.")
    ui.pick_grid("td", ui.item_options(comp_ids), {st.session_state.td_a, st.session_state.td_b}, pick_part,
                 per_row=10, names=False)
    c1, c2 = st.columns(2)
    a = c1.selectbox("Mảnh thứ 1", comp_ids, format_func=engine.item_name, key="td_a")
    b = c2.selectbox("Mảnh thứ 2", comp_ids, format_func=engine.item_name, key="td_b")
    it = engine.combine(a, b)
    if not it:
        st.info("Hai mảnh này không ghép được thành món nào.")
    else:
        ex = it.get("excel") or {}
        users = engine.users_of(it["id"])
        who = ", ".join(sorted({engine.champ(u["tuong"])["ten"] for u in users}))
        st.markdown(f"<div class='dc-card hi'><div class='dc-row' style='gap:16px'>{ui.item_icon(it['id'], 64)}"
                    f"<div><div class='dc-big'>{ui.esc(it['ten'])}</div>"
                    f"<div style='color:var(--mute)'>{ui.esc(engine.item_name(a))} + {ui.esc(engine.item_name(b))}"
                    f"{' · ' + ui.esc(ex.get('danh_cho', '')) if ex.get('danh_cho') else ''}</div></div></div>"
                    f"<p style='margin:10px 0 4px'>{ui.esc(it.get('chi_so', ''))}</p>"
                    f"<p style='margin:0 0 6px'>{ui.esc(ex.get('tac_dung') or it.get('tac_dung', ''))}</p>"
                    + (f"<p style='margin:0'><b>Tướng nên cầm:</b> {ui.rich(', '.join(ex.get('tuong_nen_cam', [])))}</p>" if ex.get('tuong_nen_cam') else "")
                    + (f"<p style='margin:4px 0 0'><b>Đội hình meta dùng:</b> {ui.esc(who)}</p>" if who else "")
                    + "</div>", unsafe_allow_html=True)
        if users:
            st.markdown(ui.html_table(["Đội hình", "Hạng", "Tướng cầm", "Vai trò"],
                                      [[u["comp"]["ten"], u["comp"]["hang"], engine.champ(u["tuong"])["ten"], u["vai"]] for u in users],
                                      rich_text=True), unsafe_allow_html=True)

with tab6:
    st.caption("Bấm hình tướng → bộ đồ người chơi Bạch Kim+ hay lên nhất (MetaTFT) và đồ chuẩn trong file hướng dẫn.")
    st.session_state.setdefault("td_champ", "Azir")
    gtabs = st.tabs([f"{g} vàng" for g in range(1, 6)])
    for g, t in zip(range(1, 6), gtabs):
        with t:
            ui.pick_grid(f"tc{g}", [o for o in ui.champ_options() if engine.champ(o[0])["gia"] == g],
                         {st.session_state.td_champ}, pick_champ, per_row=8)
    cid = st.session_state.td_champ
    ch = engine.champ(cid)
    bi = P.best_items(cid)
    tr = "".join(ui.trait_chip(t) for t in ch.get("toc_he", []))
    html = (f"<div class='dc-card hi'><div class='dc-row' style='gap:14px'>{ui.champ_tile(cid, 64, name=False)}"
            f"<div><div class='dc-big'>{ui.esc(ch['ten'])}</div><div style='color:var(--mute);font-size:.85rem'>"
            f"{ch.get('gia', 1)} vàng · {ui.esc(ch.get('vi_tri', ''))} · tầm đánh {ch.get('tam_danh', '')}</div>"
            f"<div class='dc-row' style='margin-top:6px'>{tr}</div></div></div>")
    if bi and bi["do"]:
        html += (f"<p style='margin:12px 0 4px'><b>Đồ hay lên nhất (MetaTFT)</b> · hạng TB {bi['hang_tb']:.2f} · "
                 f"{bi['ti_le']:.1f}% ván có tướng này</p><div class='dc-row'>"
                 + "".join(ui.item_icon(i, 30, True) for i in bi["do"]) + "</div>")
    std = [(c, r) for c in engine.comps() for r in c["chu_luc"] + c["do_don"] if r["tuong"] == cid]
    for c, r in std:
        html += (f"<p style='margin:10px 0 4px'><b>{ui.esc(r['vai'])}</b> trong {ui.esc(c['ten'])} (file hướng dẫn)</p>"
                 f"<div class='dc-row'>" + "".join(ui.item_icon(i, 30, True) for i in r["do"]) + "</div>")
    if not (bi and bi["do"]) and not std:
        html += "<p style='margin:10px 0 0;color:var(--mute)'>Tướng này ít khi cầm đồ chính — đưa đồ cho chủ lực.</p>"
    st.markdown(html + "</div>", unsafe_allow_html=True)

with tab2:
    st.caption("Hàng × cột = món ghép ra. Di chuột (hoặc chạm) vào biểu tượng để xem tên.")
    table = engine.recipe_table()
    head = "<th></th>" + "".join(f"<th style='text-align:center'>{ui.item_icon(p, 26)}</th>" for p in comp_ids)
    body = ""
    for i, p in enumerate(comp_ids):
        cells = "".join(f"<td style='text-align:center'>{ui.item_icon(x, 30) if x else ''}</td>" for x in table[i])
        body += f"<tr><th>{ui.item_icon(p, 26)}</th>{cells}</tr>"
    st.markdown(f"<div style='overflow-x:auto'><table class='dc-table' style='width:auto'>{head}{body}</table></div>",
                unsafe_allow_html=True)
    with st.expander("Danh sách đầy đủ (chữ)"):
        rows = []
        for x in d["trang_bi"]["hoan_chinh"]:
            ex = x.get("excel") or engine.item(x["id"]).get("excel") or {}
            rows.append([x["ten"], " + ".join(engine.item_name(p) for p in x["cong_thuc"]), x["chi_so"],
                         ex.get("tac_dung") or x["tac_dung"], ", ".join(ex.get("tuong_nen_cam", []))])
        st.markdown(ui.html_table(["Trang bị", "Công thức", "Chỉ số", "Tác dụng", "Tướng nên cầm"], rows), unsafe_allow_html=True)

with tab3:
    p = st.selectbox("Mảnh đồ bạn có nhiều nhất", comp_ids[:8], format_func=engine.item_name, key="td_start")
    st.caption(engine.item(p).get("chi_so", ""))
    for x in engine.comps_for_component(p):
        c = x["comp"]
        st.markdown(f"<div class='dc-row' style='margin:6px 0'>{ui.tier_badge(c['hang'])}<div><b>{ui.esc(c['ten'])}</b>"
                    f"<br><span style='color:var(--mute);font-size:.85rem'>→ {ui.esc(', '.join(x['do']))}</span></div></div>",
                    unsafe_allow_html=True)
    st.markdown("### Đồ chuẩn của từng chủ lực")
    for c in engine.comps(("S", "A")):
        for r in c["chu_luc"]:
            st.markdown(f"<div class='dc-row' style='margin:4px 0'>{ui.champ_tile(r['tuong'], 36, name=False)}"
                        f"<div><b>{ui.esc(engine.champ(r['tuong'])['ten'])}</b> <span style='color:var(--mute)'>· {ui.esc(c['ten'])}</span>"
                        f"<br>{''.join(ui.item_icon(i, 24) for i in r['do'])} "
                        f"<span style='font-size:.85rem'>{ui.esc(', '.join(engine.item_name(i) for i in r['do']))}</span></div></div>",
                        unsafe_allow_html=True)

with tab4:
    an = d["hd_an"]["an"]
    st.caption("Ấn cho tướng thêm 1 tộc/hệ (và chỉ số riêng). Siêu Xẻng (Xẻng Vàng) ghép ra Ấn tộc, Chảo Vàng ghép ra Ấn hệ.")
    for e in an:
        iid = engine.item_id(e["ten"])
        icon = ui.item_icon(iid, 34) if iid else ""
        st.markdown(f"<div class='dc-card'><div class='dc-row' style='gap:12px'>{icon}<div><b>{ui.esc(e['ten'])}</b>"
                    f"<div style='color:var(--mute);font-size:.84rem'>{ui.esc(e['cong_thuc'])}</div></div></div>"
                    f"<p style='margin:8px 0 2px'>{ui.esc(e['hieu_ung'])}</p>"
                    f"<div style='font-size:.85rem;color:var(--mute)'>Đeo tốt nhất: {ui.rich(e['deo_tot_nhat'])} · hạng TB {ui.esc(e['hang_tb'])}</div></div>",
                    unsafe_allow_html=True)
    st.caption("Muốn biết Ấn đang có nên đi đội nào: Trợ lý ván đấu → thẻ “Ấn → đội hình”.")

with tab5:
    st.markdown("### Tạo Tác · đồ Ánh Sáng · đồ đặc biệt nổi bật")
    pics = d["anh_phu"]["tao_tac"]
    st.markdown(ui.html_table(["", "Tên", "Loại", "Tướng hợp nhất", "Ghi chú"],
                              [[ui.Raw(ui.img(pics.get(x["ten"], ""), 34)), x["ten"], x["loai"], x["tuong"], x["ghi_chu"]]
                               for x in kt["tao_tac"]], rich_text=True), unsafe_allow_html=True)
    st.markdown("### Nguyên tắc lên đồ của Thách Đấu")
    for i, x in enumerate(kt["nguyen_tac_do"], 1):
        st.markdown(f"{i}. {x}")

ui.source_note()
