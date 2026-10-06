# ĐTCL Coach v1.1 (2026-10-06) — form theo vòng, tối ưu mốc tộc/hệ với Ấn, phân tích bản cập nhật (luật trong code)
"""
  - form theo vòng:        stage_boards(comp, emblems)   — đội phổ biến nhất ở cấp 4/5/6/7 (MetaTFT) → đội hoàn chỉnh
  - xếp vị trí thật:       place(units, cum)             — ô đứng phổ biến nhất của từng tướng (MetaTFT)
  - tối ưu Ấn:             emblem_plan(units, emblems, core, level) — ai đeo, mốc nào mở, thay tướng nào để lên mốc cao hơn
  - phân tích bản:         patch_analysis()              — đội được lợi / mạnh nhất / dễ top 1 / dễ top 4 / mạnh ít người chơi …
  - đồ tốt nhất từng tướng: best_items(cid)
Không bịa số: mọi con số lấy từ data/*.json (MetaTFT, OP.GG VN qua Excel v1.8).
"""
from __future__ import annotations

import re
from collections import Counter
from functools import lru_cache

from core import engine as E

# ============================================================================ tiện ích tộc/hệ


def trait_moc(tid: str) -> list[int]:
    return [m for m in E.data()["trait"].get(tid, {}).get("moc", []) if m]


def tiers(tid: str, n: int) -> int:
    """Số mốc đã đạt của tộc/hệ khi có n tướng."""
    return sum(1 for m in trait_moc(tid) if n >= m)


def counts(units: list[str], extra: list[str] = ()) -> Counter:
    c = Counter()
    for u in dict.fromkeys(units):
        for t in E.champ(u).get("toc_he", []):
            c[t] += 1
    for t in extra:
        c[t] += 1
    return c


def trait_name(tid: str) -> str:
    return E.data()["trait"].get(tid, {}).get("ten", tid)


def emblem_trait(iid: str) -> str | None:
    it = E.item(iid)
    return it.get("toc_he") if it.get("loai") == "an" else None


def comp_emblems(comp: dict) -> list[tuple[str, str]]:
    """Ấn có sẵn trong bộ đồ chuẩn của đội: [(id ấn, tướng cầm)]."""
    out = []
    for r in comp.get("chu_luc", []) + comp.get("do_don", []):
        for i in r["do"]:
            if emblem_trait(i):
                out.append((i, r["tuong"]))
    return out


# ============================================================================ MetaTFT: cụm đội, vị trí


def _details() -> dict:
    return E.data()["metatft_chi_tiet"]


def cluster_for(units: list[str], min_j: float = 0.3) -> tuple[str | None, float]:
    us = set(units)
    best, score = None, 0.0
    for r in E.data()["metatft_doi_hinh"]:
        s = set(r["tuong"])
        j = len(us & s) / len(us | s) if us | s else 0
        if j > score:
            best, score = r["id"].lstrip("c"), j
    return (best, score) if score >= min_j else (None, score)


@lru_cache(maxsize=None)
def _global_pos() -> dict[str, tuple[int, int]]:
    cnt: dict[str, Counter] = {}
    for c in _details()["cum"].values():
        for u, rc in c["vi_tri"].items():
            cnt.setdefault(u, Counter())[tuple(rc)] += 1
    return {u: c.most_common(1)[0][0] for u, c in cnt.items()}


def place(units: list[str], cum: str | None = None) -> dict[tuple[int, int], str]:
    """Đặt tướng vào ô phổ biến nhất (ưu tiên ô của chính cụm đội), trùng ô thì dời sang ô trống gần nhất."""
    pref = {u: tuple(rc) for u, rc in (_details()["cum"].get(cum or "", {}).get("vi_tri", {})).items()}
    gpos = _global_pos()
    board: dict[tuple[int, int], str] = {}
    order = sorted(dict.fromkeys(units), key=lambda u: (u not in pref, u not in gpos))
    for u in order:
        want = pref.get(u) or gpos.get(u)
        if not want:
            want = (0, 3) if E.champ(u).get("tam_danh", 1) <= 1 else (3, 3)
        cells = sorted(((r, c) for r in range(E.ROWS) for c in range(E.COLS) if (r, c) not in board),
                       key=lambda rc: (abs(rc[0] - want[0]) * 2 + abs(rc[1] - want[1]), rc))
        if cells:
            board[cells[0]] = u
    return board


