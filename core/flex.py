# ĐTCL Coach v1.3 (2026-10-20) — flex Ấn: tìm đội hình meta hợp nhất với Ấn đang có, xoay quanh CHỦ LỰC META
"""
Khác bảng điểm cố định của file Excel (bản 18.3b), phần này tính lại từ số liệu thật của bộ dữ liệu đang xem:
  - đội ứng viên = các cụm đội MetaTFT đủ mẫu (≥ 15.000 trận), mỗi đội có chủ lực / đỡ đòn / tướng thật
  - sức mạnh đội  = hạng TB + top 4 (MetaTFT), cộng số liệu máy chủ VN nếu khớp — tính hệ số 2 để luôn ưu tiên đội meta
  - giá trị Ấn    = mốc tộc/hệ mở thêm (mốc tộc của CHỦ LỰC nặng gấp 3) + ai cầm Ấn:
                    tướng được thống kê là cầm Ấn đó tốt (tactics.tools: hạng TB thấp hơn khi cầm),
                    chủ lực nhận tộc/hệ tăng sức mạnh cho chính nó (Đao Phủ, Thợ Săn, Mặt Trăng…),
                    đỡ đòn nhận tộc/hệ chống chịu (Vệ Quân, Dũng Sĩ…)
  - đổi tướng     = thử thay 1 tướng phụ (không đụng chủ lực, đỡ đòn, người cầm Ấn) để lên mốc cao hơn
Kết quả xếp theo tổng điểm, mỗi chủ lực chỉ giữ 1 đội tốt nhất → gợi ý luôn xoay quanh chủ lực meta.
"""
from __future__ import annotations

from collections import Counter
from itertools import permutations

from core import config
from core import engine as E
from core import plan as P

# tộc/hệ cho chính tướng mang nó sức mạnh (đeo cho chủ lực có lợi)
TOC_CHU_LUC = {"Executioner", "Hunter", "Slayer", "Rapidfire", "Spellweaver", "Invoker", "Lunar", "Fae", "Inferno",
               "Adaptor", "Blossom", "Blackthorn", "Riftbeast", "Primal"}
# tộc/hệ chống chịu (đeo cho đỡ đòn có lợi)
TOC_DO_DON = {"Defender", "Juggernaut", "Vanguard", "Brawler", "Elderwood", "Blackthorn"}
MAU_TOI_THIEU = 15000


@config.theo_bo
def _ctx() -> tuple[dict, dict]:
    """Bảng tra nhanh (tướng → tộc/hệ, tộc/hệ → mốc) — vòng lặp tối ưu gọi hàng chục nghìn lần."""
    d = E.data()
    tr = {c["id"]: tuple(c.get("toc_he", [])) for c in d["tuong"]}
    moc = {t: tuple(m for m in v.get("moc", []) if m) for t, v in d["trait"].items()}
    return tr, moc


def _counts(units, extra=()) -> Counter:
    tr = _ctx()[0]
    c = Counter()
    for u in units:
        c.update(tr.get(u, ()))
    c.update(extra)
    return c


def _tiers(t: str, n: int) -> int:
    return sum(1 for m in _ctx()[1].get(t, ()) if n >= m)


def _stats() -> dict:
    return E.data().get("an_thong_ke") or {}


def an_nguoi_cam(iid: str) -> list[dict]:
    """Ai cầm Ấn này tốt nhất theo thống kê (chênh hạng TB âm = tốt)."""
    return (_stats().get("an", {}).get(iid) or {}).get("nguoi_cam", [])


def _suc_manh(c: dict) -> float:
    s = c.get("so_lieu") or {}
    h, t4 = s.get("hang_tb", 4.6), s.get("top4", 50)
    return round((4.6 - h) * 6 + (t4 - 50) / 8, 2)


def _ung_vien() -> list[dict]:
    out = []
    for c in E.data()["metatft_doi_hinh"]:
        s = c.get("so_lieu") or {}
        if s.get("so_tran", 0) < MAU_TOI_THIEU or not c.get("chu_luc"):
            continue
        units = [u for u in dict.fromkeys(c["tuong"]) if u in E.data()["champ"]]
        carries = [r["tuong"] for r in c["chu_luc"] if r["tuong"] in units]
        tanks = [r["tuong"] for r in c.get("do_don", []) if r["tuong"] in units]
        if carries:
            out.append({"comp": c, "tuong": units, "chu_luc": carries, "do_don": tanks})
    return out


