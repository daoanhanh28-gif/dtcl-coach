# ĐTCL Coach v1.1 (2026-10-06) — dựng data/metatft_chi_tiet.json (form theo cấp, vị trí, đồ từng tướng) từ tools/raw
"""
Đầu vào (lấy từ API công khai của MetaTFT qua trình duyệt, Bạch Kim+, 3 ngày, bản 18.3b):
  tools/raw/comp_details_metatft.tsv  — mỗi cụm đội: mốc lên cấp, ô đứng từng tướng, 2 bàn cờ phổ biến nhất ở cấp 4/5/6/7
  tools/raw/unit_items_metatft.tsv    — mỗi tướng: hạng TB, tỉ lệ chơi, bộ đồ hay dùng nhất
Chạy:  python tools/build_chi_tiet.py
"""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "tools" / "raw"
FIX = {"GnarSmall": "Gnar", "Lux_Base": "Lux"}
SKIP = ("Elderwood_",)  # cây của Thần Rừng, không phải tướng


def ukey(u: str) -> str | None:
    u = u.strip()
    if not u or u.startswith(SKIP):
        return None
    return FIX.get(u, u)


def cell_to_rc(cell: int) -> list[int]:
    """Ô MetaTFT 1..28 (1–7 = hàng sau cùng) → [hàng, cột] của web (hàng 0 = sát địch)."""
    return [3 - (cell - 1) // 7, (cell - 1) % 7]


def build() -> dict:
    champs = {c["id"] for c in json.loads((ROOT / "data" / "tuong.json").read_text(encoding="utf-8"))}
    items = {i["id"] for g in json.loads((ROOT / "data" / "trang_bi.json").read_text(encoding="utf-8")).values() for i in g}
    cum = {}
    for line in (RAW / "comp_details_metatft.tsv").read_text(encoding="utf-8").splitlines():
        p = line.split("\t")
        if len(p) < 4:
            continue
        cid, lv, pos, early = p[0], p[1], p[2], p[3]
        levels = []
        for x in lv.split(","):
            if ">" in x:
                r, l = x.split(">")
                levels.append([r, int(l)])
        vt = {}
        for x in pos.split(","):
            if ":" not in x:
                continue
            u, c = x.split(":")
            u = ukey(u)
            if u in champs and c.strip().isdigit() and u not in vt:
                vt[u] = cell_to_rc(int(c))
        som = {}
        for lvl, chunk in zip(("4", "5", "6", "7"), early.split(";")):
            boards = []
            for b in chunk.strip().split("|"):
                if "@" not in b:
                    continue
                names, avg, n = b.split("@")
                us = [k for k in (ukey(x) for x in names.split(",")) if k in champs]
                if us:
                    boards.append({"tuong": list(dict.fromkeys(us)), "hang_tb": float(avg), "so_tran": int(n)})
            if boards:
                som[lvl] = boards
        cum[cid] = {"cap": levels, "vi_tri": vt, "som": som}
    do = {}
    for line in (RAW / "unit_items_metatft.tsv").read_text(encoding="utf-8").splitlines():
        p = line.split("\t")
        if len(p) < 4:
            continue
        u = ukey(p[0])
        its = [i.replace("18_Emblem", "Emblem_") for i in p[3].strip().split("+") if i]
        its = [i for i in its if i in items]
        if u in champs:
            do[u] = {"hang_tb": float(p[1]), "ti_le": float(p[2]), "do": its}
    return {"nguon": "MetaTFT (Bạch Kim+, 3 ngày, bản 18.3b) — đội hình giữa trận & đồ hay dùng",
            "cum": cum, "do_tuong": do}


if __name__ == "__main__":
    out = build()
    (ROOT / "data" / "metatft_chi_tiet.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(out["cum"]), "cụm,", len(out["do_tuong"]), "tướng")