# ============================================================================ form theo vòng


def _round_for_level(cum: dict | None, level: int, kieu: str) -> str:
    if level <= 3:
        return "1-4"
    if level == 4:
        return "2-1"
    if cum:
        for r, lv in cum["cap"]:
            if lv >= level:
                return r
    return {5: "2-5", 6: "3-2", 7: "3-5", 8: "4-2", 9: "5-2"}.get(level, "4-2")


def _final_units(comp: dict) -> list[str]:
    units = list(dict.fromkeys(comp["tuong"]))
    n = max(comp.get("cap_muc_tieu", 8), 8) if len(units) >= 8 else len(units)
    return units[:n]


def stage_boards(comp: dict, emblems: list[str] | None = None) -> dict:
    """Form của đội từ cấp 4 → hoàn chỉnh. Mỗi giai đoạn: tướng, vị trí, tộc/hệ, ai cầm Ấn (tạm hay lâu dài)."""
    final = _final_units(comp)
    cid, j = cluster_for(final)
    cum = _details()["cum"].get(cid) if cid else None
    core = {r["tuong"] for r in comp.get("chu_luc", []) + comp.get("do_don", [])}
    embl = list(emblems) if emblems else [i for i, _ in comp_emblems(comp)]
    final_holder = dict(comp_emblems(comp))
    core_list = [r["tuong"] for r in comp.get("chu_luc", []) + comp.get("do_don", [])]
    for e, u in _assign(final, embl, core_list).items():
        final_holder.setdefault(e, u)          # Ấn của người chơi: người cầm cuối = chủ lực / đỡ đòn chưa có tộc đó
    stages = []
    locked: dict[str, str] = {}
    for lv in (4, 5, 6, 7):
        boards = (cum or {}).get("som", {}).get(str(lv), [])
        if boards:
            b = max(boards, key=lambda x: (len(set(x["tuong"]) & set(final)), -x["hang_tb"]))
            units, src = b["tuong"], {"hang_tb": b["hang_tb"], "so_tran": b["so_tran"]}
        else:
            pool = sorted(final, key=lambda u: (E.champ(u).get("gia", 1), u not in core))
            units, src = pool[:lv], None
        stages.append(_stage(f"Cấp {lv}", lv, _round_for_level(cum, lv, comp["kieu"]), units, final, core,
                             embl, final_holder, cid, src, locked))
    lv_end = max(comp.get("cap_muc_tieu", 8), len(final)) if comp["kieu"] != "reroll" else len(final)
    stages.append(_stage("Hoàn chỉnh", lv_end, _round_for_level(cum, min(lv_end, 9), comp["kieu"]), final, final, core,
                         embl, final_holder, cid, None, locked))
    return {"cum": cid, "khop": round(j, 2), "giai_doan": stages,
            "nguon": "MetaTFT (Bạch Kim+, 3 ngày, 18.3b)" if cum else "ước tính từ đội hoàn chỉnh (chưa có số liệu MetaTFT)"}


