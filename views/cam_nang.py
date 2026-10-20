# ĐTCL Coach v1.3 (2026-10-20) — trang Cẩm nang Thách Đấu: top đội hình, tempo, lõi top 1, cặp lõi, bùa theo giai đoạn
import streamlit as st

from core import cam_nang as C
from core import engine, ui

d = engine.data()
m = d["meta"]
cn = d.get("cam_nang") or {}
bo = m.get("bo", m["phien_ban"])

ui.header(f"Cẩm nang Thách Đấu · bản {bo}",
          "Đội hình nên chơi theo số liệu thật máy chủ VN, cách đánh tempo như người chơi Thách Đấu, cách xử lý lõi top 1, "
          "các cặp lõi mạnh và bùa (Tinh Linh) nên mua theo từng giai đoạn.")
if not d.get("vn_opgg"):
    st.warning(f"Bộ dữ liệu {bo} không có bảng OP.GG có cấu trúc — chọn bản 18.4b ở thanh bên để xem đầy đủ.")
if cn and cn.get("phien_ban") != bo:
    ui.note(f"Phần tempo / lõi / bùa viết cho bản {cn['phien_ban']}; số liệu đội hình là của bản {bo}.")

tab1, tab2, tab3, tab4 = st.tabs(["Top đội hình", "Đánh tempo như Thách Đấu", "Lõi top 1 & cặp lõi", "Bùa theo giai đoạn"])


def comp_card(i: int, r: dict, extra: str = "") -> str:
    carries = {x["tuong"]: x["do"] for x in r.get("chinh", [])}
    tags = {x["tuong"]: "3★" for x in r.get("chinh", []) if x.get("sao3")}
    stats = [("Hạng TB VN", f"{r['hang_tb']:.2f}"), ("Top 4", f"{r['top4']:.1f}%"), ("Top 1", f"{r['top1']:.1f}%"),
             ("Người chơi", f"{r['ti_le']:.2f}%"), ("Độ khó", r["do_kho_ten"])]
    mt = r.get("metatft")
    if mt:
        stats.append(("Hạng TB quốc tế", f"{mt['so_lieu']['hang_tb']:.2f}"))
    cond = "".join(f"<li>{ui.rich(x)}</li>" for x in r.get("dieu_kien", []))
    return (f"<div class='dc-card{' hi' if i == 0 else ''}'><div class='dc-row' style='gap:10px'>"
            f"<span class='dc-tier' style='--t:{ui.TIER_COLOR.get(r['bac'], '#E8C06A')}'>{ui.esc(r['bac'])}</span>"
            f"<div style='flex:1'><b>{i + 1}. {ui.esc(r['ten'])}</b>{extra}</div></div>"
            f"<div style='margin:8px 0'>{ui.champ_row(r['tuong'], 42, carries, tags=tags)}</div>"
            f"<div class='dc-stat'>" + "".join(f"<div>{ui.esc(k)}<b>{ui.esc(v)}</b></div>" for k, v in stats) + "</div>"
            + (f"<ul class='dc-why'>{cond}</ul>" if cond else "") + "</div>")


