# ĐTCL Coach v1.0 (2026-10-06) — giao diện dùng chung: màu, chữ, thẻ tướng, bàn cờ lục giác
"""
Bảng màu "rừng đêm + đồng thau":
  nền #0F1714 · mặt thẻ #17211D · viền #2A3631 · đồng #C9A45C · chữ #ECE6D6 · chữ phụ #9AA59E
Viền tướng theo giá đúng màu trong game: 1 xám · 2 xanh lá · 3 xanh dương · 4 tím · 5 vàng.
Chữ: Be Vietnam Pro (thiết kế cho tiếng Việt). Ảnh tướng/đồ/lõi: Community Dragon (dữ liệu Riot).
"""
from __future__ import annotations

import html

import streamlit as st

from core import config, engine

COST_COLOR = {1: "#9B9B9B", 2: "#14B386", 3: "#2C86D9", 4: "#C54BDB", 5: "#F2B23A"}
TIER_COLOR = {"S": "#E8C06A", "A": "#7FB8A4", "B": "#8FA0B5", "C": "#6E7670"}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap');
:root{--bg:#0F1714;--card:#17211D;--card2:#1C2823;--line:#2A3631;--gold:#C9A45C;--gold2:#8C6A2F;
--txt:#ECE6D6;--mute:#9AA59E;}
html,body,[class*="css"],.stMarkdown,.stButton button,input,textarea,select{font-family:'Be Vietnam Pro',sans-serif!important;}
.stApp{background:radial-gradient(1200px 600px at 85% -10%,#1B2A23 0%,var(--bg) 55%);}
h1,h2,h3{letter-spacing:-.01em;color:var(--txt);}
h1{font-weight:800;font-size:2.05rem!important;}
h2{font-weight:700;font-size:1.45rem!important;}
h3{font-weight:700;font-size:1.12rem!important;}
[data-testid="stSidebar"]{background:#0C120F;border-right:1px solid var(--line);}
.block-container{padding-top:2.2rem;max-width:1180px;}
.stButton button{border-radius:10px;border:1px solid var(--line);}
.stButton button[kind="primary"]{background:var(--gold);color:#17120A;border:none;font-weight:700;}
.dc-lede{color:var(--mute);font-size:.98rem;margin:-.4rem 0 1.1rem;max-width:68ch;}
.dc-card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 18px;margin-bottom:12px;}
.dc-card.hi{border-color:var(--gold2);box-shadow:inset 0 0 0 1px rgba(201,164,92,.25);}
.dc-row{display:flex;flex-wrap:wrap;gap:8px;align-items:center;}
.dc-tile{position:relative;width:var(--s,54px);height:var(--s,54px);border-radius:10px;overflow:hidden;
border:2px solid var(--c,#999);background:#0B100E;flex:none;}
.dc-tile img{width:100%;height:100%;object-fit:cover;display:block;}
.dc-tile .nm{position:absolute;left:0;right:0;bottom:0;font-size:.62rem;line-height:1.15;text-align:center;
background:linear-gradient(transparent,rgba(0,0,0,.85));color:#fff;padding:8px 2px 2px;font-weight:600;}
.dc-tile.carry{box-shadow:0 0 0 2px var(--gold),0 0 12px rgba(201,164,92,.45);}
.dc-items{display:flex;gap:2px;justify-content:center;margin-top:3px;}
.dc-items img{width:18px;height:18px;border-radius:4px;border:1px solid #000;}
.dc-unit{display:flex;flex-direction:column;align-items:center;width:var(--s,54px);}
.dc-ico{width:var(--s,28px);height:var(--s,28px);border-radius:7px;border:1px solid var(--line);vertical-align:middle;}
.dc-tier{display:inline-grid;place-items:center;width:34px;height:34px;border-radius:9px;font-weight:800;
font-size:1.05rem;color:#14100A;background:var(--t);flex:none;}
.dc-chip{display:inline-flex;align-items:center;gap:6px;padding:3px 10px 3px 4px;border-radius:999px;
background:var(--card2);border:1px solid var(--line);font-size:.82rem;color:var(--txt);}
.dc-chip img{width:20px;height:20px;}
.dc-chip.off{opacity:.55;}
.dc-stat{display:flex;gap:22px;flex-wrap:wrap;margin:6px 0 2px;}
.dc-stat div{font-size:.78rem;color:var(--mute);}
.dc-stat b{display:block;font-size:1.15rem;color:var(--txt);font-variant-numeric:tabular-nums;}
.dc-src{font-size:.78rem;color:var(--mute);border-top:1px solid var(--line);margin-top:22px;padding-top:10px;}
.dc-src a{color:var(--gold);}
.dc-foot{font-size:.76rem;color:var(--mute);text-align:center;margin-top:36px;opacity:.85;}
.dc-board{display:inline-block;padding:10px 14px 14px;background:#0B110E;border:1px solid var(--line);border-radius:16px;}
.dc-hexrow{display:flex;gap:6px;margin-bottom:-10px;}
.dc-hexrow.odd{margin-left:33px;}
.dc-hex{width:60px;height:68px;clip-path:polygon(50% 0,100% 25%,100% 75%,50% 100%,0 75%,0 25%);
background:#22302A;display:grid;place-items:center;position:relative;}
.dc-hex.f{background:var(--c);}
.dc-hex .in{width:54px;height:62px;clip-path:inherit;overflow:hidden;background:#111;}
.dc-hex img{width:100%;height:100%;object-fit:cover;}
.dc-hex .lb{position:absolute;bottom:9px;font-size:.55rem;color:#fff;font-weight:700;text-shadow:0 1px 2px #000;}
.dc-hex.role{background:#2B2414;}
.dc-hex .rl{font-size:.5rem;color:var(--gold);text-align:center;padding:0 4px;line-height:1.1;font-weight:700;}
.dc-edge{font-size:.72rem;color:var(--mute);text-align:center;margin:2px 0 8px;}
.dc-edge:last-child{margin:14px 0 0;}
.dc-table{width:100%;border-collapse:collapse;font-size:.88rem;}
.dc-table th{text-align:left;color:var(--mute);font-weight:600;border-bottom:1px solid var(--line);padding:6px 8px;}
.dc-table td{border-bottom:1px solid #1f2b26;padding:6px 8px;vertical-align:top;}
.dc-note{background:#1F1A10;border:1px solid #4A3B1C;border-radius:12px;padding:10px 14px;color:#E9DCC0;font-size:.9rem;margin:8px 0 14px;}
.dc-plan b{color:var(--gold);}
.dc-why li{margin:2px 0;color:var(--txt);}
.dc-big{font-size:1.35rem;font-weight:800;color:var(--gold);}
@media (max-width:640px){.block-container{padding-left:.8rem;padding-right:.8rem;}
.dc-hex{width:42px;height:48px}.dc-hex .in{width:38px;height:44px}.dc-hexrow.odd{margin-left:24px}
.dc-hexrow{gap:4px;margin-bottom:-7px}h1{font-size:1.6rem!important}}
</style>
"""


def setup_page():
    st.markdown(CSS, unsafe_allow_html=True)


def esc(s) -> str:
    return html.escape(str(s))


def header(title: str, lede: str = ""):
    st.markdown(f"# {title}")
    if lede:
        st.markdown(f"<p class='dc-lede'>{esc(lede)}</p>", unsafe_allow_html=True)


# ---------------------------------------------------------------- mảnh HTML
def champ_tile(cid: str, size: int = 54, carry: bool = False, items: list[str] | None = None, name: bool = True) -> str:
    c = engine.champ(cid)
    col = COST_COLOR.get(c.get("gia", 1), "#999")
    nm = f"<span class='nm'>{esc(c['ten'])}</span>" if name else ""
    its = ""
    if items:
        its = "<div class='dc-items'>" + "".join(
            f"<img src='{engine.item(i).get('anh', '')}' title='{esc(engine.item_name(i))}' alt=''>" for i in items) + "</div>"
    return (f"<div class='dc-unit' style='--s:{size}px'><div class='dc-tile{' carry' if carry else ''}' "
            f"style='--c:{col};--s:{size}px' title='{esc(c['ten'])} · {c.get('gia', 1)} vàng'>"
            f"<img src='{c.get('anh', '')}' alt='{esc(c['ten'])}' loading='lazy'>{nm}</div>{its}</div>")


def champ_row(ids: list[str], size: int = 54, carries: dict[str, list[str]] | None = None) -> str:
    carries = carries or {}
    ids = sorted(dict.fromkeys(ids), key=lambda x: (x not in carries, engine.champ(x).get("gia", 1)))
    return "<div class='dc-row'>" + "".join(
        champ_tile(i, size, carry=i in carries, items=carries.get(i)) for i in ids) + "</div>"


def item_icon(iid: str, size: int = 28, label: bool = False) -> str:
    it = engine.item(iid)
    img = f"<img class='dc-ico' style='--s:{size}px' src='{it.get('anh', '')}' title='{esc(it['ten'])}' alt=''>"
    return f"<span class='dc-chip'>{img}{esc(it['ten'])}</span>" if label else img


def trait_chip(tid: str, n: int | None = None, active: bool = True) -> str:
    t = engine.data()["trait"].get(tid, {"ten": tid, "anh": ""})
    cnt = f" {n}" if n else ""
    return (f"<span class='dc-chip{'' if active else ' off'}'><img src='{t.get('anh', '')}' alt=''>"
            f"{esc(t['ten'])}{cnt}</span>")


def tier_badge(t: str) -> str:
    return f"<span class='dc-tier' style='--t:{TIER_COLOR.get(t, '#888')}'>{esc(t)}</span>"


def aug_chip(aid: str) -> str:
    a = engine.data()["aug"].get(aid)
    if not a:
        return ""
    img = f"<img src='{a['anh']}' alt=''>" if a.get("anh") else ""
    return f"<span class='dc-chip' title='{esc(a['mo_ta'])}'>{img}{esc(a['ten'])}</span>"


def _num(x):
    try:
        return float(str(x).replace(",", ".").replace("%", ""))
    except ValueError:
        return None


def stats_html(comp: dict) -> str:
    """Số liệu: ưu tiên máy chủ VN (Excel v1.8), kèm số MetaTFT quốc tế nếu khớp."""
    cells = []
    vn = comp.get("so_lieu_vn")
    if vn:
        cells += [("Hạng TB · VN", f"{vn['hang_tb']}"), ("Top 4 · VN", f"{vn['top4']}"), ("Tỉ lệ chơi · VN", f"{vn['ti_le']}")]
    mt = comp.get("so_lieu")
    if mt:
        cells += [("Hạng TB · quốc tế", f"{mt['hang_tb']:.2f}".replace(".", ",")),
                  ("Top 4 · quốc tế", f"{mt['top4']:.1f}%".replace(".", ","))]
    if not cells:
        return ""
    return "<div class='dc-stat'>" + "".join(f"<div>{esc(k)}<b>{esc(v)}</b></div>" for k, v in cells) + "</div>"


def roles_of(comp: dict) -> dict[str, list[str]]:
    return {r["tuong"]: r["do"] for r in comp.get("chu_luc", []) + comp.get("do_don", [])}


def board_html(board: dict[tuple[int, int], str], labels: list[list[str]] | None = None) -> str:
    rows = []
    for r in range(engine.ROWS):
        cells = []
        for c in range(engine.COLS):
            uid = board.get((r, c))
            if uid:
                ch = engine.champ(uid)
                col = COST_COLOR.get(ch.get("gia", 1), "#999")
                cells.append(f"<div class='dc-hex f' style='--c:{col}' title='{esc(ch['ten'])}'>"
                             f"<div class='in'><img src='{ch.get('anh', '')}' alt=''></div>"
                             f"<span class='lb'>{esc(ch['ten'][:9])}</span></div>")
            elif labels and labels[r][c]:
                cells.append(f"<div class='dc-hex role'><span class='rl'>{esc(labels[r][c])}</span></div>")
            else:
                cells.append("<div class='dc-hex'></div>")
        rows.append(f"<div class='dc-hexrow{' odd' if r % 2 else ''}'>{''.join(cells)}</div>")
    return ("<div class='dc-board'><div class='dc-edge'>Phía đối thủ</div>" + "".join(rows)
            + "<div class='dc-edge'>Hàng sau của bạn</div></div>")


def comp_card(comp: dict, highlight: bool = False, show_plan: bool = True, extra_html: str = ""):
    """Thẻ 1 đội hình (Excel v1.8): hạng, tên, lối chơi, số liệu, tướng + đồ, tộc hệ; mở ra xem lộ trình & sơ đồ."""
    ex = comp.get("excel", {})
    tr = "".join(trait_chip(t["id"], t["so"]) for t in comp["toc_he"])
    head = (f"<div class='dc-card{' hi' if highlight else ''}'>"
            f"<div class='dc-row' style='gap:12px'>{tier_badge(comp['hang'])}"
            f"<div><div style='font-weight:700;font-size:1.08rem'>{esc(comp['ten'])}</div>"
            f"<div style='color:var(--mute);font-size:.84rem'>{esc(comp['kieu_ten'])} · độ khó {esc(comp.get('do_kho', ''))}</div></div></div>"
            f"{stats_html(comp)}"
            f"<div style='margin:12px 0 8px'>{champ_row(comp['tuong'], 52, roles_of(comp))}</div>"
            f"<div class='dc-row' style='margin-top:8px'>{tr}</div>{extra_html}</div>")
    st.markdown(head, unsafe_allow_html=True)
    if not show_plan:
        return
    with st.expander("Lộ trình, lên đồ, lõi và xếp vị trí", expanded=False):
        if ex.get("tong_quan"):
            st.markdown(f"<p class='dc-lede' style='margin:0 0 10px'>{esc(ex['tong_quan'])}</p>", unsafe_allow_html=True)
        c1, c2 = st.columns([1.1, 1])
        with c1:
            st.markdown("**Lên đồ chuẩn**")
            for r in comp.get("chu_luc", []) + comp.get("do_don", []):
                icons = "".join(item_icon(i, 26) for i in r["do"])
                names = ", ".join(engine.item_name(i) for i in r["do"])
                note = f"<br><span style='color:var(--mute);font-size:.8rem'>{esc(r['ghi_chu'])}</span>" if r.get("ghi_chu") else ""
                st.markdown(f"<div class='dc-row' style='margin:6px 0;align-items:flex-start'>{champ_tile(r['tuong'], 40, name=False)}"
                            f"<div><b>{esc(engine.champ(r['tuong'])['ten'])}</b> <span style='color:var(--mute)'>· {esc(r['vai'])}</span>"
                            f"<br><span style='font-size:.85rem'>{icons} {esc(names)}</span>{note}</div></div>",
                            unsafe_allow_html=True)
            if ex.get("uu_tien_manh"):
                st.markdown(f"**Ưu tiên mảnh đồ:** {ex['uu_tien_manh']}")
            st.markdown("**Lõi khuyên dùng**")
            chips = "".join(aug_chip(a) for a in comp.get("loi_hop", []))
            st.markdown(f"<div class='dc-row'>{chips}</div>", unsafe_allow_html=True)
            st.caption(" · ".join(comp.get("loi_text", [])))
        with c2:
            for k, lab in (("len_cap", "Lên cấp & đổi tướng"), ("mo_man", "Mở màn (giai đoạn 2)"),
                           ("giua_tran", "Giữa trận (giai đoạn 3–4)"), ("khi_nao", "Khi nào nên chơi"),
                           ("meo", "Mẹo leo hạng"), ("diem_yeu", "Điểm yếu / khắc chế")):
                if ex.get(k):
                    st.markdown(f"<div class='dc-plan'><p><b>{lab}.</b> {esc(ex[k])}</p></div>", unsafe_allow_html=True)
        st.markdown(f"**Xếp vị trí** · mẫu “{esc(ex.get('mau_ban_co', ''))}” — {esc(ex.get('xep_vi_tri', ''))}")
        st.markdown(board_html(engine.template_board(comp)), unsafe_allow_html=True)


def source_note(extra: str = "", excel: bool = True):
    m = engine.data()["meta"]
    links = " · ".join(f"<a href='{s['url']}' target='_blank'>{esc(s['ten'])}</a>" for s in m["nguon"])
    ex = "Nội dung hướng dẫn: file Excel “Hướng dẫn Thách Đấu Mùa 18” v1.8 (06/10/2026). " if excel else ""
    st.markdown(f"<div class='dc-src'>{ex}Dữ liệu Mùa {m['mua']} ({esc(m['ten_mua_vi'])}), bản {esc(m['phien_ban'])}, "
                f"cập nhật {esc(m['ngay_cap_nhat'])}. Nguồn: {links}. {esc(extra)}</div>", unsafe_allow_html=True)


def note(text: str):
    st.markdown(f"<div class='dc-note'>{esc(text)}</div>", unsafe_allow_html=True)


def html_table(cols: list[str], rows: list[list]) -> str:
    th = "".join(f"<th>{esc(c)}</th>" for c in cols)
    tb = "".join("<tr>" + "".join(f"<td>{esc(v)}</td>" for v in r) + "</tr>" for r in rows)
    return f"<table class='dc-table'><thead><tr>{th}</tr></thead><tbody>{tb}</tbody></table>"


def login_panel():
    m = engine.data()["meta"]
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    st.markdown("# ĐTCL Coach")
    st.markdown(f"<p class='dc-lede'>Trợ lý Đấu Trường Chân Lý cho server Việt Nam. Đội hình, lõi, trang bị, "
                f"kinh tế và một trợ lý ván đấu tính sẵn nên đi đội nào, đổi tướng hay lên cấp, chọn lõi gì — "
                f"theo dữ liệu Mùa {m['mua']}, bản {esc(m['phien_ban'])}.</p>", unsafe_allow_html=True)
    sample = engine.comps(("S",))[:1]
    if sample:
        c = sample[0]
        st.markdown(f"<div class='dc-card hi'><div style='color:var(--mute);font-size:.82rem;margin-bottom:6px'>"
                    f"Đội số 1 máy chủ Việt Nam bản này</div>"
                    f"<div style='font-weight:700;margin-bottom:8px'>{esc(c['ten'])}</div>"
                    f"{champ_row(c['tuong'], 48, roles_of(c))}{stats_html(c)}</div>", unsafe_allow_html=True)


def footer():
    st.markdown(f"<div class='dc-foot'>{config.APP_NAME} {config.VERSION_LABEL} · Hướng dẫn giúp vào top đều hơn, "
                f"không đảm bảo top 1 mọi ván. Không liên kết với Riot Games.</div>", unsafe_allow_html=True)