def _stage(label, lv, rnd, units, final, core, emblems, final_holder, cid, src, locked: dict | None = None) -> dict:
    locked = locked if locked is not None else {}
    units = list(dict.fromkeys(units))
    keep = [u for u in units if u in final]
    temp = [u for u in units if u not in final]
    missing = [u for u in final if u not in units and u in core]
    an = []
    taken: set[str] = set()
    for e in emblems:
        t = emblem_trait(e)
        if not t:
            continue
        fh = final_holder.get(e)
        cands = [u for u in units if t not in E.champ(u).get("toc_he", []) and u not in taken]
        if not cands:
            continue
        before = counts(units)[t]
        opens = tiers(t, before + 1) > tiers(t, before)
        if locked.get(e) in cands:
            who, tam = locked[e], False      # đã đeo cho tướng giữ tới cuối từ giai đoạn trước → Ấn ở yên đó
        elif fh in cands:
            who, tam = fh, False
        else:
            # chưa có người cầm cuối → đeo tạm cho tướng "tạm" (bán sau, Ấn tự về hàng chờ);
            # không có tướng tạm thì chỉ đeo khi mở được mốc mới (đeo cho tướng giữ tới cuối), còn không thì cất Ấn chờ
            tmp = sorted([u for u in cands if u in temp], key=lambda u: E.champ(u).get("gia", 1))
            if tmp:
                who, tam = tmp[0], True
            elif opens or fh is None:
                who = sorted(cands, key=lambda u: (u not in core, -E.champ(u).get("gia", 1)))[0]
                tam = False
            else:
                who, tam = None, False
        if who:
            taken.add(who)
            if not tam:
                locked.setdefault(e, who)
        an.append({"an": e, "toc_he": t, "nguoi_deo": who, "tam": tam, "chuyen_cho": fh if (tam or who is None) else None,
                   "truoc": before, "sau": before + 1 if who else before, "len_moc": bool(who) and opens})
    extra = [x["toc_he"] for x in an if x["nguoi_deo"]]
    traits = [t for t in E.board_traits(units) if t["kich_hoat"]]
    if extra:
        cnt = counts(units, extra)
        traits = [{"id": t, "ten": trait_name(t), "so": n, "kich_hoat": tiers(t, n) > 0} for t, n in cnt.items()
                  if tiers(t, n) > 0]
        traits.sort(key=lambda x: -x["so"])
    return {"ten": label, "cap": lv, "vong": rnd, "tuong": units, "giu": keep, "tam": temp, "thieu": missing,
            "ban_co": place(units, cid), "toc_he": traits, "an": an, "so_lieu": src}


# ============================================================================ tối ưu Ấn theo mốc tộc/hệ


def _main_traits(units: list[str]) -> list[str]:
    cnt = counts(units)
    return sorted((t for t in cnt if len(trait_moc(t)) > 1 and tiers(t, cnt[t])),
                  key=lambda t: (-tiers(t, cnt[t]), -cnt[t]))[:3]


def _weights(units: list[str], emb_traits: list[str]) -> dict[str, float]:
    w = {}
    main = _main_traits(units)
    for t in E.data()["trait"]:
        moc = trait_moc(t)
        w[t] = 0.3 if moc == [1] else 1.0
    for t in main:
        w[t] = 2.0
    for t in emb_traits:
        w[t] = 2.0
    return w


def _value(units: list[str], extra: list[str], w: dict[str, float]) -> float:
    cnt = counts(units, extra)
    # mốc càng cao càng đáng giá (mốc k = 1+2+…+k) → không đổi 1 mốc cao của tộc chính lấy 2 mốc nhỏ
    return sum(w.get(t, 1.0) * tiers(t, n) * (tiers(t, n) + 1) / 2 for t, n in cnt.items())


def _assign(units: list[str], emblems: list[str], core: list[str]) -> dict[str, str]:
    """Ai đeo Ấn: ưu tiên chủ lực / đỡ đòn chưa có tộc đó, rồi tới tướng đắt nhất."""
    taken, out = set(), {}
    for e in emblems:
        t = emblem_trait(e)
        if not t:
            continue
        cands = [u for u in units if t not in E.champ(u).get("toc_he", []) and u not in taken]
        if not cands:
            continue
        who = sorted(cands, key=lambda u: (core.index(u) if u in core else 99, -E.champ(u).get("gia", 1)))[0]
        taken.add(who)
        out[e] = who
    return out


def _diff(units_a, extra_a, units_b, extra_b) -> list[str]:
    a, b = counts(units_a, extra_a), counts(units_b, extra_b)
    out = []
    for t in sorted(set(a) | set(b), key=lambda t: -(b[t] - a[t])):
        ta, tb = tiers(t, a[t]), tiers(t, b[t])
        if ta != tb and trait_moc(t) != [1]:
            moc = trait_moc(t)
            if tb > ta:
                out.append(f"{trait_name(t)} {a[t]} → {b[t]} (lên mốc {moc[tb - 1]})")
            else:
                out.append(f"{trait_name(t)} {a[t]} → {b[t]} (mất mốc {moc[ta - 1]})")
    return out


