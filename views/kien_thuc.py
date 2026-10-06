# ĐTCL Coach v1.1 (2026-10-06) — trang Kiến thức & tra cứu (tộc hệ, tướng, lộ trình Thách Đấu, từ điển, nguồn)
import streamlit as st

from core import engine, ui

d = engine.data()
kt = d["hd_kien_thuc"]
ui.header("Kiến thức & tra cứu",
          "Tộc hệ và 65 tướng, 10 nguyên tắc vàng, 20 thói quen Thách Đấu, kế hoạch leo hạng, từ điển thuật ngữ, nguồn dữ liệu.")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Tộc hệ & tướng", "Nguyên tắc vàng", "Lộ trình Thách Đấu", "Từ điển", "Nguồn & phiên bản"])

with tab1:
    c1, c2 = st.columns([1.2, 1])
    q = c1.text_input("Tìm tướng hoặc tộc/hệ", key="kt_q", placeholder="Ví dụ: Azir, Thần Rừng…")
    loai = c2.selectbox("Loại", ["Tất cả", "Tộc", "Hệ", "Độc nhất", "Đặc biệt"], key="kt_loai")
    for t in d["toc_he"]:
        if loai != "Tất cả" and t["loai"] != loai:
            continue
        members = [engine.champ(u)["ten"] for u in t["tuong"]]
        if q and engine.norm(q) not in engine.norm(t["ten"] + " " + " ".join(members)):
            continue
        ex = t.get("excel") or {}
        moc = " / ".join(str(m) for m in t["moc"] if m)
        st.markdown(f"<div class='dc-card'><div class='dc-row' style='gap:10px'><img class='dc-ico' style='--s:34px' src='{t['anh']}' alt=''>"
                    f"<div><b>{ui.esc(t['ten'])}</b> <span style='color:var(--mute)'>· {ui.esc(ex.get('loai') or t['loai'])} · mốc {ui.esc(moc)}</span></div></div>"
                    f"<p style='margin:8px 0'>{ui.esc(ex.get('hieu_ung') or t['mo_ta'])}</p>"
                    f"{ui.champ_row(t['tuong'], 44)}</div>", unsafe_allow_html=True)
    with st.expander("Bảng 65 tướng — giá, tộc hệ, đội hình dùng"):
        rows = []
        for u in sorted(kt["tuong"], key=lambda x: (x["gia"], x["ten"])):
            if q and engine.norm(q) not in engine.norm(u["ten"] + " " + " ".join(u["toc_he"])):
                continue
            rows.append([u["ten"], u["gia"], ", ".join(u["toc_he"]), ", ".join(u["doi_hinh"])])
        st.markdown(ui.html_table(["Tướng", "Giá", "Tộc / Hệ", "Đội hình dùng"], rows, rich_text=True), unsafe_allow_html=True)

with tab2:
    for i, x in enumerate(kt["nguyen_tac_vang"], 1):
        st.markdown(f"**{i}.** {x}")
    st.markdown("### Có gì mới · bản 18.4 (07/10/2026)")
    st.caption("Xem đầy đủ có hình ở trang “Phân tích bản cập nhật”.")
    for x in kt["ban_moi"]:
        st.markdown(f"<div style='margin:4px 0'><b>{ui.esc(x['k'])}</b> — {ui.rich(x['v'])}</div>", unsafe_allow_html=True)
    st.markdown("### Xếp bàn")
    for x in d["meo"]["xep_ban"]:
        st.markdown(f"- **{x['tieu_de']}.** {x['noi_dung']}")

with tab3:
    st.markdown("### 20 thói quen của người chơi Thách Đấu")
    st.caption("Tích những thói quen bạn đã làm được (lưu trong phiên này).")
    done = 0
    for i, h in enumerate(kt["thoi_quen"]):
        if st.checkbox(f"{h['nhom']} — {h['thoi_quen']}", key=f"tq_{i}"):
            done += 1
    st.progress(done / max(1, len(kt["thoi_quen"])), text=f"{done} / {len(kt['thoi_quen'])} thói quen")
    st.markdown("### Lỗi thường gặp → cách sửa")
    st.markdown(ui.html_table(["Lỗi", "Cách sửa"], [[x["loi"], x["sua"]] for x in kt["loi_thuong_gap"]]), unsafe_allow_html=True)
    st.markdown("### Kế hoạch leo hạng theo từng mức")
    st.markdown(ui.html_table(["Mức rank", "Trọng tâm luyện", "Chỉ số mục tiêu"],
                              [[x["muc"], x["trong_tam"], x["chi_so"]] for x in kt["ke_hoach_rank"]]), unsafe_allow_html=True)

with tab4:
    st.markdown(ui.html_table(["Trong web gọi là", "Trên mạng hay gọi là", "Nghĩa là"],
                              [[x["ten"], x["tieng_anh"], x["nghia"]] for x in kt["tu_dien"]]), unsafe_allow_html=True)
    st.markdown("### Chỉ số trong trò chơi")
    st.markdown(ui.html_table(["Chỉ số", "Nghĩa"], [[x["ten"], x["nghia"]] for x in kt["chi_so"]]), unsafe_allow_html=True)

with tab5:
    m = d["meta"]
    st.markdown(f"- **Mùa / bản:** Mùa {m['mua']} · {m['ten_mua_vi']} · bản {m['phien_ban']} (dữ liệu lấy {m['ngay_cap_nhat']})")
    for x in kt["phien_ban"]:
        st.markdown(f"- **{x['k']}:** {x['v']}")
    st.markdown("### Nguồn dữ liệu của web")
    for s in m["nguon"]:
        st.markdown(f"- [{s['ten']}]({s['url']})")
    st.caption(m["ghi_chu"])
    st.markdown("### Nguồn của file Excel hướng dẫn v1.8")
    for s in kt["nguon"]:
        st.markdown(f"- [{s['ten']}]({s['url']})")
    st.markdown("### Lịch sử file Excel")
    for x in kt["nhat_ky_excel"]:
        st.markdown(f"- **{x['k']}** — {x['v']}")
    ui.note("Hướng dẫn giúp vào top đều hơn, không đảm bảo top 1 mọi ván. Không liên kết chính thức với Riot Games.")

ui.source_note()
