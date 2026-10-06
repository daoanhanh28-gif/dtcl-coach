# ĐTCL Coach v1.1 (2026-10-06) — trang Lõi nâng cấp
import streamlit as st

from core import engine, ui

d = engine.data()
hl = d["hd_loi"]
ui.header("Lõi nâng cấp",
          "Tra lõi theo bậc Bạc / Vàng / Kim Cương, lọc theo đội hình. Xếp hạng lấy từ MetaTFT, "
          "ghi chú và lõi ăn top 1 lấy từ file hướng dẫn v1.8.")



def _aug_pic(text: str) -> str:
    ids = engine.aug_ids_from_text(text)
    return ui.aug_icon(ids[0], 32) if ids else ""


def _trait_pic(text: str) -> str:
    for part in str(text).replace("/", ",").split(","):
        tid = d["trait_by_name"].get(engine.norm(part))
        if tid:
            return ui.trait_icon(tid, 30)
    return ""


tab1, tab2, tab3, tab4 = st.tabs(["Tra lõi", "Lõi ăn top 1", "Quy tắc theo mốc", "Lõi tộc hệ"])

with tab1:
    c1, c2, c3, c4 = st.columns([1, 1, 1.4, 1.2])
    bac = c1.selectbox("Bậc", ["Tất cả", "Bạc", "Vàng", "Kim cương"], key="l_bac")
    hang = c2.selectbox("Xếp hạng", ["Tất cả", "S", "A", "B", "C"], key="l_hang")
    comp_names = ["Tất cả"] + [c["ten"] for c in engine.comps()]
    comp_sel = c3.selectbox("Hợp đội hình", comp_names, key="l_comp")
    nhom = c4.selectbox("Nhóm", ["Tất cả"] + sorted({a["nhom"] for a in d["loi"]}), key="l_nhom")
    q = st.text_input("Tìm theo tên", key="l_q", placeholder="Ví dụ: Thợ Rèn, Phân Nhánh…")
    comp = engine.comp_by_name(comp_sel) if comp_sel != "Tất cả" else None
    pool = d["loi"]
    if comp:
        order = {a: i for i, a in enumerate(comp["loi_hop"])}
        pool = sorted([a for a in pool if a["id"] in order], key=lambda a: order[a["id"]])
    res = [a for a in pool
           if (bac == "Tất cả" or a["bac"] == bac) and (hang == "Tất cả" or a["xep_hang"] == hang)
           and (nhom == "Tất cả" or a["nhom"] == nhom) and (not q or engine.norm(q) in engine.norm(a["ten"] + " " + a["ten_en"]))]
    st.caption(f"{len(res)} lõi")
    if comp and not res:
        st.info("Excel chưa ghi lõi nào khớp tên trong dữ liệu game cho đội này — xem phần “Lõi khuyên dùng” trong thẻ đội hình.")
    for a in res[:120]:
        note = engine.aug_note(a["id"])
        img = f"<img class='dc-ico' style='--s:42px' src='{a['anh']}' alt=''>" if a.get("anh") else ui.tier_badge(a["xep_hang"])
        extra = ""
        if note:
            bits = [note.get("hang_excel") and f"Excel: {note['hang_excel']}", note.get("hop_voi") and f"hợp {note['hop_voi']}",
                    note.get("ghi_chu"), note.get("uu_tien") and f"{note['uu_tien']} → {note.get('doi_hinh_ep', '')}"]
            extra = "<div style='font-size:.82rem;color:var(--gold);margin-top:4px'>" + ui.esc(" · ".join(b for b in bits if b)) + "</div>"
        vong = ", ".join(a["vong"]) or "—"
        st.markdown(f"<div class='dc-card'><div class='dc-row' style='gap:12px;align-items:flex-start'>{img}"
                    f"<div style='flex:1'><div><b>{ui.esc(a['ten'])}</b> <span style='color:var(--mute)'>· {ui.esc(a['ten_en'])}</span></div>"
                    f"<div style='font-size:.82rem;color:var(--mute)'>{ui.esc(a['bac'])} · hạng {ui.esc(a['xep_hang'])} · "
                    f"{ui.esc(a['nhom'])} · hay gặp ở {ui.esc(vong)}</div>"
                    f"<div style='font-size:.9rem;margin-top:4px'>{ui.esc(a['mo_ta'])}</div>{extra}</div>"
                    f"{ui.tier_badge(a['xep_hang'])}</div></div>", unsafe_allow_html=True)
    if len(res) > 120:
        st.caption("Đang hiện 120 lõi đầu — lọc thêm để thu hẹp.")

