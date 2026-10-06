# ĐTCL Coach v1.1 (2026-10-06) — bộ não tính toán (luật viết trong code, không dùng AI)
"""
Mọi phép tính của web nằm ở đây, không phụ thuộc Streamlit → kiểm thử dễ.
Nguồn nội dung chính: file Excel hướng dẫn v1.8 của anh Peach (data/hd_*.json).
Số liệu bổ sung: Community Dragon (tướng/đồ/lõi bản Việt), MetaTFT (thống kê quốc tế).

  - ghép đồ:            combine(), recipe_table(), buildable()
  - kinh tế:            interest(), income(), xp_to_next(), shop_odds(), roll_estimate()
  - đội hình:           comps(), comp_by_id(), template_board(), board_traits()
  - trợ lý ván đấu:     score_comps(), pace_advice(), roll_or_level(), rank_augments(), item_plan(), advise()
  - ấn → đội hình:      emblem_rank()   (đúng công thức trang CHỌN ẤN của Excel)
  - lõi → cách đánh:    aug_plan()      (đúng bảng trang LÕI → CÁCH ĐÁNH)
  - luyện tập, nhật ký: quiz_pick(), quiz_score(), stats_by(), best_fit()
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from functools import lru_cache

from core import config

FILES = ("tuong", "toc_he", "trang_bi", "loi", "metatft_doi_hinh", "kinh_te", "cau_hoi", "meo", "meta",
         "hd_doi_hinh", "hd_an", "hd_loi", "hd_nhip", "hd_kien_thuc", "metatft_chi_tiet", "anh_phu", "ban_cap_nhat")

# tên gọi khác trong Excel / GGMeo → tên trong dữ liệu game
ITEM_ALIAS = {"Kiếm BF": "Kiếm B.F.", "Xẻng Vàng": "Siêu Xẻng", "Gậy": "Gậy Quá Khổ", "Nước Mắt": "Nước Mắt Nữ Thần",
              "Áo Choàng": "Áo Choàng Bạc", "Đai": "Đai Khổng Lồ", "Găng": "Găng Đấu Tập", "Xẻng": "Siêu Xẻng"}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFC", str(s or "")).lower().strip()
    return re.sub(r"\s+", " ", s)


# ============================================================================ dữ liệu


@lru_cache(maxsize=None)
def data() -> dict:
    d = {n: config.load_json(f"{n}.json") for n in FILES}
    d["champ"] = {c["id"]: c for c in d["tuong"]}
    d["champ_by_name"] = {norm(c["ten"]): c["id"] for c in d["tuong"]}
    d["trait"] = {t["id"]: t for t in d["toc_he"]}
    d["trait_by_name"] = {norm(t["ten"]): t["id"] for t in d["toc_he"]}
    d["aug"] = {a["id"]: a for a in d["loi"]}
    d["aug_by_name"] = {norm(a["ten"]): a["id"] for a in d["loi"]}
    items = {}
    for grp in ("thanh_phan", "hoan_chinh", "an"):
        for it in d["trang_bi"][grp]:
            items[it["id"]] = {**it, "loai": grp}
    d["item"] = items
    d["item_by_name"] = {norm(i["ten"]): i["id"] for i in items.values()}
    for a, b in ITEM_ALIAS.items():
        d["item_by_name"].setdefault(norm(a), d["item_by_name"].get(norm(b)))
    # bổ sung mô tả / tướng nên cầm từ Excel
    for x in d["hd_kien_thuc"].get("trang_bi", []):
        iid = d["item_by_name"].get(norm(x["ten"]))
        if iid:
            items[iid]["excel"] = x
    tex = {norm(t["ten"]): t for t in d["hd_kien_thuc"].get("toc_he", [])}
    for t in d["toc_he"]:
        t["excel"] = tex.get(norm(t["ten"]))
    d["comps"] = _build_comps(d)
    d["comp"] = {c["id"]: c for c in d["comps"]}
    return d


def champ_id(name: str) -> str | None:
    return data()["champ_by_name"].get(norm(name))


def item_id(name: str) -> str | None:
    return data()["item_by_name"].get(norm(name))


def aug_ids_from_text(text: str, by: dict | None = None) -> list[str]:
    """'Thợ Rèn Kiếm / Đam Mê Kiếm (+2 bậc)' → id các lõi khớp tên."""
    out = []
    by = by if by is not None else data()["aug_by_name"]
    for part in re.split(r"/|,", re.sub(r"\(.*?\)", "", str(text))):
        k = norm(part).rstrip(".")
        if k in by:
            out.append(by[k])
    return out


def champ(cid: str) -> dict:
    return data()["champ"].get(cid, {"id": cid, "ten": cid, "gia": 1, "toc_he": [], "tam_danh": 1, "anh": ""})


def item(iid: str) -> dict:
    return data()["item"].get(iid, {"id": iid, "ten": iid, "cong_thuc": [], "anh": "", "loai": "?"})


def item_name(iid: str) -> str:
    return item(iid)["ten"]


COMPONENTS = ["BFSword", "RecurveBow", "NeedlesslyLargeRod", "TearOfTheGoddess", "ChainVest",
              "NegatronCloak", "GiantsBelt", "SparringGloves", "Spatula", "FryingPan"]

# ============================================================================ đội hình (từ Excel)
STYLE_KEYS = {
    ("fast8", 8): "Lên 8 nhanh (tướng 4 vàng)", ("fast9", 9): "Lên 9 nhanh (tướng 5 vàng)",
    ("reroll", 5): "Săn 3 sao tướng 1 vàng", ("reroll", 6): "Săn 3 sao tướng 2 vàng", ("reroll", 7): "Săn 3 sao tướng 3 vàng",
}


def parse_style(text: str) -> tuple[str, int]:
    t = norm(text)
    if "lên 9" in t:
        return "fast9", 9
    if "lên 8" in t:
        return "fast8", 8
    if "săn 3 sao" in t:
        if "1 vàng" in t:
            return "reroll", 5
        if "1–2" in t or "1-2" in t or "2 vàng" in t:
            return "reroll", 6
        return "reroll", 7
    return "fast8", 8


def _ids(names):
    out = []
    for n in names:
        cid = data_champ_lookup(n)
        if cid and cid not in out:
            out.append(cid)
    return out


_CHAMP_LOOKUP: dict = {}


def data_champ_lookup(name: str) -> str | None:
    return _CHAMP_LOOKUP.get(norm(name))


def _items(names):
    return [i for i in (_ITEM_LOOKUP.get(norm(n)) for n in names) if i]


_ITEM_LOOKUP: dict = {}


def _build_comps(d) -> list[dict]:
    _CHAMP_LOOKUP.clear()
    _CHAMP_LOOKUP.update(d["champ_by_name"])
    _ITEM_LOOKUP.clear()
    _ITEM_LOOKUP.update({k: v for k, v in d["item_by_name"].items() if v})
    vn_rows = d["hd_kien_thuc"]["may_chu"]["vn"]["dong"]
    mt = d["metatft_doi_hinh"]
    out = []
    for i, c in enumerate(d["hd_doi_hinh"]["doi_hinh"], 1):
        kieu, cap = parse_style(c["loi_choi"])
        units = _ids(c["tuong"])
        roles = []
        for key, label in (("chu_luc", "Chủ lực chính"), ("chu_luc_phu", "Chủ lực phụ"), ("do_don", "Đỡ đòn")):
            cid = data_champ_lookup(c[key]["tuong"])
            if cid:
                roles.append({"tuong": cid, "do": _items(c[key]["do"]), "vai": label, "ghi_chu": c[key]["ghi_chu"]})
                if cid not in units:
                    units.append(cid)
        loi = []
        for t in c["loi_khuyen_dung"]:
            loi += [a for a in aug_ids_from_text(t, d["aug_by_name"]) if a not in loi]
        comp = {
            "id": f"d{i:02d}", "ten": c["ten"], "hang": c["hang"], "kieu": kieu, "kieu_ten": c["loi_choi"],
            "cap_muc_tieu": cap, "do_kho": c["do_kho"], "tuong": units,
            "chu_luc": [r for r in roles if r["vai"] != "Đỡ đòn"], "do_don": [r for r in roles if r["vai"] == "Đỡ đòn"],
            "loi_hop": loi, "loi_text": c["loi_khuyen_dung"], "excel": c,
        }
        comp["toc_he"] = [t for t in board_traits_d(d, units) if t["kich_hoat"]]
        comp["so_lieu_vn"] = _match_vn(d, units, vn_rows)
        comp["so_lieu"] = _match_metatft(units, mt)
        out.append(comp)
    order = {"S": 0, "A": 1, "B": 2, "C": 3}
    out.sort(key=lambda x: (order.get(x["hang"], 9), x["excel"]["thu_tu"] or 99))
    return out


def _match_vn(d, units, rows):
    best, score = None, 0.0
    us = set(units)
    for r in rows:
        names = [x.strip() for x in str(r[6]).split(",")]
        ids = {d["champ_by_name"].get(norm(n)) for n in names} - {None}
        if not ids:
            continue
        s = len(us & ids) / min(len(us), len(ids))
        if s > score:
            best, score = r, s
    if best and score >= 0.75:
        return {"ten": best[1], "bac": best[2], "hang_tb": best[3], "top4": best[4], "ti_le": best[5],
                "nguon": "OP.GG · máy chủ VN · bản 18.3b (Excel v1.8)"}
    return None


def _match_metatft(units, rows):
    best, score = None, 0.0
    us = set(units)
    for r in rows:
        s = set(r["tuong"])
        j = len(us & s) / len(us | s) if us | s else 0
        if j > score:
            best, score = r, j
    if best and score >= 0.45:
        return {**best["so_lieu"], "ten_cum": best["ten"]}
    return None


def comps(tiers=("S", "A", "B", "C")) -> list[dict]:
    return [c for c in data()["comps"] if c["hang"] in tiers]


def comp_by_id(cid: str) -> dict | None:
    return data()["comp"].get(cid)


def comp_by_name(name: str) -> dict | None:
    n = norm(name)
    for c in data()["comps"]:
        if norm(c["ten"]) == n:
            return c
    return None


# ============================================================================ ghép đồ


@lru_cache(maxsize=None)
def _recipes() -> dict[frozenset, str]:
    out = {}
    for it in data()["item"].values():
        rec = it.get("cong_thuc") or []
        if it["loai"] in ("hoan_chinh", "an") and len(rec) == 2:
            out[frozenset(Counter(rec).items())] = it["id"]
    return out


def combine(a: str, b: str) -> dict | None:
    """2 mảnh → trang bị hoàn chỉnh (hoặc Ấn). None nếu không ghép được."""
    iid = _recipes().get(frozenset(Counter([a, b]).items()))
    return item(iid) if iid else None


def recipe_table() -> list[list[str | None]]:
    return [[(combine(a, b) or {}).get("id") for b in COMPONENTS] for a in COMPONENTS]


def users_of(iid: str) -> list[dict]:
    """Đội hình (Excel) nào dùng món này và cho ai."""
    out = []
    for c in comps():
        for r in c["chu_luc"] + c["do_don"]:
            if iid in r["do"]:
                out.append({"comp": c, "tuong": r["tuong"], "vai": r["vai"]})
    return out


def comps_for_component(part: str) -> list[dict]:
    """Mảnh đồ khởi đầu → đội hình hợp (đồ của chủ lực/đỡ đòn dùng mảnh đó)."""
    res = []
    for c in comps():
        hit = sorted({item_name(i) for r in c["chu_luc"] + c["do_don"] for i in r["do"] if part in item(i).get("cong_thuc", [])})
        if hit:
            res.append({"comp": c, "do": hit})
    return res


def buildable(targets: list[str], parts: list[str]) -> tuple[list[str], list[str]]:
    pool = Counter(parts)
    made = []
    for t in targets:
        rec = item(t).get("cong_thuc") or []
        if len(rec) != 2:
            continue
        need = Counter(rec)
        if all(pool[k] >= v for k, v in need.items()):
            pool -= need
            made.append(t)
    return made, list(pool.elements())


def parts_of(items: list[str]) -> list[str]:
    out = []
    for i in items:
        rec = item(i).get("cong_thuc") or []
        out += rec if rec else ([i] if i in COMPONENTS else [])
    return out


def item_lean(parts: list[str], items: list[str] = ()) -> int:
    """0 = cân bằng, 1 = vật lý, 2 = phép, 3 = đỡ đòn (đúng thứ tự Excel)."""
    p = Counter(parts + parts_of(list(items)))
    ad = p["BFSword"] + p["RecurveBow"] + p["SparringGloves"]
    ap = p["NeedlesslyLargeRod"] + p["TearOfTheGoddess"]
    tk = p["ChainVest"] + p["NegatronCloak"] + p["GiantsBelt"]
    top = max(ad, ap, tk)
    if top == 0 or [ad, ap, tk].count(top) > 1:
        return 0
    return 1 + [ad, ap, tk].index(top)


# ============================================================================ kinh tế


def interest(gold: int) -> int:
    k = data()["kinh_te"]["lai"]
    return max(0, min(int(gold) // 10 * k["moi_10_vang"], k["toi_da"]))


def streak_bonus(streak: int) -> int:
    s = abs(int(streak))
    for row in data()["kinh_te"]["chuoi"]:
        if row["tu"] <= s <= row["den"]:
            return row["vang"]
    return 0


def income(gold: int, streak: int = 0, won: bool = False) -> dict:
    k = data()["kinh_te"]
    parts = {"co_ban": k["thu_nhap_co_ban"], "lai": interest(gold), "chuoi": streak_bonus(streak),
             "thang": k["thang_pvp"] if won else 0}
    parts["tong"] = sum(parts.values())
    return parts


def xp_to_next(level: int) -> int:
    return int(data()["kinh_te"]["xp_len_cap"].get(str(level + 1), 0))


def shop_odds(level: int) -> list[int]:
    return data()["kinh_te"]["ti_le_cua_hang"][str(max(1, min(10, int(level))))]


def gold_to_level(level: int, xp_now: int = 0) -> int:
    need = max(0, xp_to_next(level) - int(xp_now))
    return -(-need // 4) * 4


def roll_estimate(level: int, cost: int, copies_left: int) -> dict:
    """Máy tính đổi tướng (đúng công thức Excel): tỉ lệ 1 ô ra đúng tướng = tỉ lệ cấp × bản còn lại ÷ (bản mỗi tướng × số tướng cùng giá)."""
    k = data()["kinh_te"]
    p_cost = shop_odds(level)[cost - 1] / 100
    pool = k["so_ban_moi_tuong"][str(cost)] * k["so_tuong_moi_bac"][str(cost)]
    p_slot = p_cost * max(0, copies_left) / pool if pool else 0
    p_roll = 1 - (1 - p_slot) ** 5
    rolls = 1 / p_roll if p_roll > 0 else float("inf")
    return {"ti_le_bac": p_cost, "ti_le_o": p_slot, "ti_le_luot": p_roll, "so_luot": rolls,
            "vang": rolls * 2 + cost if rolls != float("inf") else float("inf")}


# ============================================================================ vòng đấu


def parse_round(s: str) -> tuple[int, int]:
    try:
        a, b = str(s).strip().replace(".", "-").split("-")
        return max(1, int(a)), max(1, int(b))
    except ValueError:
        return 2, 1


def round_index(stage: int, rnd: int) -> float:
    return stage + rnd / 10


# ============================================================================ xếp bàn

ROWS, COLS = 4, 7  # hàng 0 = hàng trên (gần địch), hàng 3 = hàng sau


def board_templates() -> list[dict]:
    return data()["hd_doi_hinh"]["vi_tri"]


def template_board(comp: dict, n: int | None = None, template: str | None = None) -> dict[tuple[int, int], str]:
    """Đặt tướng của đội vào mẫu bàn cờ của Excel (ĐỠ ĐÒN / CHỦ LỰC / CHỦ LỰC 2 / HỖ TRỢ / MỒI).
    Tướng còn thừa xếp theo tầm đánh."""
    units = list(dict.fromkeys(comp["tuong"]))
    n = n or min(len(units), comp.get("cap_muc_tieu", 8))
    tpl_name = template or comp.get("excel", {}).get("mau_ban_co") or "Chủ lực ở góc (chuẩn)"
    tpl = next((t for t in board_templates() if t["ten"] == tpl_name), board_templates()[0])
    main = [r["tuong"] for r in comp.get("chu_luc", [])]
    tanks = [r["tuong"] for r in comp.get("do_don", [])]
    pick = list(dict.fromkeys(main + tanks + units))[:n]
    rest = [u for u in pick if u not in main + tanks]
    melee = [u for u in rest if champ(u).get("tam_danh", 1) <= 1]
    ranged = [u for u in rest if champ(u).get("tam_danh", 1) > 1]
    tank_q = tanks + melee
    support_q = sorted(ranged, key=lambda u: -champ(u).get("gia", 1))
    bait_q = sorted(rest, key=lambda u: champ(u).get("gia", 1))
    board: dict[tuple[int, int], str] = {}
    used: set[str] = set()

    def take(q):
        while q:
            u = q.pop(0)
            if u not in used:
                used.add(u)
                return u
        return None

    for r in range(ROWS):
        for c in range(COLS):
            lab = tpl["luoi"][r][c]
            u = None
            if "CHỦ LỰC 2" in lab:
                u = take([main[1]] if len(main) > 1 else []) or take(support_q)
            elif "CHỦ LỰC" in lab:
                u = take(main[:1])
            elif "ĐỠ ĐÒN" in lab:
                u = take(tank_q)
            elif "HỖ TRỢ" in lab:
                u = take(support_q) or take(tank_q)
            elif "MỒI" in lab:
                u = take(bait_q)
            if u:
                board[(r, c)] = u
    # còn tướng chưa đặt → xếp theo tầm đánh
    left = [u for u in pick if u not in used]
    order_rows = {True: [0, 1, 2, 3], False: [3, 2, 1, 0]}
    for u in left:
        melee_u = champ(u).get("tam_danh", 1) <= 1
        placed = False
        for r in order_rows[melee_u]:
            for c in (3, 2, 4, 1, 5, 0, 6):
                if (r, c) not in board:
                    board[(r, c)] = u
                    placed = True
                    break
            if placed:
                break
    return board


def board_traits_d(d, units: list[str]) -> list[dict]:
    cnt = Counter()
    for u in dict.fromkeys(units):
        for t in d["champ"].get(u, {}).get("toc_he", []):
            cnt[t] += 1
    out = []
    for t, n in cnt.items():
        tr = d["trait"].get(t)
        if not tr:
            continue
        mins = [m for m in tr["moc"] if m]
        active = [m for m in mins if n >= m]
        nxt = next((m for m in mins if m > n), None)
        out.append({"id": t, "ten": tr["ten"], "so": n, "moc_dat": active[-1] if active else 0,
                    "moc_tiep": nxt, "kich_hoat": bool(active), "anh": tr["anh"]})
    out.sort(key=lambda x: (not x["kich_hoat"], -x["moc_dat"], -x["so"]))
    return out


def board_traits(units: list[str]) -> list[dict]:
    return board_traits_d(data(), units)


# ============================================================================ trợ lý ván đấu
TIER_BONUS = {"S": 10, "A": 6, "B": 3, "C": 0}
HP_BUCKETS = ["Trên 70 máu", "Từ 40 đến 70 máu", "Dưới 40 máu"]
STREAK_KEYS = {1: "Đang THẮNG liên tiếp", -1: "Đang THUA liên tiếp", 0: "Thắng/thua xen kẽ"}


@dataclass
class GameState:
    units: list[str] = field(default_factory=list)       # tướng đang có (bàn + hàng chờ)
    parts: list[str] = field(default_factory=list)       # mảnh đồ đang giữ
    items: list[str] = field(default_factory=list)       # đồ hoàn chỉnh đã ghép (kể cả Ấn)
    augments: list[str] = field(default_factory=list)    # lõi đã chọn
    offered: list[str] = field(default_factory=list)     # 3 lõi đang hiện (nếu có)
    hp: int = 100
    gold: int = 0
    level: int = 4
    stage: int = 2
    rnd: int = 1
    streak: int = 0                                      # + chuỗi thắng, − chuỗi thua (số trận)


def _comp_item_targets(comp: dict) -> list[str]:
    return [i for r in comp.get("chu_luc", []) + comp.get("do_don", []) for i in r["do"]]


def _emblem_gain(comp: dict, emblems: list[str]) -> tuple[float, list[str]]:
    """Ấn giúp đội vượt mốc tộc/hệ không? (đếm lại tộc/hệ khi đeo cho 1 tướng chưa có tộc đó)."""
    if not emblems:
        return 0.0, []
    base = Counter()
    for u in comp["tuong"]:
        for t in champ(u).get("toc_he", []):
            base[t] += 1
    pts, why = 0.0, []
    for e in emblems:
        t = item(e).get("toc_he")
        tr = data()["trait"].get(t)
        if not tr:
            continue
        n = base[t]
        mins = [m for m in tr["moc"] if m]
        if any(n < m <= n + 1 for m in mins):
            pts += 6
            why.append(f"{item_name(e)} mở {tr['ten']} {n + 1}")
        elif n:
            pts += 1.5
        base[t] += 1
    return pts, why


def score_comps(st: GameState, top: int = 3) -> list[dict]:
    """Chấm điểm 19 đội của Excel theo mức khớp tướng / đồ / lõi / ấn đang có. Trả top N kèm lý do."""
    have = set(st.units)
    have_items = Counter(st.items)
    emblems = [i for i in st.items if item(i).get("loai") == "an"]
    t_now = round_index(st.stage, st.rnd)
    res = []
    for comp in comps():
        reasons = []
        units = list(dict.fromkeys(comp["tuong"]))
        carries = [r["tuong"] for r in comp.get("chu_luc", [])]
        w_total = w_have = 0.0
        for u in units:
            w = champ(u).get("gia", 1) + (4 if u in carries else 0)
            w_total += w
            if u in have:
                w_have += w
        s_units = 50 * w_have / w_total if w_total else 0
        owned = [champ(u)["ten"] for u in units if u in have]
        if owned:
            reasons.append(f"Đã có {len(owned)}/{len(units)} tướng: {', '.join(owned[:5])}")
        own_carry = [champ(c)["ten"] for c in carries if c in have]
        if own_carry:
            reasons.append(f"Có sẵn chủ lực {', '.join(own_carry)}")
        targets = _comp_item_targets(comp)
        made, _ = buildable(targets, st.parts)
        tc = Counter(targets)
        match_full = sum(min(v, tc[k]) for k, v in have_items.items())
        need_parts = Counter(parts_of(targets))
        part_hits = sum(min(v, need_parts[k]) for k, v in Counter(st.parts).items())
        s_items = min(25, 6 * match_full + 4 * len(made) + 1.5 * part_hits)
        names = [item_name(i) for i in list(dict.fromkeys([k for k in have_items if tc[k]] + made))][:3]
        if names:
            reasons.append(f"Đồ hợp: {', '.join(names)}")
        hit = [a for a in st.augments if a in comp.get("loi_hop", [])]
        s_aug = min(15, 8 * len(hit))
        if hit:
            reasons.append("Lõi hợp: " + ", ".join(data()["aug"][a]["ten"] for a in hit))
        s_emb, why_emb = _emblem_gain(comp, emblems)
        reasons += why_emb
        s_tier = TIER_BONUS.get(comp["hang"], 0)
        pen = 0
        if comp["kieu"] == "reroll" and t_now >= 4.1 and not own_carry:
            pen = 12
            reasons.append("Đã muộn để bắt đầu săn 3 sao khi chưa có chủ lực")
        if "TẮT" in comp["ten"].upper():
            pen += 30
            reasons.append("Excel ghi lõi chính của đội đang bị tắt")
        score = round(s_units + s_items + s_aug + min(12, s_emb) + s_tier - pen, 1)
        res.append({"comp": comp, "diem": score, "ly_do": reasons,
                    "chi_tiet": {"tuong": round(s_units, 1), "do": round(s_items, 1), "loi": s_aug,
                                 "an": round(min(12, s_emb), 1), "hang": s_tier}})
    res.sort(key=lambda r: (-r["diem"], {"S": 0, "A": 1, "B": 2, "C": 3}.get(r["comp"]["hang"], 9)))
    return res[:top]


def style_key(comp: dict | None) -> str:
    if not comp:
        return STYLE_KEYS[("fast8", 8)]
    return STYLE_KEYS.get((comp["kieu"], comp["cap_muc_tieu"]), STYLE_KEYS[("fast8", 8)])


def pace_row(style: str, stage: int, rnd: int) -> dict | None:
    """Dòng lộ trình của Excel (TRỢ LÝ VÁN ĐẤU) ứng với lối chơi + vòng hiện tại."""
    nh = data()["hd_nhip"]
    plan = next((s["lo_trinh"] for s in nh["loi_choi"] if s["ten"] == style), None)
    if not plan:
        return None
    t = round_index(stage, rnd)
    best = plan[0]
    for row in plan:
        v = row["vong"]
        if v == "1-x":
            k = 1.0
        else:
            a, b = v.replace("+", "").split("-")
            k = round_index(int(a), int(b))
        if t >= k:
            best = row
    return best


def hp_bucket(hp: int) -> str:
    return HP_BUCKETS[0] if hp > 70 else (HP_BUCKETS[1] if hp >= 40 else HP_BUCKETS[2])


def gold_check(gold: int) -> str:
    """Đúng công thức ô 'Kiểm tra vàng' của Excel."""
    if gold < 10:
        return "Vàng rất thấp – ưu tiên tích lãi, không mua Tinh Linh mất phí."
    if gold < 30:
        return f"Đang tích lũy – đừng để tụt mốc {gold // 10 * 10} vàng."
    if gold < 50:
        return "Gần tối đa lãi – cố giữ tới 50 trước khi đổi tướng (nếu máu cho phép)."
    return "Đủ 50+: chỉ dùng phần vàng TRÊN 50 để đổi tướng / mua Tinh Linh."


def pace_advice(st: GameState, comp: dict | None) -> dict:
    nh = data()["hd_nhip"]
    style = style_key(comp)
    row = pace_row(style, st.stage, st.rnd)
    sk = STREAK_KEYS[1 if st.streak >= 2 else (-1 if st.streak <= -2 else 0)]
    hb = hp_bucket(st.hp)
    return {
        "loi_choi": style, "dong": row,
        "chuoi": next((c["loi_khuyen"] for c in nh["chuoi"] if c["ten"] == sk), ""), "chuoi_ten": sk,
        "mau": next((m["loi_khuyen"] for m in nh["mau"] if m["ten"] == hb), ""), "mau_ten": hb,
        "vang": gold_check(st.gold), "lai_vong_toi": min(5, st.gold // 10),
        "can_them": "Đã tối đa (50+)" if st.gold >= 50 else f"+{10 - st.gold % 10} vàng",
        "doi_hinh_hop": next((s["doi_hinh"] for s in nh["loi_choi"] if s["ten"] == style), []),
    }


def roll_or_level(st: GameState, comp: dict | None = None) -> dict:
    """Quyết định chính lúc này: lên cấp / roll / roll chậm / giữ vàng (luật trong code)."""
    kieu = (comp or {}).get("kieu", "fast8")
    cap = (comp or {}).get("cap_muc_tieu", 8)
    t = round_index(st.stage, st.rnd)
    g, lv, hp = int(st.gold), int(st.level), int(st.hp)
    why = []
    lv_cost = gold_to_level(lv)

    def out(action, title):
        return {"hanh_dong": action, "tieu_de": title, "ly_do": why, "lai_hien_tai": interest(g)}

    danger = (hp < 40 and t >= 3.1) or hp <= 20
    if danger and g >= 10:
        why.append(f"Máu {hp} là vùng nguy hiểm — dồn vàng vào sức mạnh ngay, mục tiêu là vào top 4.")
        if kieu in ("fast8", "fast9") and lv < 8 and t >= 4.1 and g >= lv_cost + 20:
            why.append(f"Lên cấp {lv + 1} ({lv_cost} vàng) rồi đổi tướng phần còn lại.")
            return out("len_cap_roi_roll", f"Lên cấp {lv + 1} rồi đổi tướng")
        why.append("Đổi tướng tới khi đội đủ sức thắng / giữ máu; lãi lúc này không còn quan trọng.")
        return out("roll_het", "Đổi tướng mạnh ngay để giữ máu")

    if kieu == "reroll":
        if lv < cap:
            target_t = {5: 2.5, 6: 3.1, 7: 3.5}.get(cap, 3.2)
            if t >= target_t and g >= lv_cost:
                why.append(f"Đội săn 3 sao ở cấp {cap}: cần lên đúng cấp {cap} rồi mới đổi tướng.")
                return out("len_cap", f"Lên cấp {lv + 1}")
            why.append(f"Chưa tới mốc lên cấp {cap} — giữ vàng, tích lãi.")
            return out("giu_vang", "Giữ vàng, chờ mốc")
        if lv > cap:
            if t >= 4.2 and lv < 8 and g >= lv_cost:
                why.append("Đã qua cấp săn 3 sao: theo lộ trình Excel, 4-2 lên 8 tìm tướng 4 vàng hỗ trợ / đỡ đòn.")
                return out("len_cap", f"Lên cấp {lv + 1}")
            if g > 50:
                why.append(f"Đội đã ổn: dùng phần dư {g - 50} vàng để mua kinh nghiệm hoặc đổi tướng nhẹ, giữ mốc 50.")
                return out("mua_xp", "Dùng phần vàng dư, giữ mốc 50")
            why.append("Đội đã qua mốc săn 3 sao: tích lại 50 vàng, chờ mốc lên cấp tiếp theo.")
            return out("giu_vang", "Giữ vàng tới 50")
        if g > 50:
            why.append(f"Đã ở cấp {cap}: đổi tướng từ từ, chỉ tiêu phần trên 50 vàng ({g - 50} vàng).")
            return out("roll_cham", f"Đổi tướng từ từ {g - 50} vàng")
        if t >= 4.1 and g >= 30 and hp <= 50:
            why.append("Giai đoạn 4, máu dưới 50: hạ mốc giữ vàng để lên 3 sao sớm.")
            return out("roll_cham", "Đổi tướng xuống còn khoảng 20 vàng")
        why.append("Dưới 50 vàng: giữ để chạm 50, mỗi vòng chỉ đổi phần dư.")
        return out("giu_vang", "Giữ vàng tới 50")

    plan = {2.1: 4, 2.5: 5, 3.1: 6, 3.5: 7, 4.1: 7, 4.2: 8, 5.2: 9 if kieu == "fast9" else 8}
    if st.streak <= -2:   # chuỗi thua: lộ trình Excel lùi nhịp đầu game, lên 8 sớm ở 4-1
        plan = {2.3: 4, 2.7: 5, 3.2: 6, 3.5: 7, 4.1: 8, 5.2: 9 if kieu == "fast9" else 8}
    want = 3
    for k, v in plan.items():
        if t >= k:
            want = v
    if lv < want and g >= lv_cost:
        why.append(f"Theo lộ trình {style_key(comp)}, vòng {st.stage}-{st.rnd} nên ở cấp {want}.")
        if interest(g - lv_cost) < interest(g):
            why.append(f"Lên cấp tốn {lv_cost} vàng (lãi giảm {interest(g)} → {interest(g - lv_cost)}) — vẫn đáng vì giữ nhịp.")
        return out("len_cap", f"Lên cấp {lv + 1}")
    if lv < want and t >= 3.2 and g >= 4:
        why.append(f"Theo lộ trình {style_key(comp)}, vòng {st.stage}-{st.rnd} nên ở cấp {want}; lên cấp {lv + 1} cần tối đa "
                   f"{lv_cost} vàng (trừ kinh nghiệm đang có).")
        why.append("Bấm mua kinh nghiệm tới khi lên cấp, rồi mới đổi tướng bằng phần vàng còn lại.")
        return out("mua_xp", f"Mua kinh nghiệm lên cấp {lv + 1}")
    spike = (lv >= 8 and t >= 4.2 and kieu == "fast8") or (lv >= 9 and kieu == "fast9")
    if spike and g >= 20:
        keep = 10 if hp <= 50 else 20
        why.append(f"Cấp {lv} ở {st.stage}-{st.rnd} là mốc dồn vàng của đội — tìm chủ lực và đỡ đòn 2 sao.")
        why.append(f"Đổi tướng tới khi chủ lực 2 sao, giữ lại khoảng {keep} vàng.")
        return out("roll", f"Dồn vàng đổi tướng, giữ ~{keep} vàng")
    if g > 50 and lv >= 6:
        why.append(f"Có {g} vàng: dùng phần dư {g - 50} vàng mua kinh nghiệm (giữ mốc 50).")
        return out("mua_xp", "Mua kinh nghiệm bằng phần vàng dư")
    why.append(f"Đang có {g} vàng, lãi {interest(g)}. Giữ vàng để chạm mốc 10 tiếp theo.")
    return out("giu_vang", "Giữ vàng")


@lru_cache(maxsize=None)
def _excel_aug_notes() -> dict[str, dict]:
    """Ghi chú của Excel cho từng lõi (hạng, tắt/bật, lời khuyên) theo id lõi."""
    hl = data()["hd_loi"]
    notes: dict[str, dict] = {}
    for x in hl["loi_manh"]:
        for a in aug_ids_from_text(x["ten"]):
            notes.setdefault(a, {}).update({"hang_excel": x["hang"], "hop_voi": x["hop_voi"], "ghi_chu": x["ghi_chu"]})
    for x in hl["top1"]:
        for a in aug_ids_from_text(x["ten"]):
            notes.setdefault(a, {}).update({"uu_tien": x["uu_tien"], "lam_gi": x["lam_gi"], "doi_hinh_ep": x["doi_hinh"]})
    return notes


def aug_note(aid: str) -> dict:
    return _excel_aug_notes().get(aid, {})


def rank_augments(st: GameState, options: list[str], comp: dict | None = None) -> list[dict]:
    """Xếp các lõi đang hiện. Điểm = hạng (MetaTFT + Excel) + khớp đội + hợp thời điểm + máu."""
    base = {"S": 40, "A": 30, "B": 20, "C": 10}
    t = round_index(st.stage, st.rnd)
    comp_traits = {x["id"] for x in (comp or {}).get("toc_he", [])}
    out = []
    for aid in options:
        a = data()["aug"].get(aid)
        if not a:
            continue
        note = aug_note(aid)
        s, why = base.get(a["xep_hang"], 15), [f"Hạng {a['xep_hang']} (MetaTFT)"]
        he = str(note.get("hang_excel", ""))
        if he:
            why.append(f"Excel: {he}")
            if he.startswith("S"):
                s += 6
        if "TẮT" in he.upper() or "TẮT" in str(note.get("uu_tien", "")).upper():
            s -= 100
            why.append("Excel ghi lõi này đang bị Riot tạm tắt ở 18.3b — kiểm tra trong game")
        if "BẮT BUỘC" in str(note.get("uu_tien", "")):
            s += 10
            why.append(f"Lõi ăn top 1: {note['uu_tien'].lower()} → {note.get('doi_hinh_ep', '')}")
        if comp and aid in comp.get("loi_hop", []):
            s += 15
            why.append(f"Excel khuyên dùng cho {comp['ten']}")
        if a["nhom"] == "Tộc/Hệ":
            if comp and any(tr in aid for tr in comp_traits):
                s += 10
                why.append("Đúng tộc/hệ của đội")
            elif comp and aid not in comp.get("loi_hop", []):
                s -= 20
                why.append("Lõi tộc/hệ không thuộc đội đang đi")
        if a["nhom"] == "Kinh tế":
            if t <= 2.1:
                s += 5
                why.append("2-1: ưu tiên kinh tế / trang bị")
            elif t >= 4.2:
                s -= 10
                why.append("4-2: lõi kinh tế gần như vô nghĩa trừ khi đang lên 9")
        if a["nhom"] == "Chiến đấu" and t >= 4.2:
            s += 8
            why.append("4-2: chọn thứ tăng sức mạnh bàn cờ ngay")
        if a["nhom"] == "Trang bị" and len(st.parts) + len(st.items) * 2 < 4 and t <= 3.2:
            s += 5
            why.append("Đang thiếu đồ")
        if a["nhom"] == "Cấp & Đổi tướng" and comp:
            if comp["kieu"] == "reroll" and any(k in aid for k in ("Roll", "Patience", "Trade", "Commerce", "Pandora")):
                s += 6
                why.append("Lượt đổi miễn phí hợp đội săn 3 sao")
            if comp["kieu"] in ("fast8", "fast9") and any(k in aid for k in ("Growth", "LevelUp", "Epoch", "Rolldown", "LateGame")):
                s += 6
                why.append("Kinh nghiệm / lượt đổi hợp đội lên cấp nhanh")
        if st.hp < 40 and a["nhom"] == "Kinh tế":
            s -= 10
            why.append("Máu dưới 40: bỏ qua lõi kinh tế, chọn lõi dùng được ngay")
        out.append({"loi": a, "diem": s, "ly_do": why})
    out.sort(key=lambda r: -r["diem"])
    return out


def aug_plan(loai: str, bac: str, vong: str, mau: str) -> dict | None:
    """Trang LÕI → CÁCH ĐÁNH: loại lõi + bậc + vòng nhận + máu → kế hoạch."""
    hl = data()["hd_loi"]
    row = next((x for x in hl["loai_loi"] if x["ten"] == loai), None)
    if not row:
        return None
    return {
        "nhan": row["nhan"], "vi_du": row["vi_du"], "theo_bac": row["theo_bac"].get(bac, ""),
        "theo_vong": row["theo_vong"].get(vong, ""),
        "theo_mau": next((m["loi_khuyen"] for m in hl["theo_mau"] if m["ten"] == mau), ""),
        "len_cap": row["len_cap"], "doi_tuong": row["doi_tuong"], "chuoi": row["chuoi"],
        "doi_hinh": row["doi_hinh"], "loi_sau": row["loi_sau"], "tranh": row["tranh"],
    }


def item_plan(st: GameState, comp: dict | None) -> dict:
    """Ghép mảnh nào trước: đồ chủ lực chính → đỡ đòn → chủ lực phụ → đồ dự phòng an toàn."""
    parts = list(st.parts)
    plan = []
    if comp:
        prio = []
        carries = comp.get("chu_luc", [])
        tanks = comp.get("do_don", [])
        if carries:
            prio += [(i, carries[0]["tuong"]) for i in carries[0]["do"]]
        for tk in tanks:
            prio += [(i, tk["tuong"]) for i in tk["do"]]
        for cc in carries[1:]:
            prio += [(i, cc["tuong"]) for i in cc["do"]]
        for iid, who in prio:
            made, rest = buildable([iid], parts)
            if made:
                plan.append({"do": item(iid), "cho": champ(who)["ten"], "manh": item(iid)["cong_thuc"]})
                parts = rest
    flex = ["GargoyleStoneplate", "WarmogsArmor", "ProtectorsVow", "SunfireCape", "SpiritVisage", "BrambleVest",
            "DragonsClaw", "SpearOfShojin", "HandOfJustice", "StrikersFlail", "Crownguard", "IonicSpark",
            "SteadfastHeart", "Evenshroud", "AdaptiveHelm", "ThiefsGloves"]
    extra = []
    for iid in flex:
        made, rest = buildable([iid], parts)
        if made:
            extra.append({"do": item(iid), "cho": "tướng đỡ đòn" if "Tank" in item(iid).get("nhom", "") else "tướng tạm",
                          "manh": item(iid)["cong_thuc"]})
            parts = rest
    return {"uu_tien": plan, "du_phong": extra, "con_lai": parts,
            "thu_tu_manh": (comp or {}).get("excel", {}).get("uu_tien_manh", "")}


# ============================================================================ ấn → đội hình (Excel)


def emblem_names() -> list[str]:
    return [e["ten"] for e in data()["hd_an"]["an"]]


def emblem_rank(selected: list[str], lean: int = 0, top: int | None = None) -> list[dict]:
    """Đúng công thức trang CHỌN ẤN: điểm = điểm gốc + lệch theo loại đồ + Σ điểm ấn (bảng 1/2/3 bản ÷ số bản)."""
    an = data()["hd_an"]
    names = emblem_names()
    sel = [s for s in selected if s in names][:3]
    cnt = Counter(sel)
    res = []
    for ci, c in enumerate(an["doi_hinh"]):
        emb_pts, lines = 0.0, []
        for s in sel:
            j = names.index(s)
            k = min(cnt[s], 3) - 1
            emb_pts += an["diem"][k][ci][j] / cnt[s]
            lines.append({"an": s, "dien_giai": an["dien_giai"][k][ci][j], "diem": an["diem"][k][ci][j]})
        # mỗi loại ấn chỉ hiện 1 dòng diễn giải
        seen, uniq = set(), []
        for ln in lines:
            if ln["an"] not in seen:
                seen.add(ln["an"])
                uniq.append(ln)
        total = float(c["diem_goc"] or 0) + float((c["lech_do"] or [0, 0, 0, 0])[lean] or 0) + emb_pts
        res.append({"doi_hinh": c, "diem": round(total, 2), "diem_an": round(emb_pts, 2), "an": uniq})
    res.sort(key=lambda r: -r["diem"])
    return res[:top] if top else res


def emblem_info(name: str) -> dict | None:
    return next((e for e in data()["hd_an"]["an"] if e["ten"] == name), None)


def emblem_name_of_item(iid: str) -> str | None:
    it = item(iid)
    if it.get("loai") != "an" and iid != "TacticiansCrown":
        return None
    nm = it["ten"]
    return nm if nm in emblem_names() else None


# ============================================================================ gói lời khuyên


def advise(st: GameState) -> dict:
    ranked = score_comps(st, top=3)
    main = ranked[0]["comp"] if ranked else None
    emb = [n for n in (emblem_name_of_item(i) for i in st.items) if n]
    return {
        "doi_hinh": ranked,
        "roll": roll_or_level(st, main),
        "nhip": pace_advice(st, main),
        "loi": rank_augments(st, st.offered, main) if st.offered else [],
        "do": item_plan(st, main),
        "toc_he": board_traits(st.units),
        "lai": interest(st.gold),
        "an": emblem_rank(emb, item_lean(st.parts, st.items), top=3) if emb else [],
    }


# ============================================================================ luyện tập


def recipe_questions(seed: int | None = None, n: int = 20) -> list[dict]:
    """Câu hỏi ghép đồ tự sinh từ dữ liệu (luôn đúng theo bản game hiện tại)."""
    import random
    rnd = random.Random(seed)
    full = [i for i in data()["trang_bi"]["hoan_chinh"] if len(i["cong_thuc"]) == 2 and "Spatula" not in i["cong_thuc"]
            and "FryingPan" not in i["cong_thuc"]]
    out = []
    for it in rnd.sample(full, min(n, len(full))):
        wrong = rnd.sample([x["ten"] for x in full if x["id"] != it["id"]], 3)
        opts = wrong + [it["ten"]]
        rnd.shuffle(opts)
        a, b = (item_name(x) for x in it["cong_thuc"])
        out.append({"id": f"auto_{it['id']}", "nhom": "Ghép đồ", "cau_hoi": f"{a} + {b} ra đồ gì?",
                    "lua_chon": opts, "dap_an": opts.index(it["ten"]),
                    "giai_thich": f"{a} + {b} = {it['ten']}. {it.get('tac_dung', '')}"})
    return out


def quiz_pick(n: int = 10, seed: int | None = None, nhom: str | None = None) -> list[dict]:
    """Rút ngẫu nhiên n câu: phần lớn từ ngân hàng câu tình huống, thêm tối đa 2 câu ghép đồ tự sinh."""
    import random
    rnd = random.Random(seed)
    bank = [q for q in data()["cau_hoi"]["cau_hoi"] if not nhom or q["nhom"] == nhom]
    auto = [q for q in recipe_questions(seed) if not nhom or q["nhom"] == nhom]
    k_auto = min(2, len(auto), n) if bank else min(n, len(auto))
    pick = rnd.sample(bank, min(n - k_auto, len(bank))) + auto[:k_auto]
    rnd.shuffle(pick)
    return pick[:n]


def quiz_score(questions: list[dict], answers: dict[str, int]) -> dict:
    right = [q["id"] for q in questions if answers.get(q["id"]) == q["dap_an"]]
    n = len(questions)
    pct = round(100 * len(right) / n) if n else 0
    if pct >= 90:
        msg = "Xuất sắc! Tư duy này đủ để leo Cao Thủ – Thách Đấu."
    elif pct >= 70:
        msg = "Rất tốt! Ôn thêm vài tình huống là chắc top 4."
    elif pct >= 50:
        msg = "Khá ổn. Xem kỹ phần giải thích các câu sai — tiến bộ nhanh nhất là ở đó."
    else:
        msg = "Bắt đầu vậy là tốt rồi! Làm lại vài lượt, mỗi lượt sẽ nhớ thêm."
    return {"dung": len(right), "tong": n, "phan_tram": pct, "loi_nhan": msg, "dung_ids": right}


# ============================================================================ nhật ký


def stats_by(rows: list[dict], key: str) -> list[dict]:
    """Thống kê theo 1 cột (đội hình / lõi): số ván, hạng TB, % top 4, % top 1. Ô nhiều giá trị ngăn bởi '; '."""
    agg: dict[str, list[int]] = {}
    for r in rows:
        try:
            place = int(float(r.get("hang", 0)))
        except (TypeError, ValueError):
            continue
        if not 1 <= place <= 8:
            continue
        for v in [v.strip() for v in str(r.get(key, "") or "").split(";") if v.strip()]:
            agg.setdefault(v, []).append(place)
    out = []
    for k, ps in agg.items():
        n = len(ps)
        out.append({"ten": k, "so_van": n, "hang_tb": round(sum(ps) / n, 2),
                    "top4": round(100 * sum(p <= 4 for p in ps) / n), "top1": round(100 * sum(p == 1 for p in ps) / n)})
    out.sort(key=lambda x: (x["hang_tb"], -x["so_van"]))
    return out


def best_fit(rows: list[dict], min_games: int = 3) -> dict | None:
    s = [x for x in stats_by(rows, "doi_hinh") if x["so_van"] >= min_games]
    return s[0] if s else None
