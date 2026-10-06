# ĐTCL Coach v1.1 (2026-10-06) — trang Kinh tế & nhịp ván
import streamlit as st

from core import engine, ui

d = engine.data()
k = d["kinh_te"]
kt = d["hd_kien_thuc"]
ui.header("Kinh tế & nhịp ván",
          "Mốc lãi 10/20/30/40/50, chuỗi thắng / thua, mốc lên cấp theo vòng, khi nào dồn vàng đổi tướng, tỉ lệ ra tướng.")

tab1, tab2, tab3, tab4 = st.tabs(["Tính vàng", "Lên cấp & tỉ lệ ra tướng", "Vòng đấu & Tinh Linh", "Khi nào dồn vàng"])

with tab1:
    st.session_state.setdefault("kt_gold", 34)
    st.session_state.setdefault("kt_streak", 3)
    c1, c2, c3 = st.columns(3)
    c1.number_input("Vàng cuối vòng", min_value=0, max_value=200, step=1, key="kt_gold")
    c2.number_input("Chuỗi (+thắng / −thua)", min_value=-15, max_value=15, step=1, key="kt_streak")
    won = c3.toggle("Thắng trận này", value=True, key="kt_won")
    g = int(st.session_state.kt_gold)
    inc = engine.income(g, int(st.session_state.kt_streak), won)
    st.markdown(f"<div class='dc-card hi'><div class='dc-big'>+{inc['tong']} vàng vòng tới</div>"
                f"<div class='dc-stat'><div>Cơ bản<b>{inc['co_ban']}</b></div><div>Lãi<b>{inc['lai']}</b></div>"
                f"<div>Chuỗi<b>{inc['chuoi']}</b></div><div>Thắng<b>{inc['thang']}</b></div></div></div>",
                unsafe_allow_html=True)
    nxt = 50 if g >= 50 else (g // 10 + 1) * 10
    st.markdown(f"- Lãi hiện tại **{engine.interest(g)}** vàng. "
                + ("Đã đạt lãi tối đa — chỉ tiêu phần trên 50." if g >= 50 else f"Thêm **{nxt - g}** vàng để lên mốc {nxt}."))
    st.markdown(f"- {k['lai']['giai_thich']}")
    st.markdown("- Chuỗi: " + " · ".join(f"{r['tu']}–{r['den'] if r['den'] < 99 else '…'} trận: +{r['vang']}" for r in k["chuoi"] if r["vang"]))
    for x in kt["kinh_te"]:
        st.markdown(f"- **{x['k']}:** {x['v']}")

with tab2:
    st.markdown("### Tỉ lệ ra tướng theo cấp (%)")
    rows = [[lv] + k["ti_le_cua_hang"][str(lv)] for lv in range(1, 11)]
    st.markdown(ui.html_table(["Cấp", "1 vàng", "2 vàng", "3 vàng", "4 vàng", "5 vàng"], rows), unsafe_allow_html=True)
    st.caption(f"Số bản mỗi tướng: " + " · ".join(f"{c} vàng: {n}" for c, n in k["so_ban_moi_tuong"].items())
               + ". " + k["ghi_chu"])
    st.markdown("### Kinh nghiệm cần để lên cấp")
    st.markdown(ui.html_table(["Lên cấp"] + [str(i) for i in range(3, 11)],
                              [["Kinh nghiệm"] + [k["xp_len_cap"][str(i)] for i in range(3, 11)],
                               ["Vàng (4 vàng / 4 KN)"] + [engine.gold_to_level(i - 1) for i in range(3, 11)]]),
                unsafe_allow_html=True)
    st.markdown("### Lộ trình lên cấp chuẩn")
    for x in kt["lo_trinh_cap"]:
        st.markdown(f"- **{x['k']}:** {x['v']}")
    st.markdown("### Máy tính đổi tướng (ước tính)")
    st.session_state.setdefault("kt_lv", 8)
    st.session_state.setdefault("kt_cost", 4)
    st.session_state.setdefault("kt_left", 7)
    c1, c2, c3 = st.columns(3)
    c1.number_input("Cấp hiện tại", min_value=1, max_value=10, step=1, key="kt_lv")
    c2.number_input("Giá tướng cần tìm", min_value=1, max_value=5, step=1, key="kt_cost")
    c3.number_input("Số bản tướng còn lại trong bể", min_value=0, max_value=30, step=1, key="kt_left")
    est = engine.roll_estimate(int(st.session_state.kt_lv), int(st.session_state.kt_cost), int(st.session_state.kt_left))
    if est["ti_le_luot"] <= 0:
        st.warning("Ở cấp này không ra tướng giá đó — lên cấp trước.")
    else:
        st.markdown(f"<div class='dc-card'><div class='dc-stat'>"
                    f"<div>1 ô ra đúng tướng<b>{est['ti_le_o'] * 100:.1f}%</b></div>"
                    f"<div>Mỗi lượt đổi thấy ≥1 bản<b>{est['ti_le_luot'] * 100:.1f}%</b></div>"
                    f"<div>Số lượt trung bình<b>{est['so_luot']:.1f}</b></div>"
                    f"<div>≈ Vàng cần<b>{est['vang']:.0f}</b></div></div></div>", unsafe_allow_html=True)
        st.caption("Công thức: tỉ lệ theo cấp × (bản còn lại ÷ (số bản mỗi tướng × số tướng cùng giá)). Giả định tướng khác cùng giá còn đủ bản. "
                   "Số lượt quá lớn → lên cấp hoặc đổi hướng đội hình.")

with tab3:
    st.markdown("### Làm gì ở mỗi vòng")
    st.markdown(ui.html_table(["Vòng", "Sự kiện", "Việc cần làm"], [[x["vong"], x["su_kien"], x["viec"]] for x in kt["vong_dau"]], rich_text=True),
                unsafe_allow_html=True)
    st.markdown("### Tinh Linh")
    for x in kt["tinh_linh"]["quy_tac"]:
        st.markdown(f"- {x}")
    loai = st.selectbox("Lọc loại Tinh Linh", ["Tất cả"] + sorted({x["loai"] for x in kt["tinh_linh"]["danh_sach"]}), key="kt_tl")
    tl_pic = ui.Raw(ui.img(d["anh_phu"]["tinh_linh"], 26))
    st.markdown(ui.html_table(["", "Tinh Linh", "Loại", "Giá (vàng)", "Hiệu ứng", "Khi nào mua"],
                              [[tl_pic, x["ten"], x["loai"], x["gia"], x["hieu_ung"], x["khi_nao"]] for x in kt["tinh_linh"]["danh_sach"]
                               if loai == "Tất cả" or x["loai"] == loai]), unsafe_allow_html=True)

with tab4:
    for x in k["all_in"]:
        st.markdown(f"- {x}")
    st.markdown("### Mẹo kinh tế")
    for x in k["meo"]:
        st.markdown(f"- {x}")
    st.markdown("### Lộ trình theo lối chơi (Excel)")
    nh = d["hd_nhip"]
    style = st.selectbox("Lối chơi", [s["ten"] for s in nh["loi_choi"]], key="kt_style")
    s = next(x for x in nh["loi_choi"] if x["ten"] == style)
    st.markdown(ui.html_table(["Vòng", "Cấp", "Vàng", "Việc cần làm"], [[r["vong"], r["cap"], r["vang"], r["viec"]] for r in s["lo_trinh"]]),
                unsafe_allow_html=True)
    st.caption("Đội hình hợp lối chơi này: " + " · ".join(s["doi_hinh"]))

ui.source_note()