with tab2:
    st.markdown("### Nguyên tắc chọn lõi để ăn top")
    for x in hl["top1_nguyen_tac"]:
        st.markdown(f"- **{x['tieu_de']}.** {x['noi_dung']}")
    st.markdown("### Lõi quyết định ván đấu")
    pri = st.selectbox("Lọc mức ưu tiên", ["Tất cả"] + sorted({x["uu_tien"] for x in hl["top1"]}), key="l_top1")
    for x in hl["top1"]:
        if pri != "Tất cả" and x["uu_tien"] != pri:
            continue
        ids = engine.aug_ids_from_text(x["ten"])
        chips = "".join(ui.aug_chip(a) for a in ids)
        st.markdown(f"<div class='dc-card'><div style='font-weight:700'>{ui.esc(x['ten'])}</div>"
                    f"<div style='color:var(--gold);font-size:.85rem'>{ui.esc(x['uu_tien'])} · hay gặp ở {ui.esc(x['vong'])} · "
                    f"ép: {ui.rich(x['doi_hinh'])}</div><p style='margin:6px 0'>{ui.rich(x['lam_gi'])}</p>"
                    f"<div style='color:var(--mute);font-size:.85rem'>Kỳ vọng: {ui.esc(x['ky_vong'])}</div>"
                    f"<div class='dc-row' style='margin-top:6px'>{chips}</div></div>", unsafe_allow_html=True)
    st.caption(hl["ghi_chu_top1"])

with tab3:
    st.markdown("### Quy tắc chọn lõi theo mốc")
    for x in hl["quy_tac_moc"]:
        st.markdown(f"- **{x['moc']}** — {x['quy_tac']}")
    st.markdown("### Danh sách lõi mạnh (bản 18.3b)")
    loai = st.selectbox("Loại", ["Tất cả"] + sorted({x["loai"] for x in hl["loi_manh"]}), key="l_manh")
    st.markdown(ui.html_table(["", "Lõi", "Loại", "Hạng", "Hợp với", "Ghi chú"],
                              [[ui.Raw(_aug_pic(x["ten"])), x["ten"], x["loai"], x["hang"], x["hop_voi"], x["ghi_chu"]]
                               for x in hl["loi_manh"] if loai == "Tất cả" or x["loai"] == loai], rich_text=True),
                unsafe_allow_html=True)

with tab4:
    st.markdown("### Xếp hạng lõi tộc hệ — bản 18.3b + thay đổi 18.4")
    st.markdown(ui.html_table(["", "Lõi", "Tộc/Hệ", "Sức mạnh", "Cho bạn", "Đội hình hợp", "Cách đánh", "Bản 18.4"],
                              [[ui.Raw(_aug_pic(x["ten"]) or _trait_pic(x["toc_he"])), x["ten"], x["toc_he"], x["suc_manh"],
                                x["cho"], x["doi_hinh"], x["cach_danh"], x["ban_moi"]]
                               for x in hl["loi_toc_he"]], rich_text=True), unsafe_allow_html=True)
    st.caption("Muốn biết lõi vừa nhận nên đánh thế nào: mở Trợ lý ván đấu → thẻ “Lõi → cách đánh”.")

ui.source_note()
