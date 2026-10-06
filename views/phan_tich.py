# ĐTCL Coach v1.1 (2026-10-06) — trang Phân tích bản cập nhật: tăng/giảm có hình + đội nên chơi, dễ top 1, ít người biết…
import streamlit as st

from core import engine, ui
from core import plan as P

d = engine.data()
bc = d["ban_cap_nhat"]
ui.header(f"Phân tích bản {bc['phien_ban']}",
          f"Bản {bc['phien_ban']} ra {bc['ngay']}. Tướng / tộc hệ / lõi được tăng hay giảm, và đội nào đang được lợi, "
          f"mạnh nhất, dễ top 1, dễ vào top 4, mạnh mà ít người chơi để spam, đội nên tránh.")
ui.note(bc["ghi_chu"])

tab1, tab2, tab3 = st.tabs(["Đội nên chơi", "Tăng / giảm", "Bảng tổng hợp"])


def row_html(i: int, r: dict) -> str:
    vn = r["vn"]
    stats = []
    if vn.get("hang_tb"):
        stats.append(("Hạng TB VN", f"{vn['hang_tb']:.2f}"))
    if vn.get("top4"):
        stats.append(("Top 4 VN", f"{vn['top4']:.1f}%".replace(".", ",")))
    if vn.get("ti_le") is not None:
        stats.append(("Người chơi", f"{vn['ti_le']:.2f}%".replace(".", ",")))
    if r.get("metatft"):
        stats.append(("Top 1 quốc tế", f"{r['metatft']['top1']:.1f}%".replace(".", ",")))
    flags = []
    if r.get("mau_nho"):
        flags.append("mẫu số liệu nhỏ")
    if r.get("tranh_nhieu"):
        flags.append("bị tranh nhiều")
    carry = set(r.get("chu_luc") or [])
    return (f"<div class='dc-card'><div class='dc-row' style='gap:10px'><span class='dc-tier' style='--t:#C9A45C'>{i}</span>"
            f"<div style='flex:1'><b>{ui.esc(r['ten'])}</b> {ui.trend_mark(r['xu_huong'])}"
            f"<div style='font-size:.84rem;color:var(--mute)'>{ui.rich(r['ban_moi'])}"
            f"{' · ⚠ ' + ui.esc(', '.join(flags)) if flags else ''}</div></div></div>"
            f"<div style='margin:8px 0'>{ui.champ_row(r['tuong'], 40, {u: [] for u in carry})}</div>"
            f"<div class='dc-stat'>" + "".join(f"<div>{ui.esc(k)}<b>{ui.esc(v)}</b></div>" for k, v in stats) + "</div></div>")


with tab1:
    pa = P.patch_analysis()
    for key, title, why in P.CATEGORIES:
        rows = pa.get(key, [])
        st.markdown(f"### {title}")
        st.caption(why)
        if not rows:
            st.caption("Chưa có đội nào thỏa điều kiện.")
            continue
        cols = st.columns(2)
        for i, r in enumerate(rows[:4]):
            cols[i % 2].markdown(row_html(i + 1, r), unsafe_allow_html=True)
    st.caption("Điểm “nên chơi” = hạng TB VN 18.3b − 0,12 × xu hướng 18.4 (▲▲ = +2 … ▼▼ = −2) + 0,15 nếu ≥ 3% người chơi "
               "(dễ bị tranh tướng) + 0,25 nếu < 0,15% người chơi (mẫu nhỏ). Thấp hơn là tốt hơn. "
               "Xu hướng lấy từ nhận định bản 18.4 trong file Excel v1.8.")

with tab2:
    ch = P.patch_changes()
    for loai, title in (("tuong", "Tướng"), ("toc_he", "Tộc / hệ"), ("loi", "Lõi"), ("tinh_linh", "Tinh Linh")):
        xs = [x for x in ch if x["loai"] == loai]
        if not xs:
            continue
        st.markdown(f"### {title}")
        html = ""
        for x in xs:
            if loai == "tuong" and x["ref"]:
                pic = ui.champ_tile(x["ref"], 44, name=False)
            elif loai == "toc_he" and x["ref"]:
                pic = ui.trait_icon(x["ref"], 40)
            elif loai == "loi" and x["ref"]:
                pic = ui.aug_icon(x["ref"], 40)
            elif loai == "tinh_linh":
                pic = ui.img(d["anh_phu"]["tinh_linh"], 40)
            else:
                pic = "<span class='dc-tier' style='--t:#2A3631;color:#ECE6D6'>?</span>"
            name = engine.champ(x["ref"])["ten"] if loai == "tuong" and x["ref"] else x["ten"]
            html += (f"<div class='dc-row' style='margin:6px 0;gap:12px'>{pic}<div><b>{ui.esc(name)}</b> "
                     f"{ui.change_mark(x['huong'])}<div style='font-size:.88rem'>{ui.esc(x['chi_tiet'])}</div></div></div>")
        st.markdown(f"<div class='dc-card'>{html}</div>", unsafe_allow_html=True)
    st.markdown("### Nhận định của file hướng dẫn")
    for x in d["hd_kien_thuc"]["ban_moi"]:
        st.markdown(f"<div style='margin:4px 0'><b>{ui.esc(x['k'])}</b> — {ui.rich(x['v'])}</div>", unsafe_allow_html=True)

with tab3:
    rows = sorted(P.patch_rows(), key=lambda r: r["diem"])
    st.markdown(ui.html_table(
        ["#", "Đội hình", "Xu hướng 18.4", "Hạng TB VN", "Top 4 VN", "Người chơi", "Top 1 quốc tế", "Điểm nên chơi", "Bản 18.4"],
        [[i + 1, r["ten"], ui.Raw(ui.trend_mark(r["xu_huong"])), r["vn"]["hang_tb"] or "—",
          f"{r['vn']['top4']}%" if r["vn"]["top4"] else "—", f"{r['vn']['ti_le']}%" if r["vn"]["ti_le"] is not None else "—",
          f"{r['metatft']['top1']}%" if r["metatft"] else "—", r["diem"], r["ban_moi"]] for i, r in enumerate(rows)],
        rich_text=True), unsafe_allow_html=True)

st.markdown(f"<div class='dc-src'>Nguồn: {ui.esc(bc['nguon'])}. Top 1 quốc tế: MetaTFT (Bạch Kim+, 3 ngày, 18.3b). "
            f"Phân tích giúp chọn đội, không đảm bảo top 1 mọi ván.</div>", unsafe_allow_html=True)