def emblem_plan(units: list[str], emblems: list[str], core: list[str], level: int = 8) -> dict:
    """Đội + Ấn đang có → ai đeo, mốc nào mở, và cách thay/thêm 1 tướng để lên mốc cao hơn ở cấp `level`."""
    units = [u for u in dict.fromkeys(units) if u in E.data()["champ"]]
    core = [u for u in core if u in units]
    board = units[:level] if len(units) >= level else list(units)
    # giữ chủ lực/đỡ đòn trong đội dù danh sách dài hơn số ô
    for u in core:
        if u not in board:
            drop = next((x for x in reversed(board) if x not in core), None)
            if drop:
                board[board.index(drop)] = u
    holders = _assign(board, emblems, core)
    extra = [emblem_trait(e) for e in holders]
    emb_traits = [t for t in (emblem_trait(e) for e in emblems) if t]
    w = _weights(board, emb_traits)
    base = _value(board, extra, w)
    keep_traits = set(_main_traits(board)) | set(emb_traits)
    cnt0 = counts(board, extra)
    max_cost = 4 if level <= 8 else 5
    pool = [c["id"] for c in E.data()["tuong"] if c["gia"] <= max_cost and c["id"] not in board
            and c.get("toc_he")]
    moves = []
    removable = [u for u in board if u not in core and u not in holders.values()]
    options = []
    if len(board) < level:
        options += [(None, c) for c in pool]
    options += [(r, c) for r in removable for c in pool]
    for r, c in options:
        nb = [x for x in board if x != r] + [c]
        h2 = _assign(nb, emblems, core)
        ex2 = [emblem_trait(e) for e in h2]
        v = _value(nb, ex2, w)
        cnt1 = counts(nb, ex2)
        if any(tiers(t, cnt1[t]) < tiers(t, cnt0[t]) for t in keep_traits):
            continue  # không bao giờ hy sinh mốc của tộc/hệ chính hoặc tộc của Ấn
        if v >= base + 1:
            gain_emb = any(tiers(t, counts(nb, ex2)[t]) > tiers(t, counts(board, extra)[t]) for t in emb_traits)
            moves.append({"bo": r, "them": c, "diem": round(v - base, 2), "mo_moc_an": gain_emb,
                          "doi": _diff(board, extra, nb, ex2), "nguoi_deo": h2})
    moves.sort(key=lambda m: (-m["mo_moc_an"], -m["diem"], E.champ(m["them"]).get("gia", 1),
                              E.champ(m["bo"]).get("gia", 1) if m["bo"] else 0))
    # bỏ gợi ý trùng (cùng tướng thêm, cùng kết quả)
    seen, uniq = set(), []
    for m in moves:
        k = (m["them"], tuple(m["doi"]))
        if k not in seen:
            seen.add(k)
            uniq.append(m)
    cnt = counts(board, extra)
    an = []
    for e in emblems:
        t = emblem_trait(e)
        if not t:
            continue
        who = holders.get(e)
        n0 = counts(board)[t]
        n1 = cnt[t]
        moc = trait_moc(t)
        nxt = next((m for m in moc if m > n1), None)
        an.append({"an": e, "toc_he": t, "nguoi_deo": who, "truoc": n0, "sau": n1 if who else n0,
                   "moc": moc, "moc_dat": moc[tiers(t, n1) - 1] if tiers(t, n1) else 0, "moc_tiep": nxt,
                   "len_moc": bool(who) and tiers(t, n1) > tiers(t, n0),
                   "khong_ai_deo": who is None})
    traits = sorted(({"id": t, "ten": trait_name(t), "so": n, "moc_dat": trait_moc(t)[tiers(t, n) - 1]}
                     for t, n in cnt.items() if tiers(t, n) and trait_moc(t) != [1]), key=lambda x: (-x["moc_dat"], -x["so"]))
    return {"cap": level, "doi": board, "nguoi_deo": holders, "an": an, "toc_he": traits, "goi_y": uniq[:3]}


