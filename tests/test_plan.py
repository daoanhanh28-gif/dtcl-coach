# ĐTCL Coach v1.4 (2026-10-22) — kiểm thử form theo vòng, tối ưu Ấn theo mốc tộc/hệ, phân tích bản cập nhật
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import engine as E  # noqa: E402
from core import plan as P  # noqa: E402


def test_tiers_and_counts():
    assert P.trait_moc("Executioner") == [2, 3, 4]
    assert P.tiers("Executioner", 1) == 0 and P.tiers("Executioner", 3) == 2 and P.tiers("Executioner", 9) == 3
    c = P.counts(["Azir", "Azir", "Veigar"], ["Lunar"])
    assert c["Lunar"] == 1 and c["Blackthorn"] == 2       # Azir đếm 1 lần dù nhập 2


def test_cell_mapping_and_details():
    import importlib.util
    spec = importlib.util.spec_from_file_location("bct", ROOT / "tools" / "build_chi_tiet.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert m.cell_to_rc(1) == [3, 0] and m.cell_to_rc(28) == [0, 6] and m.cell_to_rc(25) == [0, 3]
    det = E.data()["metatft_chi_tiet"]
    assert len(det["cum"]) >= 50 and len(det["do_tuong"]) >= 60
    for c in det["cum"].values():
        for u, (r, col) in c["vi_tri"].items():
            assert u in E.data()["champ"] and 0 <= r < 4 and 0 <= col < 7
        for lv, boards in c["som"].items():
            assert lv in ("4", "5", "6", "7")
            for b in boards:
                assert all(u in E.data()["champ"] for u in b["tuong"]) and b["so_tran"] > 0


def test_place_no_overlap_and_ranges():
    units = ["Azir", "Rammus", "Soraka", "Teemo", "Veigar", "Zyra", "Fiddlesticks", "Kennen"]
    b = P.place(units, "425013")
    assert sorted(b.values()) == sorted(units)
    assert len(b) == len(set(b))
    assert b and all(0 <= r < 4 and 0 <= c < 7 for r, c in b)
    rammus = next(rc for rc, u in b.items() if u == "Rammus")
    assert rammus[0] == 0                                # đỡ đòn đứng hàng đầu


def test_stage_boards_every_comp():
    for comp in E.comps():
        sb = P.stage_boards(comp)
        g = sb["giai_doan"]
        assert [x["ten"] for x in g] == ["Cấp 4", "Cấp 5", "Cấp 6", "Cấp 7", "Hoàn chỉnh"]
        assert set(g[-1]["tuong"]) <= set(comp["tuong"]) and len(g[-1]["tuong"]) >= 5
        for x in g:
            assert len(x["ban_co"]) == len(set(x["tuong"]))
            assert set(x["tam"]).isdisjoint(set(comp["tuong"]))
            E.parse_round(x["vong"])


def test_stage_emblem_holder_temporary():
    comp = E.comps()[0]                                   # Đao Phủ Azir
    sb = P.stage_boards(comp, ["Emblem_Lunar"])
    for x in sb["giai_doan"]:
        for a in x["an"]:
            if a["nguoi_deo"] is None:                     # cất Ấn chờ người cầm cuối
                assert a["chuyen_cho"] and a["sau"] == a["truoc"]
                continue
            assert "Lunar" not in E.champ(a["nguoi_deo"])["toc_he"]
            assert a["nguoi_deo"] in x["tuong"]
            assert a["sau"] == a["truoc"] + 1
            if a["tam"]:
                assert a["nguoi_deo"] in x["tam"]          # chỉ đeo tạm cho tướng sẽ bán
    final = sb["giai_doan"][-1]
    assert all(a["nguoi_deo"] and not a["tam"] for a in final["an"])


def test_emblem_plan_holder_and_breakpoint():
    c = E.data()["hd_an"]["doi_hinh"][0]                 # Đao Phủ Azir (Excel)
    units, core = P.an_comp_units(c)
    ep = P.emblem_plan(units, ["Emblem_Executioner"], core, 8)
    a = ep["an"][0]
    assert a["nguoi_deo"] and "Executioner" not in E.champ(a["nguoi_deo"])["toc_he"]
    assert a["truoc"] == 3 and a["sau"] == 4 and a["len_moc"] and a["moc_dat"] == 4
    assert len(ep["doi"]) == 8 and all(u in ep["doi"] for u in core)


def test_emblem_plan_never_drops_main_or_emblem_trait():
    for c in E.data()["hd_an"]["doi_hinh"]:
        units, core = P.an_comp_units(c)
        for lv in (8, 9):
            ep = P.emblem_plan(units, ["Emblem_Executioner", "Emblem_Lunar"], core, lv)
            extra = [E.item(e)["toc_he"] for e in ep["nguoi_deo"]]
            before = P.counts(ep["doi"], extra)
            keep = set(P._main_traits(ep["doi"])) | {"Executioner", "Lunar"}
            for g in ep["goi_y"]:
                assert g["them"] not in ep["doi"] and (g["bo"] is None or g["bo"] not in core)
                assert E.champ(g["them"])["gia"] <= (4 if lv == 8 else 5)
                nb = [u for u in ep["doi"] if u != g["bo"]] + [g["them"]]
                after = P.counts(nb, [E.item(e)["toc_he"] for e in g["nguoi_deo"]])
                for t in keep:
                    assert P.tiers(t, after[t]) >= P.tiers(t, before[t]), (c["ten"], g, t)
                assert len(nb) <= lv


def test_emblem_plan_level9_adds_unit():
    c = next(x for x in E.data()["hd_an"]["doi_hinh"] if x["ten"].startswith("Thần Rừng Kha"))
    units, core = P.an_comp_units(c)
    ep = P.emblem_plan(units, ["Emblem_Executioner"], core, 9)
    assert ep["goi_y"] and ep["goi_y"][0]["bo"] is None   # còn 1 ô trống ở cấp 9 → thêm tướng


def test_emblem_with_whole_team_having_trait():
    ep = P.emblem_plan(["Azir"], ["Emblem_Blackthorn"], ["Azir"], 8)
    assert ep["an"][0]["khong_ai_deo"]


def test_patch_rows_and_categories():
    from core import config

    with config.voi_bo("18.4b"):
        _check_patch_full()
    _check_patch_185()


def _check_patch_full():
    """Bộ 18.4b: bảng VN đủ 32 đội → mọi nhóm đều có đội."""
    rows = P.patch_rows()
    assert len(rows) == 19
    az = next(r for r in rows if r["ten"].startswith("Đao Phủ Azir"))
    assert az["vn"] == {"hang_tb": 2.78, "top4": 84.3, "ti_le": 1.9}
    assert P.trend_of("↑ 18.4: …") == 2 and P.trend_of("→ 18.4: … MẠNH LÊN") == 0.5 and P.trend_of("↓ x") == -2
    pa = P.patch_analysis()
    assert set(pa) == {k for k, _, _ in P.CATEGORIES} == {k for k, _, _ in P.categories()}
    assert all(pa[k] for k in ("nen_choi", "duoc_loi", "manh_nhat", "de_top1", "de_top4", "an_spam", "de_choi", "nen_tranh"))
    assert pa["manh_nhat"][0]["ten"].startswith("Đao Phủ Azir")
    assert all(r["xu_huong"] > 0 for r in pa["duoc_loi"])
    assert all((r["vn"]["ti_le"] or 0) < 0.5 and r["vn"]["hang_tb"] <= 3.35 for r in pa["an_spam"])
    top1 = [r["metatft"]["top1"] for r in pa["de_top1"]]
    assert top1 == sorted(top1, reverse=True)


def _check_patch_185():
    """Bộ 18.5 (mặc định): ghi chú chính thức, xu hướng tự tính, số VN còn ít nhưng trang không lỗi."""
    rows = P.patch_rows()
    assert len(rows) == 19 and "18.5" in P.categories()[0][1]
    alune = next(r for r in rows if r["ten"].startswith("Tiên Phong Alune"))
    assert alune["xu_huong"] >= 1 and alune["vn"]["hang_tb"] == 3.63
    pa = P.patch_analysis()
    assert pa["duoc_loi"] and all(r["xu_huong"] > 0 for r in pa["duoc_loi"])


def test_patch_changes_have_images():
    ch = P.patch_changes()
    assert any(x["huong"] == "tang" for x in ch) and any(x["huong"] == "giam" for x in ch)
    for x in ch:
        if x["loai"] in ("tuong", "toc_he"):
            assert x["ref"], x


def test_best_items():
    bi = P.best_items("Azir")
    assert bi and bi["do"] and all(i in E.data()["item"] for i in bi["do"])
    assert P.best_items("KhôngCó") is None


def test_old_data_set_kept():
    """Bộ 18.3b cũ vẫn đọc được song song với bộ mới, số liệu không lẫn nhau."""
    from core import config

    new = P.patch_rows()
    with config.voi_bo("18.3b"):
        old = P.patch_rows()
        assert E.data()["meta"]["bo"] == "18.3b" and E.data()["ban_cap_nhat"]["phien_ban"] == "18.4"
        az = next(r for r in old if r["ten"].startswith("Đao Phủ Azir"))
        assert az["vn"] == {"hang_tb": 2.69, "top4": 84.8, "ti_le": 1.15} and az["xu_huong"] == -1
        assert P.patch_analysis()["manh_nhat"][0]["ten"].startswith("Đao Phủ Azir")
        assert "18.4" in P.categories()[0][1]
    assert E.data()["meta"]["bo"] == config.BO_MAC_DINH and new is P.patch_rows()


def test_data_sets_185_default():
    """18.5 là mặc định (đang chạy); 18.4b giữ làm bản trước, có cẩm nang, bảng VN đủ và thống kê Ấn."""
    from core import config

    assert config.BO_MAC_DINH == "18.5" and set(config.BO_DU_LIEU) == {"18.4b", "18.5", "18.3b"}
    d = E.data()
    assert d["meta"]["bo"] == "18.5" and d["meta"]["phien_ban"] == "18.5" and d["ban_cap_nhat"]["phien_ban"] == "18.5"
    assert d["cam_nang"]["phien_ban"] == "18.5" and d["cam_nang"]["loi_top1"] and d["cam_nang"]["tinh_linh"]
    assert all(x["id"] in d["aug"] for x in d["cam_nang"]["loi_top1"])
    assert all(i in d["aug"] for x in d["cam_nang"]["cap_loi"] for i in x["loi"])
    with config.voi_bo("18.4b"):
        d4 = E.data()
        assert d4["meta"]["bo"] == "18.4b" and len(d4["vn_opgg"]["doi_hinh"]) >= 20 and d4["an_thong_ke"]["an"]
    with config.voi_bo("18.3b"):
        assert E.data()["vn_opgg"] == {} and E.data()["cam_nang"] == {}


def test_bien_dong_and_spam_185():
    from core import cam_nang as C

    bd = C.bien_dong()
    assert bd["ban_truoc"] == "18.4b"
    assert bd["len"] and all(r["chenh"] < 0 for r in bd["len"]) and bd["len"][0]["tuong"]
    assert bd["xuong"] and all(r["chenh"] > 0 for r in bd["xuong"])
    assert any("Azir" in r["tuong"] for r in bd["xuong"])               # 18.5 giảm Azir
    spam = C.manh_it_nguoi_quoc_te()
    assert spam and all(c["ti_le_qt"] < 1.5 and c["so_lieu"]["hang_tb"] <= 4.40 for c in spam)
    top = C.top_quoc_te()
    assert [c["so_lieu"]["hang_tb"] for c in top] == sorted(c["so_lieu"]["hang_tb"] for c in top)


def test_cam_nang_lists():
    from core import cam_nang as C
    from core import config

    with config.voi_bo("18.4b"):
        top = C.top_manh()
        assert top and all(r["ti_le"] >= 0.3 for r in top)
        assert [r["hang_tb"] for r in top] == sorted(r["hang_tb"] for r in top)
        rare = C.manh_it_nguoi()
        assert rare and all(r["ti_le"] < 0.3 and r["hang_tb"] <= 3.6 for r in rare)
        easy = C.de_vao_top()
        assert easy and all(r["top4"] >= 65 for r in easy) and easy[0]["dieu_kien"]
        moc = C.moc_len_cap()
        f8 = next(x for x in moc if x["loi_choi"] == "Lên nhanh cấp 8")
        assert f8["cap"][8] == "4-2"


def test_flex_emblem_around_meta_carry():
    from core import flex as F

    res = F.flex_an(["Emblem_Executioner"])
    assert res and len({r["chu_luc"] for r in res}) == len(res)          # mỗi chủ lực 1 đội
    azir = next(r for r in res if r["chu_luc"] == "Azir")
    assert dict((w, e) for e, w in azir["nguoi_cam"]).get("Zyra") == "Emblem_Executioner"   # Ấn Đao Phủ → Zyra
    assert azir["moc"][0]["len_moc"]
    two = F.flex_an(["Emblem_Invoker", "Emblem_Invoker"])
    assert two and len(two[0]["nguoi_cam"]) == 2 and len({w for _, w in two[0]["nguoi_cam"]}) == 2
    assert F.an_nguoi_cam("Emblem_Defender")[0]["tuong"] == "Rengar"
