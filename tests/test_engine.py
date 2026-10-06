# ĐTCL Coach v1.1 (2026-10-06) — kiểm thử mọi phép tính của bộ luật (không cần Streamlit)
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import engine as e  # noqa: E402


# ------------------------------------------------------------------ ghép đồ
def test_combine_basic():
    assert e.combine("BFSword", "SparringGloves")["ten"] == "Vô Cực Kiếm"
    assert e.combine("SparringGloves", "BFSword")["ten"] == "Vô Cực Kiếm"
    assert e.combine("NeedlesslyLargeRod", "TearOfTheGoddess")["ten"] == "Quyền Trượng Thiên Thần"
    assert e.combine("ChainVest", "NegatronCloak")["ten"] == "Thú Tượng Thạch Giáp"
    assert e.combine("Spatula", "GiantsBelt")["ten"] == "Ấn Gai Đen"
    assert e.combine("FryingPan", "SparringGloves")["ten"] == "Ấn Đao Phủ"
    assert e.combine("Spatula", "Spatula")["ten"] == "Vương Miện Chiến Thuật"


def test_recipe_table_full():
    t = e.recipe_table()
    assert len(t) == 10 and all(len(r) == 10 for r in t)
    assert all(x is not None for r in t for x in r)
    for i in range(10):          # bảng đối xứng
        for j in range(10):
            assert t[i][j] == t[j][i]


def test_buildable_greedy():
    made, rest = e.buildable(["InfinityEdge", "Deathblade"], ["BFSword", "SparringGloves", "BFSword"])
    assert made == ["InfinityEdge"] and rest == ["BFSword"]
    made, rest = e.buildable(["Deathblade"], ["BFSword", "BFSword"])
    assert made == ["Deathblade"] and rest == []


def test_item_lean():
    assert e.item_lean(["BFSword", "RecurveBow"]) == 1
    assert e.item_lean(["NeedlesslyLargeRod", "TearOfTheGoddess"]) == 2
    assert e.item_lean(["ChainVest", "GiantsBelt", "NegatronCloak"]) == 3
    assert e.item_lean([]) == 0


# ------------------------------------------------------------------ kinh tế
def test_interest_and_income():
    assert [e.interest(g) for g in (0, 9, 10, 38, 50, 90)] == [0, 0, 1, 3, 5, 5]
    inc = e.income(50, 6, True)
    assert inc == {"co_ban": 5, "lai": 5, "chuoi": 3, "thang": 1, "tong": 14}
    assert e.income(20, -4)["chuoi"] == 1
    assert e.income(20, 2)["chuoi"] == 0
    assert e.income(20, -5)["chuoi"] == 2


def test_xp_and_odds():
    assert e.xp_to_next(7) == 56 and e.xp_to_next(8) == 64
    assert e.gold_to_level(7) == 56
    assert e.gold_to_level(7, xp_now=10) == 48
    for lv in range(1, 11):
        assert sum(e.shop_odds(lv)) == 100
    assert e.shop_odds(8)[3] == 30


def test_roll_estimate_matches_excel():
    est = e.roll_estimate(8, 4, 7)       # Excel: tỉ lệ 1 ô 0.015, ~13.74 lượt, ~31.5 vàng
    assert abs(est["ti_le_o"] - 0.015) < 1e-9
    assert abs(est["so_luot"] - 13.739) < 0.01
    assert abs(est["vang"] - 31.48) < 0.05
    assert e.roll_estimate(4, 5, 9)["so_luot"] == float("inf")


# ------------------------------------------------------------------ đội hình
def test_comps_loaded_from_excel():
    cs = e.comps()
    assert len(cs) == 19
    assert cs[0]["ten"].startswith("Đao Phủ Azir")
    for c in cs:
        assert c["hang"] in "SABC"
        assert c["tuong"] and all(u in e.data()["champ"] for u in c["tuong"])
        assert c["chu_luc"] and all(2 <= len(r["do"]) <= 3 for r in c["chu_luc"])
        assert c["kieu"] in ("fast8", "fast9", "reroll")