def an_comp_units(c: dict) -> tuple[list[str], list[str]]:
    """Đội của trang CHỌN ẤN (Excel) → (tướng, tướng chủ chốt theo thứ tự chủ lực, phụ, đỡ đòn)."""
    units = [x for x in (E.champ_id(n) for n in c["tuong"]) if x]
    core = [x for x in (E.champ_id(c[k]["tuong"]) for k in ("chu_luc", "chu_luc_phu", "do_don")) if x]
    for u in core:
        if u not in units:
            units.append(u)
    return units, core


def emblem_holder_early(c: dict, emblems: list[str]) -> list[dict]:
    """Giai đoạn đầu (cấp 4–6): tướng nào cầm Ấn tạm cho hợp lý."""
    units, core = an_comp_units(c)
    cid, _ = cluster_for(units)
    cum = _details()["cum"].get(cid) if cid else None
    out = []
    locked: dict[str, str] = {}
    for lv in (4, 5, 6):
        boards = (cum or {}).get("som", {}).get(str(lv), [])
        if not boards:
            continue
        b = max(boards, key=lambda x: (len(set(x["tuong"]) & set(units)), -x["hang_tb"]))
        st = _stage(f"Cấp {lv}", lv, _round_for_level(cum, lv, ""), b["tuong"], units, set(core),
                    emblems, dict(_assign(units, emblems, core)), cid, {"hang_tb": b["hang_tb"], "so_tran": b["so_tran"]},
                    locked)
        out.append(st)
    return out


# ============================================================================ đồ tốt nhất từng tướng


def best_items(cid: str) -> dict | None:
    return _details()["do_tuong"].get(cid)


# ============================================================================ phân tích bản cập nhật

TREND = {"↑": 2.0, "↗": 1.0, "→": 0.0, "↘": -1.0, "↓": -2.0}


def _num(s: str) -> float | None:
    try:
        return float(s.replace(",", "."))
    except (TypeError, ValueError, AttributeError):
        return None


def parse_vn(s: str) -> dict:
    m1 = re.search(r"hạng TB ([\d.,]+)", s or "")
    m2 = re.search(r"top 4 ([\d.,]+)%", s or "")
    m3 = re.search(r"([\d.,]+)% người chơi", s or "")
    return {"hang_tb": _num(m1.group(1)) if m1 else None, "top4": _num(m2.group(1)) if m2 else None,
            "ti_le": _num(m3.group(1)) if m3 else None}


def trend_of(s: str) -> float:
    s = (s or "").strip()
    v = TREND.get(s[:1], 0.0)
    if v == 0 and "MẠNH LÊN" in s.upper():
        v = 0.5
    return v


@lru_cache(maxsize=None)
def patch_rows() -> list[dict]:
    rows = []
    for c in E.data()["hd_an"]["doi_hinh"]:
        units, core = an_comp_units(c)
        vn = parse_vn(c["so_lieu_vn"])
        tr = trend_of(c["ban_moi"])
        cid, j = cluster_for(units, 0.4)
        mt = next((r["so_lieu"] for r in E.data()["metatft_doi_hinh"] if r["id"] == f"c{cid}"), None) if cid else None
        h = vn["hang_tb"] or 4.5
        ti = vn["ti_le"] or 0
        score = h - 0.12 * tr + (0.15 if ti >= 3 else 0) + (0.25 if ti < 0.15 else 0)
        rows.append({"ten": c["ten"], "tuong": units, "chu_luc": core[:1], "vn": vn, "xu_huong": tr,
                     "ban_moi": c["ban_moi"], "metatft": mt,
                     "do_kho": "", "diem": round(score, 2),
                     "mau_nho": ti < 0.15, "tranh_nhieu": ti >= 3})
    return rows


