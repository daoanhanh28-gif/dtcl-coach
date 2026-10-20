# ĐTCL Coach v1.3 (2026-10-20) — số liệu cho trang Cẩm nang: top đội mạnh / mạnh ít người chơi / dễ vào top, mốc lên cấp
"""
Mọi con số lấy từ bộ dữ liệu đang xem:
  vn_opgg.json          — đội hình máy chủ VN (OP.GG): hạng TB, top 4, top 1, tỉ lệ chơi, độ khó, cấp mục tiêu, tướng + đồ
  metatft_doi_hinh.json — cụm đội quốc tế (MetaTFT, Bạch Kim+): hạng TB, top 4, số trận, Ấn hay ghép
  metatft_chi_tiet.json — vòng lên từng cấp của mỗi cụm đội → mốc lên cấp trung vị theo lối chơi
"""
from __future__ import annotations

import statistics
from collections import defaultdict

from core import engine as E

DO_KHO = {1: "Dễ", 2: "Vừa", 3: "Khó"}
DO_DO_DON = {"GargoyleStoneplate", "WarmogsArmor", "SpiritVisage", "Crownguard", "ProtectorsVow", "DragonsClaw",
             "BrambleVest", "SunfireCape", "SteadfastHeart", "Evenshroud", "IonicSpark", "TitansResolve"}


def chu_luc(r: dict) -> dict | None:
    """Tướng gánh sát thương: tên có trong tên đội, nếu không thì ít đồ đỡ đòn nhất, giá cao hơn."""
    xs = [x for x in r.get("chinh", []) if x.get("do")]
    if not xs:
        return None
    ten = E.norm(r["ten"])
    named = [x for x in xs if E.norm(E.champ(x["tuong"])["ten"]) in ten or E.norm(x["tuong"]) in ten]
    named = [x for x in named if sum(i in DO_DO_DON for i in x["do"]) < 2]
    if named:
        return named[0]
    return min(xs, key=lambda x: (sum(i in DO_DO_DON for i in x["do"]), -E.champ(x["tuong"]).get("gia", 1)))


def _vn() -> list[dict]:
    return (E.data().get("vn_opgg") or {}).get("doi_hinh", [])


def _metatft_for(units: list[str]) -> dict | None:
    us, best, score = set(units), None, 0.0
    for c in E.data()["metatft_doi_hinh"]:
        s = set(c["tuong"])
        j = len(us & s) / len(us | s) if us | s else 0
        if j > score:
            best, score = c, j
    return best if score >= 0.45 else None


def _dieu_kien(r: dict, mt: dict | None) -> list[str]:
    """Những thứ đội cần để chạy — càng ít càng dễ."""
    out = []
    cap = r.get("cap")
    if cap and cap <= 7:
        sao3 = [E.champ(x["tuong"])["ten"] for x in r.get("chinh", []) if x.get("sao3")]
        out.append(f"Reroll cấp {cap}" + (f": cần 3 sao {', '.join(sao3[:3])}" if sao3 else ""))
    elif cap:
        out.append(f"Lên cấp {cap}" + (" (tướng 5 vàng)" if cap >= 9 else " (tướng 4 vàng 2 sao)"))
    if mt and mt.get("an_nen_ghep"):
        out.append("Hay ghép " + ", ".join(E.item_name(i) for i in mt["an_nen_ghep"]))
    carry = chu_luc(r)
    if carry:
        out.append(f"Chủ lực {E.champ(carry['tuong'])['ten']}: " + ", ".join(E.item_name(i) for i in carry["do"]))
    return out


def _row(r: dict) -> dict:
    mt = _metatft_for(r["tuong"])
    return {**r, "metatft": mt, "dieu_kien": _dieu_kien(r, mt), "do_kho_ten": DO_KHO.get(r.get("do_kho"), "—")}


def top_manh(n: int = 6) -> list[dict]:
    """Mạnh nhất VN, đủ người chơi (≥ 0,3%) để số liệu tin được."""
    return [_row(r) for r in sorted((r for r in _vn() if r["ti_le"] >= 0.3), key=lambda r: r["hang_tb"])[:n]]


def manh_it_nguoi(n: int = 5) -> list[dict]:
    """Hạng TB tốt nhưng ít người chơi (< 0,3%) → ít bị tranh tướng. Cỡ mẫu nhỏ: số dao động."""
    rows = sorted((r for r in _vn() if r["ti_le"] < 0.3 and r["hang_tb"] <= 3.6), key=lambda r: r["hang_tb"])[:n]
    return [_row(r) for r in rows]


def manh_it_nguoi_quoc_te(n: int = 4) -> list[dict]:
    """Cụm MetaTFT hạng TB ≤ 4,35 nhưng ít trận (< 120.000 trong 3 ngày) — ít người biết."""
    cs = [c for c in E.data()["metatft_doi_hinh"] if c["so_lieu"]["so_tran"] < 120000 and c["so_lieu"]["hang_tb"] <= 4.35]
    return sorted(cs, key=lambda c: c["so_lieu"]["hang_tb"])[:n]


def de_vao_top(n: int = 5) -> list[dict]:
    """Dễ vào top 4, ít điều kiện: top 4 cao, độ khó thấp, không cần Ấn, không cần tướng 5 vàng."""
    out = []
    for r in _vn():
        if r["top4"] < 65 or r["ti_le"] < 0.1:
            continue
        row = _row(r)
        kho = {1: 0, 2: 5, 3: 12}.get(r.get("do_kho"), 6)
        can_an = 3 if row["metatft"] and row["metatft"].get("an_nen_ghep") else 0
        can_9 = 4 if (r.get("cap") or 8) >= 9 else 0
        row["diem_de"] = round(r["top4"] - kho - can_an - can_9, 1)
        out.append(row)
    return sorted(out, key=lambda r: -r["diem_de"])[:n]


def moc_len_cap() -> list[dict]:
    """Vòng lên mỗi cấp (trung vị các đội meta) theo lối chơi — tính từ MetaTFT."""
    ct = (E.data().get("metatft_chi_tiet") or {}).get("cum", {})
    comps = {c["id"].lstrip("c"): c for c in E.data()["metatft_doi_hinh"]}
    agg: dict[str, dict[int, list[int]]] = defaultdict(lambda: defaultdict(list))
    for cid, v in ct.items():
        c = comps.get(cid)
        if not c:
            continue
        for rnd, lv in v.get("cap", []):
            a, b = rnd.split("-")
            agg[c["kieu_ten"]][lv].append(int(a) * 10 + int(b))
    out = []
    for style in sorted(agg, key=lambda s: (s.startswith("Reroll"), s)):
        cells = {}
        for lv in range(4, 11):
            xs = agg[style].get(lv, [])
            if len(xs) >= 2:
                m = int(statistics.median(xs))
                cells[lv] = f"{m // 10}-{m % 10}"
        n = max((len(v) for v in agg[style].values()), default=0)
        if len(cells) < 3:
            continue
        out.append({"loi_choi": style, "so_doi": n, "cap": cells})
    return out