def test_template_board_valid():
    for c in e.comps():
        b = e.template_board(c)
        assert len(b) == len(set(b.values()))
        assert all(0 <= r < 4 and 0 <= col < 7 for r, col in b)
        if c["chu_luc"]:
            main = c["chu_luc"][0]["tuong"]
            assert main in b.values()


def test_board_traits():
    tr = {t["id"]: t for t in e.board_traits(["Azir", "Veigar", "RekSai"])}
    assert tr["Blackthorn"]["so"] == 3 and tr["Blackthorn"]["kich_hoat"] and tr["Blackthorn"]["moc_tiep"] == 4


# ------------------------------------------------------------------ trợ lý
def test_score_comps_prefers_matching_comp():
    st = e.GameState(units=["Azir", "Soraka", "Zyra", "Rammus", "Teemo", "Veigar", "Fiddlesticks"],
                     parts=["NeedlesslyLargeRod", "SparringGloves"], stage=3, rnd=2, level=6, gold=30)
    top = e.score_comps(st)
    assert top[0]["comp"]["ten"].startswith("Đao Phủ Azir")
    assert len(top) == 3 and top[0]["diem"] >= top[1]["diem"] >= top[2]["diem"]


def test_roll_or_level_rules():
    comp = e.comps()[0]                                   # lên 8 nhanh
    s = e.GameState(stage=4, rnd=2, level=7, gold=60, hp=60)
    assert e.roll_or_level(s, comp)["hanh_dong"] == "len_cap"
    s = e.GameState(stage=4, rnd=2, level=8, gold=60, hp=60)
    assert e.roll_or_level(s, comp)["hanh_dong"] == "roll"
    s = e.GameState(stage=3, rnd=5, level=7, gold=25, hp=30)
    assert e.roll_or_level(s, comp)["hanh_dong"] == "roll_het"
    reroll = next(c for c in e.comps() if c["kieu"] == "reroll" and c["cap_muc_tieu"] == 5)
    s = e.GameState(stage=3, rnd=2, level=5, gold=62, hp=70)
    r = e.roll_or_level(s, reroll)
    assert r["hanh_dong"] == "roll_cham" and "12" in r["tieu_de"]
    s = e.GameState(stage=2, rnd=3, level=4, gold=20, hp=90)
    assert e.roll_or_level(s, comp)["hanh_dong"] == "giu_vang"
    s = e.GameState(stage=4, rnd=2, level=7, gold=55, hp=60)        # thiếu 1 vàng để lên 8 thẳng → mua kinh nghiệm dần
    r = e.roll_or_level(s, comp)
    assert r["hanh_dong"] == "mua_xp" and "cấp 8" in r["tieu_de"]


def test_pace_advice_uses_excel_plan():
    comp = e.comps()[0]
    p = e.pace_advice(e.GameState(stage=4, rnd=2, gold=50, hp=55, streak=3), comp)
    assert p["dong"]["vong"] == "4-2" and "MỐC ĐỔI TƯỚNG" in p["dong"]["viec"]
    assert p["chuoi_ten"] == "Đang THẮNG liên tiếp" and p["mau_ten"] == "Từ 40 đến 70 máu"
    assert p["can_them"] == "Đã tối đa (50+)"
    assert e.gold_check(5).startswith("Vàng rất thấp")
    assert "20" in e.gold_check(27)


def test_rank_augments():
    comp = e.comps()[0]
    st = e.GameState(stage=2, rnd=1, hp=100)
    res = e.rank_augments(st, ["DA_18_FloraFatalisAugmentPlus", "DA_18_LunarTraitAugment", "DA_GroupHugI"], comp)
    assert res[0]["loi"]["id"] == "DA_18_FloraFatalisAugmentPlus"
    assert res[-1]["loi"]["id"] == "DA_18_LunarTraitAugment"
    res = e.rank_augments(st, ["DA_18_CovenTraitAugment_LootToAP", "DA_GroupHugI"], comp)
    assert res[0]["loi"]["id"] == "DA_GroupHugI"           # Excel: Tà Thuật đang tắt