CATEGORIES = [
    ("nen_choi", "Nên chơi nhất ở 18.4", "Tổng hợp: hạng TB VN 18.3b, xu hướng 18.4, độ tranh và cỡ mẫu."),
    ("duoc_loi", "Được lợi ở bản 18.4", "Được tăng sức mạnh hoặc không bị đụng trong khi đội khác bị giảm."),
    ("manh_nhat", "Mạnh nhất hiện tại (VN 18.3b)", "Hạng TB thấp nhất, chỉ tính đội có ≥ 0,3% người chơi."),
    ("de_top1", "Dễ top 1", "Tỉ lệ về nhất cao nhất (MetaTFT quốc tế, Bạch Kim+)."),
    ("de_top4", "Dễ vào top 4 (ổn định)", "Tỉ lệ top 4 VN cao nhất, ≥ 0,2% người chơi."),
    ("an_spam", "Mạnh mà ít người chơi — có thể spam", "Hạng TB ≤ 3,35 nhưng dưới 0,5% người chơi, không bị giảm ở 18.4."),
    ("de_choi", "Dễ chơi (hợp leo hạng đều)", "Excel v1.8 đánh giá độ khó “Dễ” — ít phải xoay, đồ dễ ghép."),
    ("nen_tranh", "Nên tránh / cẩn thận", "Bị giảm ở 18.4, bị tranh rất nhiều (≥ 3% người chơi) hoặc đang yếu."),
]


def _easy_rows() -> list[dict]:
    order = {"S": 0, "A": 1, "B": 2, "C": 3}
    out = []
    for c in sorted((c for c in E.comps() if c.get("do_kho") == "Dễ"), key=lambda c: order.get(c["hang"], 9)):
        vn = c.get("so_lieu_vn") or {}
        out.append({"ten": c["ten"], "tuong": c["tuong"], "chu_luc": [r["tuong"] for r in c["chu_luc"][:1]],
                    "vn": {"hang_tb": _num(str(vn.get("hang_tb", ""))), "top4": _num(str(vn.get("top4", "")).rstrip("%")),
                           "ti_le": _num(str(vn.get("ti_le", "")).rstrip("%"))},
                    "xu_huong": 0.0, "ban_moi": f"Bậc {c['hang']} · {c['kieu_ten']}", "metatft": c.get("so_lieu"),
                    "do_kho": "Dễ", "diem": None, "mau_nho": False, "tranh_nhieu": False})
    return out


def patch_analysis() -> dict[str, list[dict]]:
    rows = patch_rows()
    h = lambda r: r["vn"]["hang_tb"] or 9
    out = {
        "nen_choi": sorted([r for r in rows if r["xu_huong"] >= -1], key=lambda r: r["diem"])[:5],
        "duoc_loi": sorted([r for r in rows if r["xu_huong"] > 0], key=lambda r: (-r["xu_huong"], h(r))),
        "manh_nhat": sorted([r for r in rows if (r["vn"]["ti_le"] or 0) >= 0.3], key=h)[:3],
        "de_top1": sorted([r for r in rows if r["metatft"]], key=lambda r: -r["metatft"]["top1"])[:3],
        "de_top4": sorted([r for r in rows if (r["vn"]["ti_le"] or 0) >= 0.2 and r["vn"]["top4"]],
                          key=lambda r: -r["vn"]["top4"])[:3],
        "an_spam": sorted([r for r in rows if h(r) <= 3.35 and (r["vn"]["ti_le"] or 0) < 0.5 and r["xu_huong"] >= 0],
                          key=h)[:4],
        "de_choi": _easy_rows(),
        "nen_tranh": sorted([r for r in rows if r["xu_huong"] <= -2 or r["tranh_nhieu"] or h(r) >= 4.5
                             or "TẮT" in r["ten"].upper()], key=lambda r: (r["xu_huong"], -h(r))),
    }
    return out


def patch_changes() -> list[dict]:
    """Danh sách tăng/giảm của bản mới, kèm id để hiện ảnh."""
    d = E.data()
    by_en = {E.norm(c.get("ten_en", "")): c["id"] for c in d["tuong"]}
    out = []
    for x in d["ban_cap_nhat"]["thay_doi"]:
        ref = None
        if x["loai"] == "tuong":
            ref = E.champ_id(x["ten"]) or by_en.get(E.norm(x["ten"]))
        elif x["loai"] == "toc_he":
            ref = d["trait_by_name"].get(E.norm(x["ten"]))
        elif x["loai"] == "loi":
            ref = d["aug_by_name"].get(E.norm(x["ten"]))
        out.append({**x, "ref": ref})
    return out