def _trong_so(units: list[str], carry: str, extra_carry: list[str]) -> dict[str, float]:
    w = {}
    main = set(P._main_traits(units))
    carry_traits = set(E.champ(carry).get("toc_he", [])) | set(extra_carry)
    for t, moc in _ctx()[1].items():
        w[t] = 0.3 if moc == (1,) else 1.0
        if t in main:
            w[t] = 2.0
        if t in carry_traits and moc != (1,):
            w[t] = 3.0
    return w


def _gia_tri(units, extra, w) -> float:
    total = 0.0
    for t, n in _counts(units, extra).items():
        k = _tiers(t, n)
        total += w.get(t, 1.0) * k * (k + 1) / 2
    return total


def _thuong_nguoi_cam(iid: str, t: str, who: str, carries: list[str], tanks: list[str]) -> tuple[float, str | None]:
    carry = carries[0]
    for x in an_nguoi_cam(iid):
        if x["tuong"] == who and x["chenh"] < 0:
            return 2 + min(3.0, -x["chenh"] * 10), (f"thống kê 18.4b: {E.champ(who)['ten']} cầm {E.item_name(iid)} "
                                                     f"hạng TB tốt hơn {abs(x['chenh']):.2f}")
    if who == carry and t in TOC_CHU_LUC:
        return 2.0, f"{P.trait_name(t)} tăng sức mạnh trực tiếp cho chủ lực {E.champ(who)['ten']}"
    if who in carries and t in TOC_CHU_LUC:
        return 1.5, f"{P.trait_name(t)} tăng sức mạnh cho chủ lực phụ {E.champ(who)['ten']}"
    if who in tanks and t in TOC_DO_DON:
        return 1.5, f"{P.trait_name(t)} giúp đỡ đòn {E.champ(who)['ten']} lì hơn"
    if who in tanks and t in TOC_CHU_LUC and t not in TOC_DO_DON:
        return -0.5, None       # Ấn sát thương phí trên tướng đỡ đòn
    return 0.05 * E.champ(who).get("gia", 1), None   # hoà điểm: ưu tiên tướng đắt (ở lại tới cuối trận)


def _xep_an(units, emblems, carries, tanks, comp_embs):
    """Thử mọi cách chia Ấn cho tướng (tối đa 3 Ấn) → [(ấn, người cầm)] có điểm cao nhất.
    Điểm = mốc tộc/hệ mở thêm (trọng số chủ lực) + thưởng người cầm hợp + thưởng nếu đội vốn ghép Ấn đó."""
    tr = _ctx()[0]
    embs = [e for e in emblems if P.emblem_trait(e)]
    best = (0.0, [], [])
    if not embs:
        return best
    et = {e: P.emblem_trait(e) for e in embs}
    # điểm người cầm tính sẵn cho từng (Ấn, tướng) — không đổi giữa các cách chia
    bon = {}
    for e in embs:
        for who in units:
            if et[e] in tr.get(who, ()):
                continue
            b, y = _thuong_nguoi_cam(e, et[e], who, carries, tanks)
            if e in comp_embs:
                b += 2.0
                y = y or f"đội này vốn hay ghép {E.item_name(e)}"
            bon[(e, who)] = (b, y)
    w_cache: dict[frozenset, dict] = {}
    base_cache: dict[frozenset, float] = {}
    cands = list(units) + [None]
    for combo in permutations(cands, len(embs)):
        pairs, bonus, why, ok = [], 0.0, [], True
        for e, who in zip(embs, combo):
            if who is None:
                continue
            if (e, who) not in bon:
                ok = False
                break
            pairs.append((e, who))
            b, y = bon[(e, who)]
            bonus += b
            if y:
                why.append(y)
        if not ok:
            continue
        extra = [et[e] for e, _ in pairs]
        key = frozenset(et[e] for e, u in pairs if u == carries[0])
        if key not in w_cache:
            w_cache[key] = _trong_so(units, carries[0], list(key))
            base_cache[key] = _gia_tri(units, [], w_cache[key])
        w = w_cache[key]
        cnt = _counts(units, extra)
        pen = sum(1.5 for t in extra if not _tiers(t, cnt[t]))      # Ấn chưa đủ mốc tộc/hệ → chỉ còn chỉ số
        v = _gia_tri(units, extra, w) - base_cache[key] + bonus - pen
        if v > best[0] + 1e-9:
            best = (v, pairs, why)
    return best