def test_item_plan():
    comp = e.comps()[0]                                   # Soraka: Găng Bảo Thạch đầu tiên
    st = e.GameState(parts=["NeedlesslyLargeRod", "SparringGloves", "ChainVest", "NegatronCloak", "BFSword"])
    p = e.item_plan(st, comp)
    names = [x["do"]["ten"] for x in p["uu_tien"]]
    assert names[0] == "Găng Bảo Thạch" and "Thú Tượng Thạch Giáp" in names
    assert p["con_lai"] == ["BFSword"]


def test_emblem_rank_matches_excel_example():
    res = e.emblem_rank(["Ấn Đao Phủ", "Ấn Mặt Trăng"], 0)
    assert res[0]["doi_hinh"]["ten"].startswith("Đao Phủ Azir")
    assert abs(res[0]["diem"] - 12.89) < 0.01 and abs(res[0]["diem_an"] - 7.4) < 0.01
    assert res[1]["doi_hinh"]["ten"] == "Thần Rừng Kha'Zix" and abs(res[1]["diem_an"] - 8.8) < 0.01
    double = e.emblem_rank(["Ấn Đao Phủ", "Ấn Đao Phủ"], 0)
    assert len(double[0]["an"]) == 1
    assert len(e.emblem_rank([], 2)) == 19


def test_aug_plan():
    p = e.aug_plan("💰 Vàng / Kinh tế", "Vàng", "2-1", "Trên 70 máu")
    assert "lên 8" in p["theo_bac"].lower() and p["doi_hinh"]
    assert e.aug_plan("không có", "Vàng", "2-1", "Trên 70 máu") is None


def test_advise_bundle():
    st = e.GameState(units=["Azir"], parts=["NeedlesslyLargeRod"], items=["Emblem_Executioner"],
                     offered=["DA_PandorasBench", "DA_ExplosiveGrowth"], stage=3, rnd=2, gold=40, level=6)
    a = e.advise(st)
    for k in ("doi_hinh", "roll", "nhip", "loi", "do", "toc_he", "an"):
        assert k in a
    assert len(a["loi"]) == 2 and a["an"]


# ------------------------------------------------------------------ luyện tập & nhật ký
def test_quiz():
    qs = e.quiz_pick(10, seed=1)
    assert len(qs) == 10 and len({q["id"] for q in qs}) == 10
    for q in qs + e.recipe_questions(seed=3):
        assert 0 <= q["dap_an"] < len(q["lua_chon"])
    res = e.quiz_score(qs, {q["id"]: q["dap_an"] for q in qs})
    assert res["phan_tram"] == 100 and res["dung"] == 10
    assert e.quiz_score(qs, {})["phan_tram"] == 0
    assert e.quiz_pick(10, seed=1) == qs


def test_stats_and_best_fit():
    rows = [{"doi_hinh": "A", "hang": 1, "loi": "X; Y"}, {"doi_hinh": "A", "hang": 3, "loi": "X"},
            {"doi_hinh": "A", "hang": 5, "loi": ""}, {"doi_hinh": "B", "hang": "2.0", "loi": "Y"},
            {"doi_hinh": "B", "hang": "abc"}, {"doi_hinh": "C", "hang": 9}]
    s = {x["ten"]: x for x in e.stats_by(rows, "doi_hinh")}
    assert s["A"]["so_van"] == 3 and s["A"]["hang_tb"] == 3.0 and s["A"]["top4"] == 67 and s["A"]["top1"] == 33
    assert s["B"]["so_van"] == 1 and "C" not in s
    lo = {x["ten"]: x for x in e.stats_by(rows, "loi")}
    assert lo["X"]["so_van"] == 2 and lo["Y"]["so_van"] == 2
    assert e.best_fit(rows)["ten"] == "A"
    assert e.best_fit(rows, min_games=5) is None
