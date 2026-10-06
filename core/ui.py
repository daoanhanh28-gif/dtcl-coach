# ĐTCL Coach v1.1 (2026-10-06) — giao diện dùng chung: màu, chữ, thẻ tướng, bàn cờ lục giác
"""
Bảng màu "rừng đêm + đồng thau":
  nền #0F1714 · mặt thẻ #17211D · viền #2A3631 · đồng #C9A45C · chữ #ECE6D6 · chữ phụ #9AA59E
Viền tướng theo giá đúng màu trong game: 1 xám · 2 xanh lá · 3 xanh dương · 4 tím · 5 vàng.
Chữ: Be Vietnam Pro (thiết kế cho tiếng Việt). Ảnh tướng/đồ/lõi: Community Dragon (dữ liệu Riot).
"""
from __future__ import annotations

import html
import re
from functools import lru_cache

import streamlit as st

from core import config, engine
from core import plan as P

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
.dc-rn{white-space:nowrap;}
.dc-rn img{width:var(--s,18px);height:var(--s,18px);border-radius:4px;vertical-align:-4px;margin-right:3px;border:1px solid #000;}
.dc-tag{position:absolute;top:0;left:0;font-size:.55rem;font-weight:800;padding:1px 4px;border-radius:0 0 6px 0;
background:var(--gold);color:#17120A;}
.dc-tag.tam{background:#5B6B63;color:#fff;}
.dc-tile.dim{opacity:.6;}
.dc-up{color:#5FD39A;font-weight:800;}.dc-down{color:#F07A6A;font-weight:800;}.dc-new{color:#7FB8FF;font-weight:800;}
.dc-ans{display:grid;grid-template-columns:34px 1fr;gap:10px 12px;align-items:center;}
.dc-ans .k{font-size:1.3rem;text-align:center;}
.dc-ans .v{font-size:1rem;}
.dc-ans .v b{color:var(--gold);}
.dc-step{font-weight:800;color:var(--gold);font-size:1.02rem;margin:4px 0 6px;}
[class*="st-key-pk"] [data-testid="stHorizontalBlock"]{flex-wrap:nowrap!important;gap:4px!important;}
[class*="st-key-pk"] [data-testid="stColumn"]{min-width:0!important;width:auto!important;flex:1 1 0!important;}
[class*="st-key-pk"] button{padding:3px 1px!important;min-height:0!important;line-height:1.05;border-radius:10px!important;}
[class*="st-key-pk"] button p{font-size:.64rem!important;display:flex;flex-direction:column;align-items:center;gap:2px;
margin:0;white-space:normal;word-break:break-word;}
[class*="st-key-pk"] button img{width:40px!important;height:40px!important;max-height:none!important;max-width:100%!important;
border-radius:8px;object-fit:cover;}
[class*="st-key-pk"] button[kind="primary"] img{outline:2px solid #17120A;}
.st-key-hexgrid button img{width:34px!important;height:34px!important;max-height:none!important;border-radius:50%;object-fit:cover;}
@media (max-width:640px){.block-container{padding-left:.8rem;padding-right:.8rem;}
.dc-hex{width:42px;height:48px}.dc-hex .in{width:38px;height:44px}.dc-hexrow.odd{margin-left:24px}
.dc-hexrow{gap:4px;margin-bottom:-7px}h1{font-size:1.6rem!important}
[class*="st-key-pk"] button img{width:30px!important;height:30px!important}
[class*="st-key-pk"] button p{font-size:.55rem!important}}
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
def champ_tile(cid: str, size: int = 54, carry: bool = False, items: list[str] | None = None, name: bool = True,
               tag: str = "", dim: bool = False) -> str:
    c = engine.champ(cid)
    col = COST_COLOR.get(c.get("gia", 1), "#999")
    nm = f"<span class='nm'>{esc(c['ten'])}</span>" if name else ""
    if tag:
        nm += f"<span class='dc-tag{' tam' if tag == 'tạm' else ''}'>{esc(tag)}</span>"
    its = ""
    if items:
        its = "<div class='dc-items'>" + "".join(
            f"<img src='{engine.item(i).get('anh', '')}' title='{esc(engine.item_name(i))}' alt=''>" for i in items) + "</div>"
    return (f"<div class='dc-unit' style='--s:{size}px'><div class='dc-tile{' carry' if carry else ''}{' dim' if dim else ''}' "
            f"style='--c:{col};--s:{size}px' title='{esc(c['ten'])} · {c.get('gia', 1)} vàng'>"
            f"<img src='{c.get('anh', '')}' alt='{esc(c['ten'])}' loading='lazy'>{nm}</div>{its}</div>")


def champ_row(ids: list[str], size: int = 54, carries: dict[str, list[str]] | None = None,
              tags: dict[str, str] | None = None, dim: set | None = None, sort: bool = True) -> str:
    carries, tags, dim = carries or {}, tags or {}, dim or set()
    ids = list(dict.fromkeys(ids))
    if sort:
        ids.sort(key=lambda x: (x not in carries, engine.champ(x).get("gia", 1)))
    return "<div class='dc-row'>" + "".join(
        champ_tile(i, size, carry=i in carries, items=carries.get(i), tag=tags.get(i, ""), dim=i in dim) for i in ids) + "</div>"


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
        st.markdown("**Form theo vòng — từ đầu trận tới đội hoàn chỉnh**")
        stage_view(comp)
        st.markdown(f"**Mẫu xếp của Excel** · “{esc(ex.get('mau_ban_co', ''))}” — {esc(ex.get('xep_vi_tri', ''))}")
        st.markdown(board_html(engine.template_board(comp)), unsafe_allow_html=True)


def stage_view(comp: dict, emblems: list[str] | None = None, key: str = ""):
    """Các tab Cấp 4 → Cấp 7 → Hoàn chỉnh: tướng, ai cầm Ấn, tộc hệ, vị trí đứng thật (MetaTFT)."""
    sb = P.stage_boards(comp, emblems)
    tabs = st.tabs([f"{g['ten']} · {g['vong']}" for g in sb["giai_doan"]])
    for tab, g in zip(tabs, sb["giai_doan"]):
        with tab:
            tags = {u: "tạm" for u in g["tam"]}
            for a in g["an"]:
                if a["nguoi_deo"]:
                    tags[a["nguoi_deo"]] = "Ấn"
            src = g["so_lieu"]
            meta = (f"MetaTFT: hạng TB {src['hang_tb']:.2f} · {src['so_tran']:,} trận".replace(",", ".") if src
                    else "đội hoàn chỉnh")
            st.markdown(f"<div style='color:var(--mute);font-size:.82rem;margin-bottom:6px'>Cấp {g['cap']} · khoảng vòng "
                        f"{esc(g['vong'])} · {esc(meta)}</div>"
                        f"{champ_row(g['tuong'], 46, roles_of(comp) if g['ten'] == 'Hoàn chỉnh' else None, tags=tags, dim=set(g['tam']))}",
                        unsafe_allow_html=True)
            notes = []
            if g["tam"]:
                notes.append("Tướng “tạm” giữ máu giai đoạn này, bán dần khi có tướng của đội hình cuối: "
                             + ", ".join(engine.champ(u)["ten"] for u in g["tam"]) + ".")
            if g["thieu"] and g["ten"] != "Hoàn chỉnh":
                notes.append("Thấy là mua sớm: " + ", ".join(engine.champ(u)["ten"] for u in g["thieu"]) + ".")
            for a in g["an"]:
                if not a["nguoi_deo"]:
                    notes.append(f"{engine.item_name(a['an'])}: chưa đeo — đeo lúc này không mở thêm mốc; cất ở hàng chờ, "
                                 f"có {engine.champ(a['chuyen_cho'])['ten']} thì đeo cho {engine.champ(a['chuyen_cho'])['ten']}.")
                    continue
                who = engine.champ(a["nguoi_deo"])["ten"]
                moc = f" → {P.trait_name(a['toc_he'])} {a['sau']}" + (" (mở mốc mới)" if a["len_moc"] else "")
                if a["tam"] and a["chuyen_cho"]:
                    notes.append(f"{engine.item_name(a['an'])}: đeo tạm cho {who}{moc}. Khi có "
                                 f"{engine.champ(a['chuyen_cho'])['ten']} thì bán {who} — Ấn tự về hàng chờ, đeo lại cho "
                                 f"{engine.champ(a['chuyen_cho'])['ten']}.")
                else:
                    notes.append(f"{engine.item_name(a['an'])}: đeo cho {who}{moc}.")
            if notes:
                st.markdown("<ul class='dc-why'>" + "".join(f"<li>{rich(n)}</li>" for n in notes) + "</ul>",
                            unsafe_allow_html=True)
            c1, c2 = st.columns([1.25, 1])
            c1.markdown(board_html(g["ban_co"]), unsafe_allow_html=True)
            c2.markdown("<div class='dc-row'>" + "".join(trait_chip(t["id"], t["so"]) for t in g["toc_he"]) + "</div>",
                        unsafe_allow_html=True)
    st.caption(f"Nguồn form: {sb['nguon']}. Vị trí đứng = ô phổ biến nhất của từng tướng trong các ván Bạch Kim+.")


def source_note(extra: str = "", excel: bool = True):
    m = engine.data()["meta"]
    links = " · ".join(f"<a href='{s['url']}' target='_blank'>{esc(s['ten'])}</a>" for s in m["nguon"])
    ex = "Nội dung hướng dẫn: file Excel “Hướng dẫn Thách Đấu Mùa 18” v1.8 (06/10/2026). " if excel else ""
    st.markdown(f"<div class='dc-src'>{ex}Dữ liệu Mùa {m['mua']} ({esc(m['ten_mua_vi'])}), bản {esc(m['phien_ban'])}, "
                f"cập nhật {esc(m['ngay_cap_nhat'])}. Nguồn: {links}. {esc(extra)}</div>", unsafe_allow_html=True)


def note(text: str):
    st.markdown(f"<div class='dc-note'>{esc(text)}</div>", unsafe_allow_html=True)


class Raw(str):
    """Ô bảng đã là HTML sẵn (không escape lại)."""


def html_table(cols: list[str], rows: list[list], rich_text: bool = False) -> str:
    def cell(v):
        if isinstance(v, Raw):
            return v
        return rich(v) if rich_text and isinstance(v, str) else esc(v)
    th = "".join(f"<th>{esc(c)}</th>" for c in cols)
    tb = "".join("<tr>" + "".join(f"<td>{cell(v)}</td>" for v in r) + "</tr>" for r in rows)
    return f"<div style='overflow-x:auto'><table class='dc-table'><thead><tr>{th}</tr></thead><tbody>{tb}</tbody></table></div>"


# ---------------------------------------------------------------- chữ có hình: tên tướng / đồ / lõi / tộc hệ → kèm ảnh
@lru_cache(maxsize=None)
def _name_index() -> tuple[dict, re.Pattern | None]:
    d = engine.data()
    m: dict[str, str] = {}
    for a in d["loi"]:
        if a.get("anh") and len(a["ten"].split()) >= 2:
            m[a["ten"]] = a["anh"]
    for it in d["item"].values():
        if it.get("anh"):
            m[it["ten"]] = it["anh"]
    for k, v in d["anh_phu"]["tao_tac"].items():
        for part in k.split(" / "):
            m[part.strip()] = v
    for t in d["toc_he"]:
        if t.get("anh"):
            m[t["ten"]] = t["anh"]
    for c in d["tuong"]:
        if c.get("anh"):
            m[c["ten"]] = c["anh"]
            if c.get("ten_en"):
                m.setdefault(c["ten_en"], c["anh"])
    keys = sorted((k for k in m if len(k) >= 2), key=len, reverse=True)
    if not keys:
        return {}, None
    esc_map = {html.escape(k, quote=False): m[k] for k in keys}
    pat = re.compile(r"(?<!\w)(" + "|".join(re.escape(k) for k in esc_map) + r")(?!\w)")
    return esc_map, pat


def rich(text, size: int = 18) -> str:
    """Chữ thường → HTML, mỗi tên tướng / trang bị / Ấn / Tạo Tác / lõi / tộc hệ có ảnh nhỏ đứng trước."""
    s = html.escape(str(text), quote=False)
    m, pat = _name_index()
    if not pat:
        return s
    return pat.sub(lambda g: f"<span class='dc-rn' style='--s:{size}px'><img src='{m[g.group(1)]}' alt=''>{g.group(1)}</span>", s)


def img(url: str, size: int = 28, title: str = "") -> str:
    return f"<img class='dc-ico' style='--s:{size}px' src='{url}' title='{esc(title)}' alt=''>" if url else ""


def aug_icon(aid: str, size: int = 28) -> str:
    a = engine.data()["aug"].get(aid) or {}
    return img(a.get("anh", ""), size, a.get("ten", ""))


def trait_icon(tid: str, size: int = 22) -> str:
    t = engine.data()["trait"].get(tid) or {}
    return img(t.get("anh", ""), size, t.get("ten", ""))


def change_mark(huong: str) -> str:
    return {"tang": "<span class='dc-up'>▲ tăng</span>", "giam": "<span class='dc-down'>▼ giảm</span>",
            "moi": "<span class='dc-new'>✚ mới</span>", "xoa": "<span class='dc-down'>✖ xoá</span>"}.get(huong, "")


def trend_mark(x: float) -> str:
    if x >= 2:
        return "<span class='dc-up'>▲▲</span>"
    if x > 0:
        return "<span class='dc-up'>▲</span>"
    if x <= -2:
        return "<span class='dc-down'>▼▼</span>"
    if x < 0:
        return "<span class='dc-down'>▼</span>"
    return "<span style='color:var(--mute)'>■</span>"


# ---------------------------------------------------------------- bảng chọn bằng hình (bấm để chọn / bỏ)
def pick_grid(key: str, options: list[tuple[str, str, str]], selected, on_click, per_row: int = 8,
              names: bool = True, counts: dict | None = None):
    """options = [(id, tên, ảnh)]. Mỗi ô là 1 nút có ảnh; đang chọn = nút vàng. on_click(id) chạy trước khi vẽ lại."""
    counts = counts or {}
    with st.container(key=f"pkg_{key}"):
        for i in range(0, len(options), per_row):
            cols = st.columns(per_row)
            for col, (oid, name, url) in zip(cols, options[i:i + per_row]):
                n = counts.get(oid, 0)
                label = (f"![{name}]({url})" if url else "") + (f" {name}" if names or not url else "")
                if n:
                    label += f" ×{n}"
                col.button(label, key=f"pk{key}_{oid}", help=name, use_container_width=True,
                           type="primary" if (oid in selected or n) else "secondary", on_click=on_click, args=(oid,))


def champ_options(ids: list[str] | None = None) -> list[tuple[str, str, str]]:
    cs = sorted(engine.data()["tuong"], key=lambda c: (c["gia"], c["ten"]))
    return [(c["id"], c["ten"], c.get("anh", "")) for c in cs if ids is None or c["id"] in ids]


def item_options(ids: list[str]) -> list[tuple[str, str, str]]:
    return [(i, engine.item_name(i), engine.item(i).get("anh", "")) for i in ids]


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
