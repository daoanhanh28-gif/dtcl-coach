# ĐTCL Coach v1.4 (2026-10-22) — cập nhật phần hướng dẫn (data/hd_*.json) theo bản mới mà không cần làm lại file Excel
"""
Chạy SAU build_data.py và build_chi_tiet.py:   python tools/cap_nhat_ban.py
Cập nhật lần lượt mọi bộ trong BO_CAN_CAP_NHAT (bộ mới data/ và bộ đang chạy data/ban/18.4b/); mỗi bộ có ban_cap_nhat.json riêng.

Đầu vào:
  tools/raw/vn_opgg.tsv       — bảng đội hình máy chủ VN (OP.GG, lọc region=vn), mỗi dòng:
                                tên · bậc · hạng TB · top 4 % · top 1 % · % người chơi · số ván · tướng (id, cách nhau dấu phẩy)
                                · độ khó (1 dễ / 2 vừa / 3 khó) · cấp mục tiêu · tướng chính[đồ+đồ+đồ]*3 (cách nhau dấu cách)
  data/ban_cap_nhat.json      — danh sách tăng / giảm của bản mới (viết tay từ ghi chú bản vá)
Ghi đè:
  data/hd_kien_thuc.json      — bảng máy chủ VN, mục “Có gì mới”
  data/hd_an.json             — số liệu VN + xu hướng bản mới của 19 đội (trang Chọn Ấn / Phân tích bản cập nhật)
  data/hd_doi_hinh.json       — dòng “Khi nào chơi” thêm nhận định bản mới
  data/meta.json              — thông tin bản dữ liệu (bo, ban_moi, vn_nguon)
  data/vn_opgg.json           — bảng VN có cấu trúc (trang Cẩm nang)
Xu hướng của đội = tổng (tăng +1 / giảm −1) của 2 tướng chủ lực (tướng khác ×0,5) và tộc/hệ đạt đúng mốc bị đổi (“moc” trong ban_cap_nhat.json).
"""
from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = ROOT / "tools" / "raw"

# bộ dữ liệu → (thư mục, bảng OP.GG VN, bản của số liệu VN, ngày lấy, số ván 24 giờ)
BO_CAN_CAP_NHAT = {
    "18.5": (DATA, "vn_opgg_185.tsv", "18.5", "22/10/2026", "32.640"),
    "18.4b": (DATA / "ban" / "18.4b", "vn_opgg.tsv", "18.4b", "20/10/2026", "196.456"),
}
BO = "18.5"                       # bộ đang xử lý (main() đổi lần lượt)
VN_FILE, VN_BAN, VN_NGAY, VN_SO_VAN = "vn_opgg_185.tsv", "18.5", "22/10/2026", "32.640"
VN_NGUON = f"OP.GG · máy chủ VN · bản {VN_BAN} ({VN_SO_VAN} ván / 24 giờ, {VN_NGAY})"


THU_MUC = DATA


def load(name, thu_muc: Path | None = None):
    return json.loads(((thu_muc or THU_MUC) / name).read_text(encoding="utf-8"))