with tab1:
    vn_src = (d.get("vn_opgg") or {}).get("nguon", m.get("vn_nguon", ""))
    st.markdown("### Top đội hình mạnh nhất (đủ người chơi)")
    st.caption(f"Hạng TB thấp nhất trong các đội có ≥ 0,3% người chơi — số liệu đủ lớn để tin. Nguồn: {vn_src}.")
    rows = C.top_manh()
    cols = st.columns(2)
    for i, r in enumerate(rows):
        cols[i % 2].markdown(comp_card(i, r), unsafe_allow_html=True)

    st.markdown("### Mạnh mà ít người chơi — ít bị tranh tướng")
    st.caption("Hạng TB ≤ 3,6 nhưng dưới 0,3% người chơi VN. Ít người chơi = dễ có tướng, nhưng cỡ mẫu nhỏ nên số dao động — "
               "đối chiếu thêm cột hạng TB quốc tế.")
    rows = C.manh_it_nguoi()
    cols = st.columns(2)
    for i, r in enumerate(rows):
        cols[i % 2].markdown(comp_card(i, r), unsafe_allow_html=True)
    qt = C.manh_it_nguoi_quoc_te()
    if qt:
        st.markdown("**Quốc tế (MetaTFT) — mạnh mà ít trận**")
        st.markdown(ui.html_table(["Đội (cụm MetaTFT)", "Lối chơi", "Hạng TB", "Top 4", "Top 1", "Số trận 3 ngày", "Chủ lực"],
                                  [[c["ten"], c["kieu_ten"], c["so_lieu"]["hang_tb"], f"{c['so_lieu']['top4']}%",
                                    f"{c['so_lieu']['top1']}%", f"{c['so_lieu']['so_tran']:,}".replace(",", "."),
                                    ", ".join(engine.champ(x["tuong"])["ten"] for x in c["chu_luc"])] for c in qt],
                                  rich_text=True), unsafe_allow_html=True)

    st.markdown("### Dễ vào top, ít điều kiện")
    st.caption("Xếp theo: top 4 VN − độ khó (OP.GG: dễ 0 · vừa −5 · khó −12) − cần Ấn (−3) − cần lên cấp 9 (−4). "
               "Ưu tiên đội không phụ thuộc lõi/Ấn, chỉ cần đúng tướng và đồ thường.")
    rows = C.de_vao_top()
    cols = st.columns(2)
    for i, r in enumerate(rows):
        cols[i % 2].markdown(comp_card(i, r, f" <span style='color:var(--mute);font-size:.82rem'>· điểm dễ {r['diem_de']}</span>"),
                             unsafe_allow_html=True)
    st.caption("Bấm từng đội ở trang “Đội hình meta” để xem lộ trình, form theo vòng, vị trí đứng.")

with tab2:
    tp = cn.get("tempo")
    if not tp:
        st.info("Chưa có phần tempo cho bộ dữ liệu này — chọn bản 18.4b.")
    else:
        ui.note(tp["gioi_thieu"])
        st.markdown("### Mốc lên cấp của đội meta (trung vị, số liệu thật)")
        moc = C.moc_len_cap()
        st.markdown(ui.html_table(["Lối chơi", "Số đội"] + [f"Cấp {lv}" for lv in range(4, 11)],
                                  [[x["loi_choi"], x["so_doi"]] + [x["cap"].get(lv, "—") for lv in range(4, 11)] for x in moc]),
                    unsafe_allow_html=True)
        st.caption(f"Vòng mà người chơi Bạch Kim+ lên từng cấp, lấy trung vị các cụm đội MetaTFT bản {m['phien_ban']}. "
                   "Đội đang chuỗi thắng thường đi sớm hơn 1 vòng.")
        st.markdown("### 10 nguyên tắc tempo")
        for x in tp["nguyen_tac"]:
            st.markdown(f"<div class='dc-card'><b style='color:var(--gold)'>{ui.esc(x['k'])}</b><div>{ui.rich(x['v'])}</div></div>",
                        unsafe_allow_html=True)
        st.markdown("### Việc cần làm theo từng vòng")
        st.markdown(ui.html_table(["Vòng", "Việc"], [[x["vong"], x["viec"]] for x in tp["lich"]], rich_text=True),
                    unsafe_allow_html=True)
        st.markdown("### Lỗi hay gặp")
        for x in tp["loi_thuong_gap"]:
            st.markdown(f"- {x}")