def _doi_tuong(units, pairs, carry, tanks, w, level):
    """Thay 1 tướng phụ để lên mốc tộc của Ấn / của chủ lực — không làm mất mốc của tộc/hệ chính."""
    extra = [P.emblem_trait(e) for e, _ in pairs]
    base = _gia_tri(units, extra, w)
    keep = set([carry] + tanks + [u for _, u in pairs])
    max_cost = 4 if level <= 8 else 5
    pool = [c["id"] for c in E.data()["tuong"] if c["gia"] <= max_cost and c["id"] not in units and c.get("toc_he")]
    focus = set(extra) | set(E.champ(carry).get("toc_he", []))
    cnt0 = _counts(units, extra)
    protect = {t for t in cnt0 if w.get(t, 1) >= 2 or (_tiers(t, cnt0[t]) >= 2 and _ctx()[1].get(t) != (1,))}
    best = None
    for r in [u for u in units if u not in keep]:
        for c in pool:
            nb = [x for x in units if x != r] + [c]
            cnt1 = _counts(nb, extra)
            if any(_tiers(t, cnt1[t]) < _tiers(t, cnt0[t]) for t in focus | protect):
                continue
            up = [t for t in focus if _tiers(t, cnt1[t]) > _tiers(t, cnt0[t])]
            if not up:
                continue
            gain = _gia_tri(nb, extra, w) - base - 0.5
            if gain >= 2 and (best is None or gain > best["diem"]):
                best = {"bo": r, "them": c, "diem": round(gain, 1), "doi": P._diff(units, extra, nb, extra)}
    return best


def flex_an(emblems: list[str], top: int = 5, level: int = 9) -> list[dict]:
    """Ấn đang có (id) → top đội hình meta hợp nhất, mỗi chủ lực 1 đội (nhớ kết quả theo bộ dữ liệu + Ấn)."""
    return _flex_an(tuple(e for e in emblems if P.emblem_trait(e))[:3], top, level)


@config.theo_bo
def _flex_an(emblems: tuple, top: int, level: int) -> list[dict]:
    emblems = list(emblems)
    vn = (E.data().get("vn_opgg") or {}).get("doi_hinh", [])
    res = []
    for cand in _ung_vien():
        units, carry, tanks = cand["tuong"][:level], cand["chu_luc"][0], cand["do_don"]
        comp_embs = set(cand["comp"].get("an_nen_ghep", []))
        gain, pairs, why = _xep_an(units, emblems, [c for c in cand["chu_luc"] if c in units], tanks, comp_embs)
        if emblems and not pairs:
            continue
        extra = [P.emblem_trait(e) for e, _ in pairs]
        w2 = _trong_so(units, carry, [P.emblem_trait(e) for e, u in pairs if u == carry])
        swap = _doi_tuong(units, pairs, carry, tanks, w2, level) if pairs else None
        # số liệu VN nếu cùng đội
        us, best_vn, j_best = set(units), None, 0.0
        for r in vn:
            s = set(r["tuong"])
            j = len(us & s) / len(us | s) if us | s else 0
            if j > j_best:
                best_vn, j_best = r, j
        best_vn = best_vn if j_best >= 0.5 else None
        sm = _suc_manh(cand["comp"]) + ((4.0 - best_vn["hang_tb"]) * 1.5 if best_vn else 0)
        moc = []
        cnt0, cnt1 = P.counts(units), P.counts(units, extra)
        for e, who in pairs:
            t = P.emblem_trait(e)
            moc.append({"an": e, "nguoi_cam": who, "toc_he": t, "truoc": cnt0[t], "sau": cnt1[t],
                        "moc_dat": P.trait_moc(t)[P.tiers(t, cnt1[t]) - 1] if P.tiers(t, cnt1[t]) else 0,
                        "len_moc": P.tiers(t, cnt1[t]) > P.tiers(t, cnt0[t]),
                        "moc_tiep": next((m for m in P.trait_moc(t) if m > cnt1[t]), None)})
        res.append({"comp": cand["comp"], "tuong": units, "chu_luc": carry, "do_don": tanks, "nguoi_cam": pairs,
                    "ten": f"{E.champ(carry)['ten']} – " + " · ".join(P.trait_name(t) for t in P._main_traits(units)[:2]),
                    "moc": moc, "doi": swap, "vi_sao": why, "vn": best_vn, "suc_manh": round(sm, 1),
                    "diem_an": round(gain, 1), "diem": round(2 * sm + gain + (swap["diem"] * 0.3 if swap else 0), 1),
                    "toc_he": [t for t in sorted(cnt1, key=lambda t: (-P.tiers(t, cnt1[t]), -cnt1[t]))
                               if P.tiers(t, cnt1[t]) and P.trait_moc(t) != [1]]})
    res.sort(key=lambda r: -r["diem"])
    seen, out = set(), []
    for r in res:
        if r["chu_luc"] in seen:
            continue
        seen.add(r["chu_luc"])
        out.append(r)
        if len(out) >= top:
            break
    return out
