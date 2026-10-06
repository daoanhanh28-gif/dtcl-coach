# ĐTCL Coach v1.0 (2026-10-06) — trang Đội hình meta (Excel v1.8 + số liệu VN/Trung/Hàn + MetaTFT)
import pandas as pd
import streamlit as st

from core import engine, ui

d = engine.data()
kt = d["hd_kien_thuc"]
ui.header("Đội hình meta",
          "19 đội hình xếp hạng S/A/B/C theo file hướng dẫn v1.8, kèm số liệu máy chủ Việt Nam. "
          "Bấm vào từng đội để xem lộ trình, lên đồ, lõi và sơ đồ xếp vị trí.")

with st.expander("Bản 18.4 (07/10/2026) thay đổi gì?", expanded=False):
    for x in kt["ban_moi"]:
        st.markdown(f"- **{x['k']}** — {x['v']}")

tab1, tab2, tab3 = st.tabs(["Xếp hạng đội hình", "Máy chủ VN · Trung · Hàn", "Thống kê MetaTFT"])

with tab1:
    c1, c2 = st.columns([1, 1.4])
    with c1:
        tiers = st.multiselect("Hạng", ["S", "A", "B", "C"], default=["S", "A", "B", "C"], key="dh_tier")
    with c2:
        styles = sorted({c["kieu_ten"] for c in engine.comps()})
        style = st.selectbox("Lối chơi", ["Tất cả"] + styles, key="dh_style")
    shown = [c for c in engine.comps(tuple(tiers)) if style == "Tất cả" or c["kieu_ten"] == style]
    if not shown:
        st.info("Không có đội nào khớp bộ lọc — bỏ bớt điều kiện lọc.")
    for c in shown:
        ui.comp_card(c, highlight=c["hang"] == "S")
    st.caption("Hạng có thể tăng 1–2 bậc khi có lõi / Ấn / Tạo Tác phù hợp. Mỗi phiên bản (~2 tuần) đội mạnh sẽ thay đổi.")

with tab2:
    mc = kt["may_chu"]
    st.markdown("### Máy chủ Việt Nam")
    st.caption(mc["vn"]["tieu_de"])
    st.markdown(ui.html_table(mc["vn"]["cot"], mc["vn"]["dong"]), unsafe_allow_html=True)
    ui.note(mc["vn"]["goi_y"])
    st.markdown("### So sánh Việt Nam – Hàn – Trung")
    st.markdown(ui.html_table(["Đội hình", "Việt Nam", "Hàn / quốc tế", "Trung Quốc", "Ý nghĩa cho bạn"],
                              [[x["doi_hinh"], x["vn"], x["han"], x["trung"], x["y_nghia"].lstrip("→ ")] for x in mc["so_sanh"]]),
                unsafe_allow_html=True)
    st.caption("Số trước là hạng trung bình (càng thấp càng tốt), số trong ngoặc là tỉ lệ người chơi (càng cao càng dễ bị tranh tướng).")
    cA, cB = st.columns(2)
    with cA:
        st.markdown("### Hàn / quốc tế (OP.GG)")
        st.markdown(ui.html_table(mc["han"]["cot"], mc["han"]["dong"]), unsafe_allow_html=True)
    with cB:
        st.markdown("### Trung Quốc (TopMeta)")
        st.markdown(ui.html_table(mc["trung"]["cot"], mc["trung"]["dong"]), unsafe_allow_html=True)
    st.caption(mc["ghi_chu"])
    st.markdown("### Cách build từng bước")
    for b in mc["cach_build"]:
        with st.expander(f"{b['ten']} — {b['so_lieu']}"):
            for s in b["buoc"]:
                st.markdown(f"- **{s['k']}** {s['v']}")

with tab3:
    st.caption("Thống kê MetaTFT: Bạch Kim trở lên, 3 ngày gần nhất, bản 18.3b (lấy ngày 06/10/2026). "
               "Đây là số quốc tế — dùng để so xu hướng, bảng máy chủ VN sát với phòng bạn đánh hơn.")
    rows = []
    for c in d["metatft_doi_hinh"]:
        sl = c["so_lieu"]
        rows.append({"Hạng": c["hang"], "Đội (cụm MetaTFT)": c["ten"], "Lối chơi": c["kieu_ten"],
                     "Hạng TB": sl["hang_tb"], "Top 4 %": sl["top4"], "Top 1 %": sl["top1"], "Số trận": sl["so_tran"],
                     "Chủ lực": ", ".join(engine.champ(x["tuong"])["ten"] for x in c["chu_luc"])})
    df = pd.DataFrame(rows)
    st.dataframe(df, hide_index=True, use_container_width=True,
                 column_config={"Số trận": st.column_config.NumberColumn(format="%d")})

ui.source_note()