with tab3:
    if not cn.get("loi_top1"):
        st.info("Chưa có phần lõi cho bộ dữ liệu này — chọn bản 18.4b.")
    else:
        ui.note(cn["ghi_chu_loi"])
        st.markdown("### Lõi top 1 — cách xử lý")
        for x in cn["loi_top1"]:
            a = d["aug"].get(x["id"])
            if not a:
                continue
            steps = "".join(f"<li>{ui.rich(s)}</li>" for s in x["cach"])
            st.markdown(
                f"<div class='dc-card'><div class='dc-row' style='gap:12px'>{ui.aug_icon(x['id'], 44)}<div style='flex:1'>"
                f"<b>{ui.esc(a['ten'])}</b> <span style='color:var(--mute);font-size:.82rem'>· {ui.esc(a['ten_en'])} · "
                f"{ui.esc(a['bac'])} · bậc {ui.esc(a['xep_hang'])} · nhận ở {ui.esc(x['khi_nao'])}</span>"
                f"<div style='font-size:.85rem;color:var(--mute)'>{ui.esc(a['mo_ta'])}</div></div></div>"
                f"<p style='margin:8px 0 4px'><b style='color:var(--gold)'>Vì sao mạnh.</b> {ui.rich(x['vi_sao'])}</p>"
                f"<ul class='dc-why'>{steps}</ul>"
                f"<p style='margin:4px 0;font-size:.88rem'><b>Tránh:</b> {ui.rich(x['tranh'])}</p></div>",
                unsafe_allow_html=True)
        st.markdown("### Cặp lõi mạnh")
        st.caption("Nhận định theo cơ chế lõi (không có số liệu cặp lõi công khai cho bản này).")
        for x in cn["cap_loi"]:
            names = [d["aug"][i]["ten"] for i in x["loi"] if i in d["aug"]]
            icons = "".join(ui.aug_icon(i, 36) for i in x["loi"] if i in d["aug"])
            st.markdown(f"<div class='dc-card'><div class='dc-row' style='gap:10px'>{icons}<b>{ui.esc(' + '.join(names))}</b></div>"
                        f"<p style='margin:6px 0 2px'>{ui.rich(x['vi_sao'])}</p>"
                        f"<div style='font-size:.86rem;color:var(--mute)'>Đội hợp: {ui.rich(x['doi'])}</div></div>",
                        unsafe_allow_html=True)
        with st.expander("Bảng xếp hạng lõi đầy đủ (chuyên gia MetaTFT)"):
            hang = st.selectbox("Bậc", ["S", "A", "B", "C"], key="cn_hang")
            st.markdown(ui.html_table(["", "Lõi", "Bậc lõi", "Vòng", "Mô tả"],
                                      [[ui.Raw(ui.aug_icon(a["id"], 28)), a["ten"], a["bac"], ", ".join(a["vong"]), a["mo_ta"]]
                                       for a in d["loi"] if a["xep_hang"] == hang], rich_text=True), unsafe_allow_html=True)

with tab4:
    tl = cn.get("tinh_linh")
    if not tl:
        st.info("Chưa có bảng bùa cho bộ dữ liệu này — chọn bản 18.4b.")
    else:
        ui.note(cn["ghi_chu_tinh_linh"])
        giai_doan = {"Giai đoạn 2 (2-1 → 2-7)": (2, 2), "Giai đoạn 3 (3-1 → 3-7)": (3, 3), "Giai đoạn 4 (4-1 → 4-7)": (4, 4),
                     "Giai đoạn 5 trở đi": (5, 10)}
        nhom = ["Tất cả"] + sorted({x["nhom"] for x in tl})
        c1, c2 = st.columns([2, 1])
        gd = c1.radio("Giai đoạn", list(giai_doan), horizontal=True, key="cn_gd")
        nh = c2.selectbox("Loại", nhom, key="cn_nhom")
        lo, hi = giai_doan[gd]

        def stage(s: str) -> int:
            return int(s.split("-")[0])

        rows = [x for x in tl if stage(x["tu"]) <= hi and stage(x["den"]) >= lo and (nh == "Tất cả" or x["nhom"] == nh)]
        rows.sort(key=lambda x: (x["hang"], x["nhom"], x["ten"]))
        st.markdown(ui.html_table(["Bậc", "Bùa (Tinh Linh)", "Loại", "Giá", "Xuất hiện", "Tác dụng"],
                                  [[x["hang"], x["ten"] + (" *" if x["tam_dich"] else "") + f" ({x['ten_en']})", x["nhom"],
                                    "—" if x["gia"] is None else f"{x['gia']} vàng", f"{x['tu']} → {x['den']}", x["mo_ta"]]
                                   for x in rows], rich_text=True), unsafe_allow_html=True)
        st.caption("Gợi ý: giai đoạn 2 mua bùa ra tướng 2 sao / XP / vàng; giai đoạn 3 bùa trang bị và tướng 3 vàng 2 sao; "
                   "giai đoạn 4–5 bùa giao tranh khi cần thắng trận quyết định (Dư Chấn, Động Đất, Lá Chắn, Baron Chi Viện).")

links = " · ".join(f"<a href='{ui.esc(s['url'])}' target='_blank'>{ui.esc(s['ten'])}</a>" for s in cn.get("nguon", []))
st.markdown(f"<div class='dc-src'>Nguồn: {links or ui.esc(m.get('vn_nguon', ''))}. Cẩm nang giúp vào top đều hơn, "
            f"không đảm bảo top 1 mọi ván.</div>", unsafe_allow_html=True)
