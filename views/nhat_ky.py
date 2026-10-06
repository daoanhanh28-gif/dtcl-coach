# ĐTCL Coach v1.0 (2026-10-06) — trang Nhật ký ván đấu (lưu Google Sheets) + thống kê đội hợp tay
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import auth, db, engine, ui

d = engine.data()
user = auth.current_user() or {"name": "", "admin": False}
ui.header("Nhật ký ván đấu",
          "Ghi lại mỗi ván: đội hình, lõi, trang bị, hạng về. Web tự tính tỉ lệ top 4 / top 1 theo đội và theo lõi, "
          "chỉ ra đội hợp tay nhất của bạn.")

KHAC = "Khác (tự ghi)"
comp_names = [c["ten"] for c in engine.comps()] + [KHAC]
aug_names = sorted(a["ten"] for a in d["loi"])
item_names = sorted(i["ten"] for i in d["trang_bi"]["hoan_chinh"]) + sorted(e["ten"] for e in d["trang_bi"]["an"])

st.session_state.setdefault("nk_form", 0)
with st.form(f"nk_{st.session_state.nk_form}", border=True):
    c1, c2 = st.columns([2, 1])
    comp = c1.selectbox("Đội hình đã chơi", comp_names)
    place = c2.selectbox("Hạng về", list(range(1, 9)), index=3)
    other = st.text_input("Tên đội (nếu chọn Khác)", placeholder="Ví dụ: Gai Đen Warwick")
    augs = st.multiselect("Lõi đã chọn", aug_names, max_selections=3)
    items = st.multiselect("Trang bị / Ấn trên chủ lực", item_names, max_selections=6)
    c3, c4 = st.columns(2)
    level = c3.selectbox("Cấp cuối trận", list(range(5, 11)), index=3)
    hp_round = c4.text_input("Bị loại / kết thúc ở vòng", placeholder="Ví dụ: 6-2")
    note = st.text_area("Lỗi lớn nhất ván này (để sửa ván sau)", height=70)
    ok = st.form_submit_button("Lưu ván đấu", type="primary", use_container_width=True)

if ok:
    name = other.strip() if comp == KHAC else comp
    if not name:
        st.error("Ghi tên đội hình khi chọn “Khác”.")
    else:
        saved = db.log("nhat_ky", {"nguoi_choi": user["name"], "doi_hinh": name, "hang": int(place),
                                   "loi": "; ".join(augs), "trang_bi": "; ".join(items), "cap": int(level),
                                   "vong_cuoi": f"'{hp_round}" if hp_round else "", "ghi_chu": note.strip(),
                                   "ban_game": d["meta"]["phien_ban"]})
        if saved:
            st.success(f"Đã lưu: {name} · hạng {place}.")
            st.session_state.nk_form += 1
        else:
            st.error("Chưa lưu được vào Google Sheets — kiểm tra SHEETS_WEBAPP_URL / SHEETS_TOKEN trong Secrets.")


def load_rows() -> list[dict]:
    df = db.read("nhat_ky")
    if df.empty:
        return []
    rows = []
    for r in df.to_dict("records"):
        # Google Sheets có thể tự đổi kiểu → ép lại từng ô
        try:
            r["hang"] = int(float(r.get("hang", 0)))
        except (TypeError, ValueError):
            continue
        for k in ("doi_hinh", "loi", "trang_bi", "ghi_chu", "nguoi_choi", "vong_cuoi", "thoi_gian"):
            v = r.get(k, "")
            r[k] = "" if v is None or (isinstance(v, float) and pd.isna(v)) else str(v).lstrip("'")
        rows.append(r)
    if not user.get("admin"):
        rows = [r for r in rows if engine.norm(r["nguoi_choi"]) == engine.norm(user["name"])]
    return rows


rows = load_rows()
st.markdown("## Thống kê của bạn")
if not rows:
    st.info("Chưa có ván nào. Ghi ván đầu tiên ở khung trên — sau 3 ván cùng một đội, web sẽ chỉ ra đội hợp tay nhất.")
else:
    n = len(rows)
    places = [r["hang"] for r in rows]
    st.markdown(f"<div class='dc-card'><div class='dc-stat'><div>Số ván<b>{n}</b></div>"
                f"<div>Hạng TB<b>{sum(places) / n:.2f}</b></div>"
                f"<div>Top 4<b>{round(100 * sum(p <= 4 for p in places) / n)}%</b></div>"
                f"<div>Top 1<b>{round(100 * sum(p == 1 for p in places) / n)}%</b></div></div></div>",
                unsafe_allow_html=True)
    fit = engine.best_fit(rows)
    if fit:
        ui.note(f"Đội hợp tay nhất: {fit['ten']} — {fit['so_van']} ván, hạng TB {fit['hang_tb']}, top 4 {fit['top4']}%.")
    else:
        st.caption("Cần ít nhất 3 ván cùng một đội để xác định đội hợp tay nhất.")

    df = pd.DataFrame(rows)
    df["van"] = range(1, n + 1)
    df["tb5"] = df["hang"].rolling(5, min_periods=1).mean()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["van"], y=df["hang"], mode="markers", name="Hạng từng ván",
                             marker=dict(color="#9AA59E", size=7)))
    fig.add_trace(go.Scatter(x=df["van"], y=df["tb5"], mode="lines", name="Trung bình 5 ván",
                             line=dict(color="#C9A45C", width=3)))
    fig.add_hline(y=4.5, line_dash="dot", line_color="#4A5A52", annotation_text="ranh giới top 4",
                  annotation_font_color="#9AA59E")
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#ECE6D6", family="Be Vietnam Pro"),
                      yaxis=dict(autorange="reversed", range=[8.5, 0.5], title="Hạng", gridcolor="#1f2b26", dtick=1),
                      xaxis=dict(title="Ván", gridcolor="#1f2b26"), legend=dict(orientation="h", y=1.15),
                      title=dict(text="Hạng theo thời gian (thấp hơn là tốt hơn)", font=dict(size=14)))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    t1, t2, t3 = st.tabs(["Theo đội hình", "Theo lõi", "Các ván gần đây"])
    with t1:
        s = engine.stats_by(rows, "doi_hinh")
        st.markdown(ui.html_table(["Đội hình", "Số ván", "Hạng TB", "Top 4 %", "Top 1 %"],
                                  [[x["ten"], x["so_van"], x["hang_tb"], x["top4"], x["top1"]] for x in s]), unsafe_allow_html=True)
    with t2:
        s = engine.stats_by(rows, "loi")
        st.markdown(ui.html_table(["Lõi", "Số ván", "Hạng TB", "Top 4 %", "Top 1 %"],
                                  [[x["ten"], x["so_van"], x["hang_tb"], x["top4"], x["top1"]] for x in s]), unsafe_allow_html=True)
    with t3:
        recent = rows[-15:][::-1]
        cols = ["Thời gian", "Đội hình", "Hạng", "Lõi", "Lỗi lớn nhất"] + (["Người chơi"] if user.get("admin") else [])
        st.markdown(ui.html_table(cols, [[r.get("thoi_gian", ""), r["doi_hinh"], r["hang"], r["loi"], r["ghi_chu"]]
                                         + ([r["nguoi_choi"]] if user.get("admin") else []) for r in recent]),
                    unsafe_allow_html=True)
st.caption(f"Nơi lưu: {db.backend()}.")
