# ĐTCL Coach v1.1 (2026-10-06) — kiểm thử dữ liệu game (data/*.json) và quy ước phiên bản
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import config, engine as e  # noqa: E402


def test_version_everywhere():
    v, dte = config.VERSION, config.VERSION_DATE
    assert (ROOT / "VERSION").read_text(encoding="utf-8").strip() == f"{v} · {dte}"
    assert f"{v}" in (ROOT / "README.md").read_text(encoding="utf-8").splitlines()[0]
    files = [p for p in ROOT.rglob("*") if p.suffix in {".py", ".gs", ".toml", ".example", ".yml", ".md", ".txt"}
             and ".git" not in p.parts and "raw" not in p.parts and p.name != "VERSION"]
    bad = []
    for p in files:
        first = p.read_text(encoding="utf-8").splitlines()[0] if p.read_text(encoding="utf-8") else ""
        if not (v in first and dte in first):
            bad.append(str(p.relative_to(ROOT)))
    assert not bad, f"Dòng đầu thiếu phiên bản {v} ({dte}): {bad}"


def test_json_files_parse():
    for p in (ROOT / "data").glob("*.json"):
        json.loads(p.read_text(encoding="utf-8"))


def test_game_data_counts():
    d = e.data()
    assert len(d["tuong"]) == 65
    costs = [c["gia"] for c in d["tuong"]]
    assert [costs.count(i) for i in range(1, 6)] == [14, 13, 14, 14, 10]
    assert len(d["toc_he"]) >= 30
    assert len(d["trang_bi"]["thanh_phan"]) == 10
    assert len(d["trang_bi"]["an"]) == 20
    assert len(d["loi"]) > 200
    for a in d["loi"]:
        assert a["bac"] in ("Bạc", "Vàng", "Kim cương") and a["xep_hang"] in "SABC"


def test_every_champ_trait_exists():
    d = e.data()
    for c in d["tuong"]:
        for t in c["toc_he"]:
            assert t in d["trait"], (c["id"], t)
        assert c["anh"].startswith("https://raw.communitydragon.org/")


def test_excel_data_links():
    d = e.data()
    an = d["hd_an"]
    assert len(an["an"]) == 21 and len(an["doi_hinh"]) == 19
    for m in an["diem"]:
        assert len(m) == 19 and all(len(r) == 21 for r in m)
    for c in an["doi_hinh"]:
        for n in c["tuong"]:
            assert e.champ_id(n), n
    nh = d["hd_nhip"]
    assert len(nh["loi_choi"]) == 5 and all(len(s["lo_trinh"]) == 12 for s in nh["loi_choi"])
    assert len(d["hd_loi"]["loai_loi"]) == 9
    for c in e.comps():
        for r in c["chu_luc"] + c["do_don"]:
            assert all(i in d["item"] for i in r["do"])


def test_quiz_bank_valid():
    qs = e.data()["cau_hoi"]["cau_hoi"]
    assert len(qs) >= 30 and len({q["id"] for q in qs}) == len(qs)
    for q in qs:
        assert len(q["lua_chon"]) >= 2 and 0 <= q["dap_an"] < len(q["lua_chon"]) and q["giai_thich"]


def test_no_secrets_in_repo():
    pat = re.compile(r"AIza[0-9A-Za-z_\-]{20,}|sk-ant-[0-9A-Za-z]{10,}|script\.google\.com/macros/s/AKfy")
    for p in ROOT.rglob("*"):
        if p.is_file() and p.suffix in {".py", ".toml", ".md", ".json", ".gs", ".example", ".yml"} and ".git" not in p.parts:
            assert not pat.search(p.read_text(encoding="utf-8", errors="ignore")), p