def save(name, obj):
    (THU_MUC / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", str(s or "")).lower().strip())


def vn_num(x: float, nd: int) -> str:
    return f"{x:.{nd}f}".replace(".", ",")


tuong = load("tuong.json", DATA)
toc_he = load("toc_he.json", DATA)
champ = {c["id"]: c for c in tuong}
by_name = {norm(c["ten"]): c["id"] for c in tuong} | {norm(c["ten_en"]): c["id"] for c in tuong} | {norm(c["id"]): c["id"] for c in tuong}
trait = {t["id"]: t for t in toc_he}
trait_by_name = {norm(t["ten"]): t["id"] for t in toc_he}


def cid(name: str) -> str | None:
    return by_name.get(norm(name))


def active_traits(units: list[str]) -> set[str]:
    cnt = Counter(t for u in units for t in champ[u]["toc_he"])
    out = set()
    for t, n in cnt.items():
        moc = [m for m in trait.get(t, {}).get("moc", []) if m]
        if moc and n >= moc[0]:
            out.add(t)
    return out


# ------------------------------------------------------------------ bảng VN
def read_vn() -> list[dict]:
    rows = []
    for line in (RAW / VN_FILE).read_text(encoding="utf-8").splitlines():
        p = line.split("\t")
        if len(p) < 8:
            continue
        units = [u if u in champ else {"GnarSmall": "Gnar"}.get(u, u) for u in p[7].split(",")]
        chinh = []
        for x in (p[10].split() if len(p) > 10 else []):
            m = re.match(r"(\w+)\[([^\]]*)\](\*3)?", x)
            if m and {"GnarSmall": "Gnar"}.get(m.group(1), m.group(1)) in champ:
                chinh.append({"tuong": {"GnarSmall": "Gnar"}.get(m.group(1), m.group(1)),
                              "do": [i for i in m.group(2).split("+") if i], "sao3": bool(m.group(3))})
        rows.append({"ten": p[0], "bac": p[1], "hang_tb": float(p[2]), "top4": float(p[3]), "top1": float(p[4]),
                     "ti_le": float(p[5]), "so_van": int(p[6]), "tuong": [u for u in units if u in champ],
                     "do_kho": int(p[8]) if len(p) > 8 and p[8] else None,
                     "cap": int(p[9]) if len(p) > 9 and p[9] else None, "chinh": chinh})
    return rows


def vn_table(rows: list[dict]) -> dict:
    order = {"OP": 0, "S": 1, "A": 2, "B": 3, "C": 4, "D": 5}
    rs = sorted(rows, key=lambda r: (order.get(r["bac"], 9), r["hang_tb"]))
    dong = [[i + 1, r["ten"], r["bac"], f"{r['hang_tb']:.2f}", vn_num(r["top4"], 1) + "%", vn_num(r["ti_le"], 2) + "%",
             ", ".join(champ[u]["ten"] for u in r["tuong"])] for i, r in enumerate(rs)]
    best = sorted([r for r in rows if r["ti_le"] >= 0.3], key=lambda r: r["hang_tb"])[:3]
    spam = sorted([r for r in rows if r["ti_le"] < 0.3 and r["hang_tb"] <= 3.2], key=lambda r: r["hang_tb"])[:3]
    avoid = sorted([r for r in rows if r["ti_le"] >= 0.4 and r["hang_tb"] >= 4.3], key=lambda r: -r["ti_le"])[:4]
    f = lambda r: f"{r['ten']} {r['hang_tb']:.2f} / top 4 {vn_num(r['top4'], 1)}% ({vn_num(r['ti_le'], 2)}% người chơi)"
    goi_y = (f"Nguồn: OP.GG lọc riêng MÁY CHỦ VIỆT NAM (VN), bản {VN_BAN}, {VN_SO_VAN} ván trong 24 giờ (cập nhật {VN_NGAY}). "
             f"Đây là số liệu sát với phòng bạn đánh nhất.\n"
             f"GỢI Ý NHANH ({VN_NGAY}): (1) Mạnh nhất và đủ người chơi: " + " · ".join(f(r) for r in best) + ". "
             f"(2) Mạnh mà ít người chơi (mẫu nhỏ, dao động): " + " · ".join(f(r) for r in spam) + ". "
             f"(3) Tránh — đông người mà hạng thấp: " + " · ".join(f(r) for r in avoid) + ". "
             f"Xem trang “Phân tích bản cập nhật” để biết đội nào được lợi ở {BO}.")
    return {"tieu_de": f"★ MÁY CHỦ VIỆT NAM (VN) – OP.GG, bản {VN_BAN}, {VN_SO_VAN} ván / 24 giờ ({VN_NGAY[:5]}) – ĐỌC BẢNG NÀY TRƯỚC",
            "cot": ["#", "Đội hình", "Bậc", "Hạng TB", "Top 4", "Tỉ lệ chơi", "Tướng chính"], "dong": dong, "goi_y": goi_y}


def match_vn(units: list[str], rows: list[dict]) -> dict | None:
    us = set(units)
    best, score = None, 0.0
    for r in rows:
        s = set(r["tuong"])
        j = len(us & s) / len(us | s) if us | s else 0
        if j > score:
            best, score = r, j
    return best if score >= 0.5 else None


# ------------------------------------------------------------------ xu hướng bản mới
def changes() -> list[dict]:
    out = []
    for x in load("ban_cap_nhat.json")["thay_doi"]:
        w = {"tang": 1.0, "giam": -1.0}.get(x["huong"], 0.0) * x.get("muc", 1)   # muc 0,5 = chỉnh nhỏ (≈ 5%)
        if x["loai"] == "tuong" and cid(x["ten"]):
            if "Săn Thưởng" in x["chi_tiet"]:
                w *= 0.5            # chỉ ảnh hưởng Draven lấy sớm
            out.append({"kieu": "tuong", "id": cid(x["ten"]), "w": w, "ten": champ[cid(x["ten"])]["ten"]})
        elif x["loai"] == "toc_he" and trait_by_name.get(norm(x["ten"])):
            out.append({"kieu": "toc_he", "id": trait_by_name[norm(x["ten"])], "w": w, "ten": x["ten"], "moc": x.get("moc", 0)})
    return out


def trend(units: list[str], core: list[str], ch: list[dict]) -> tuple[float, str]:
    act = active_traits(units)
    cnt = Counter(t for u in units for t in champ[u]["toc_he"])
    s, up, down = 0.0, [], []
    for c in ch:
        if not c["w"]:
            continue
        if c["kieu"] == "tuong" and c["id"] in units:
            k = 1.0 if c["id"] in core[:2] else 0.5
        elif c["kieu"] == "toc_he" and c["id"] in act and cnt[c["id"]] >= c["moc"]:
            k = 1.0     # chỉ tính khi đội đạt đúng mốc bị đổi (vd Gai Đen 6, Thần Rừng 9)
        else:
            continue
        s += c["w"] * k
        (up if c["w"] > 0 else down).append(c["ten"])
    if s >= 1.5:
        arrow, lab = "↑", "MẠNH LÊN RÕ"
    elif s >= 0.5:
        arrow, lab = "↗", "MẠNH LÊN"
    elif s <= -1.5:
        arrow, lab = "↓", "GIẢM"
    elif s <= -0.5:
        arrow, lab = "↘", "giảm nhẹ"
    else:
        arrow, lab = "→", "cân bằng" if (up or down) else "không bị đụng tới"
    parts = []
    if up:
        parts.append(", ".join(dict.fromkeys(up)) + " tăng")
    if down:
        parts.append(", ".join(dict.fromkeys(down)) + " giảm")
    return s, f"{arrow} {BO}: " + ("; ".join(parts) + " – " if parts else "") + lab


# ------------------------------------------------------------------ chạy
def thong_ke_an() -> dict:
    """tools/raw/tactics_tools_184b.txt → Ấn: ai cầm tốt nhất (chênh hạng TB), tướng: hạng TB, tộc hệ: hạng TB theo mốc."""
    an, tg, th = {}, {}, {}
    fix = {"GnarSmall": "Gnar", "Lux_Base": "Lux"}
    for line in (RAW / "tactics_tools_184b.txt").read_text(encoding="utf-8").splitlines():
        p = line.split()
        if not p:
            continue
        if p[0] == "EM":
            iid = p[1].replace("18_Emblem", "Emblem_")
            users = []
            for x in (p[6].split(",") if len(p) > 6 else []):
                u, dlt = x.split(":")
                u = fix.get(u, u)
                if u in champ:
                    users.append({"tuong": u, "chenh": float(dlt)})
            an[iid] = {"so_doi": int(p[2]), "hang_tb": float(p[3]), "top4": float(p[4]), "top1": float(p[5]), "nguoi_cam": users}
        elif p[0] == "UN":
            u = fix.get(p[1], p[1])
            if u in champ:
                tg[u] = {"so_doi": int(p[2]), "hang_tb": float(p[3]), "top4": float(p[4]), "top1": float(p[5])}
        elif p[0] == "TR":
            th[p[1]] = {k: float(v) for k, v in (x.split(":") for x in p[2:])}
    return {"nguon": "tactics.tools · Kim Cương+ · bản 18.4b · 4.490.384 đội hình (20/10/2026)",
            "giai_thich": "chenh = hạng TB của tướng khi cầm Ấn đó trừ hạng TB chung của tướng; âm là tốt hơn.",
            "an": an, "tuong": tg, "toc_he_moc": th}


def main():
    global THU_MUC, BO, VN_FILE, VN_BAN, VN_NGAY, VN_SO_VAN, VN_NGUON
    for bo, (thu_muc, vn_file, vn_ban, vn_ngay, vn_so_van) in BO_CAN_CAP_NHAT.items():
        THU_MUC, BO = thu_muc, bo
        VN_FILE, VN_BAN, VN_NGAY, VN_SO_VAN = vn_file, vn_ban, vn_ngay, vn_so_van
        VN_NGUON = f"OP.GG · máy chủ VN · bản {VN_BAN} ({VN_SO_VAN} ván / 24 giờ, {VN_NGAY})"
        cap_nhat_bo()


def cap_nhat_bo():
    vn = read_vn()
    save("an_thong_ke.json", thong_ke_an())
    save("vn_opgg.json", {"nguon": VN_NGUON, "ban": VN_BAN, "ngay": VN_NGAY,
                          "do_kho": {"1": "Dễ", "2": "Vừa", "3": "Khó"}, "doi_hinh": vn})
    ch = changes()
    bc = load("ban_cap_nhat.json")

    kt = load("hd_kien_thuc.json")
    kt["may_chu"]["vn"] = vn_table(vn)
    kt["may_chu"]["ghi_chu"] = (f"⚠ Bảng Việt Nam: {VN_NGUON}. Bảng Hàn / Trung Quốc, phần so sánh và “cách build từng bước” "
                                "vẫn là bản 18.3b (file Excel v1.8) — chỉ để xem xu hướng. ⚠ Cỡ mẫu: đội có tỉ lệ chơi dưới 0,3% "
                                "chỉ dựa trên vài trăm ván → số liệu dao động mạnh, đừng coi là chắc chắn.")
    tg = {"tang": [], "giam": [], "khac": []}
    for x in bc["thay_doi"]:
        key = "tang" if x["huong"] == "tang" else "giam" if x["huong"] == "giam" else "khac"
        tg[key].append(x)
    nhom = {"tuong": "tướng", "toc_he": "tộc/hệ", "loi": "lõi", "trang_bi": "trang bị", "tinh_linh": "Tinh Linh", "he_thong": "hệ thống"}
    bm = [{"k": f"🗓 Bản {bc['phien_ban']} – {bc['ngay']}", "v": bc["ghi_chu"]}]
    for key, icon, word in (("tang", "▲", "tăng"), ("giam", "⚠", "giảm"), ("khac", "↔", "điều chỉnh / mới")):
        for loai, ten in nhom.items():
            xs = [x for x in tg[key] if x["loai"] == loai]
            if xs:
                bm.append({"k": f"{icon} {bc['phien_ban']} {word} {ten}",
                           "v": " · ".join(f"{x['ten']}: {x['chi_tiet']}" for x in xs) + "."})
    for x in bc.get("ban_truoc", []):
        bm.append({"k": f"🕘 Bản {x['k']}", "v": x["v"]})
    kt["ban_moi"] = bm
    save("hd_kien_thuc.json", kt)

    an = load("hd_an.json")
    n_vn = 0
    for c in an["doi_hinh"]:
        units = [x for x in (cid(n) for n in c["tuong"]) if x]
        core = [x for x in (cid(c[k]["tuong"]) for k in ("chu_luc", "chu_luc_phu", "do_don")) if x]
        units += [u for u in core if u not in units]
        r = match_vn(units, vn)
        if r:
            n_vn += 1
            c["so_lieu_vn"] = (f"VN {VN_BAN}: hạng TB {r['hang_tb']:.2f} · top 4 {vn_num(r['top4'], 1)}% · "
                               f"{vn_num(r['ti_le'], 2)}% người chơi")
        else:
            c["so_lieu_vn"] = (f"VN {VN_BAN}: chưa có trong bảng OP.GG (đội ít người chơi)" if len(vn) >= 15 else
                               f"VN {VN_BAN}: chưa đủ ván (bản mới ra, OP.GG mới có {len(vn)} đội) — xem số quốc tế MetaTFT")
        c["ban_moi"] = trend(units, core, ch)[1]
    an["nguon"] = an.get("nguon", "") .split(" · Cập nhật")[0] + f" · Cập nhật {BO}: số liệu {VN_NGUON}, xu hướng theo thay đổi bản {BO}."
    save("hd_an.json", an)

    hd = load("hd_doi_hinh.json")
    for c in hd["doi_hinh"]:
        units = [x for x in (cid(n) for n in c["tuong"]) if x]
        core = [x for x in (cid(c[k]["tuong"]) for k in ("chu_luc", "chu_luc_phu", "do_don")) if x]
        units += [u for u in core if u not in units]
        c["khi_nao"] = re.split(r" ⚠ (?:[↑↗→↘↓] )?\d+\.\w+:", c["khi_nao"])[0] + f" ⚠ {trend(units, core, ch)[1]}."
    save("hd_doi_hinh.json", hd)

    meta = load("meta.json")
    meta.update({"bo": BO, "ban_moi": bc["phien_ban"], "ngay_ban_moi": bc["ngay"], "vn_nguon": VN_NGUON,
                 "excel": "file Excel “Hướng dẫn Thách Đấu Mùa 18” v1.8 (06/10/2026) + cập nhật " + BO})
    save("meta.json", meta)
    print(f"[{BO}] VN: {len(vn)} đội · 19 đội Excel có số VN: {n_vn} · thay đổi tính xu hướng: {len(ch)}")


if __name__ == "__main__":
    main()
