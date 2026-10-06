# ĐTCL Coach v1.1 (2026-10-06) — kiểm thử giao diện bằng Streamlit AppTest (offline, lưu CSV cục bộ)
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ["LLM_PROVIDER"] = "offline"
for k in ("SHEETS_WEBAPP_URL", "GEMINI_API_KEY", "ACCESS_CODE", "ADMIN_CODE"):
    os.environ.pop(k, None)
os.chdir(ROOT)

import pytest  # noqa: E402
from streamlit.testing.v1 import AppTest  # noqa: E402

from core import config  # noqa: E402

PAGES = ["views/doi_hinh.py", "views/tro_ly.py", "views/phan_tich.py", "views/loi.py", "views/trang_bi.py", "views/ban_co.py",
         "views/kinh_te.py", "views/luyen_tap.py", "views/nhat_ky.py", "views/kien_thuc.py"]


def setup_module():
    shutil.rmtree(config.LOCAL_LOG_DIR, ignore_errors=True)


def _page(path, admin=False):
    """Chạy riêng 1 trang như người đã đăng nhập."""
    at = AppTest.from_file(str(ROOT / path), default_timeout=60)
    at.session_state["user"] = {"name": "Peach Test", "admin": admin}
    return at


def _ok(at):
    assert not at.exception, [e.value for e in at.exception]


def test_login_screen_and_login():
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    _ok(at)
    at.text_input[0].input("Peach")
    at.text_input[1].input("dtcl2026")
    at.button[0].click().run()
    _ok(at)
    assert at.session_state["user"]["name"] == "Peach"


def test_wrong_code_rejected():
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    at.text_input[0].input("Peach")
    at.text_input[1].input("sai-ma")
    at.button[0].click().run()
    assert "user" not in at.session_state
    assert any("Sai mã" in e.value for e in at.error)


def test_app_shell_shows_version():
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
    at.session_state["user"] = {"name": "Peach Test", "admin": False}
    at.run()
    _ok(at)
    text = " ".join(c.value for c in at.caption) + " ".join(m.value for m in at.markdown)
    assert config.VERSION in text


@pytest.mark.parametrize("path", PAGES)
def test_every_page_renders(path):
    at = _page(path).run()
    _ok(at)


def test_doi_hinh_filters():
    at = _page("views/doi_hinh.py").run()
    at.multiselect(key="dh_tier").set_value(["S"]).run()
    _ok(at)
    at.selectbox(key="dh_style").set_value("Lên 8 nhanh").run()
    _ok(at)


def test_tro_ly_full_flow():
    at = _page("views/tro_ly.py").run()
    at.selectbox(key="tl_round").set_value("4-2")
    at.number_input(key="tl_level").set_value(7)
    at.number_input(key="tl_gold").set_value(55)
    at.number_input(key="tl_hp").set_value(45)
    at.number_input(key="tl_streak").set_value(-3)
    at.multiselect(key="tl_units").set_value(["Azir", "Soraka", "Zyra", "Rammus"])
    at.number_input(key="tl_p_NeedlesslyLargeRod").set_value(2)
    at.number_input(key="tl_p_SparringGloves").set_value(1)
    at.multiselect(key="tl_items").set_value(["Emblem_Executioner"])
    at.multiselect(key="tl_offer").set_value(["DA_PandorasBench", "DA_ExplosiveGrowth", "DA_GroupHugI"])
    at.run()
    _ok(at)
    md = " ".join(m.value for m in at.markdown)
    assert "Lúc này nên làm gì" in md and "Nên đi đội nào" in md and "Chọn lõi nào" in md
    assert "dc-ans" in md and "Hoàn chỉnh" in " ".join(t.label for t in at.tabs)
    at.button(key="tl_ai").click().run()
    _ok(at)
    assert at.session_state["tl_ai_txt"][1] is False      # offline → lời giải thích soạn sẵn


def test_tro_ly_image_pickers():
    at = _page("views/tro_ly.py").run()
    _ok(at)
    at.button(key="pku3_Azir").click().run()            # bấm hình Azir (3 vàng) → chọn
    _ok(at)
    assert at.session_state["tl_units"] == ["Azir"]
    at.button(key="pku3_Azir").click().run()            # bấm lại → bỏ
    assert at.session_state["tl_units"] == []
    at.button(key="pkp_BFSword").click().run()
    at.button(key="pkp_BFSword").click().run()
    _ok(at)
    assert at.session_state["tl_p_BFSword"] == 2
    at.button(key="pke_Emblem_Executioner").click().run()
    assert at.session_state["tl_items"] == ["Emblem_Executioner"]
    at.button(key="tl_clear_p").click().run()
    assert at.session_state["tl_p_BFSword"] == 0
    at.button(key="pkan_Emblem_Executioner").click().run()
    at.button(key="pkan_Emblem_Lunar").click().run()
    _ok(at)
    assert at.session_state["an_1"] == "Ấn Đao Phủ" and at.session_state["an_2"] == "Ấn Mặt Trăng"
    md = " ".join(m.value for m in at.markdown)
    assert "Cấp 8" in md and "Cấp 9" in md
    at.button(key="an_clear").click().run()
    assert at.session_state["an_1"] == "— Không có —"


def test_phan_tich_page():
    at = _page("views/phan_tich.py").run()
    _ok(at)
    md = " ".join(m.value for m in at.markdown)
    assert "Dễ top 1" in md and "Mạnh mà ít người chơi" in md and "Được lợi" in md
    assert "dc-up" in md and "dc-down" in md


def test_trang_bi_champ_items():
    at = _page("views/trang_bi.py").run()
    at.button(key="pktc3_Azir").click().run()
    _ok(at)
    assert at.session_state["td_champ"] == "Azir"
    assert any("Đồ hay lên nhất" in m.value for m in at.markdown)
    at.button(key="pktd_BFSword").click().run()
    at.button(key="pktd_SparringGloves").click().run()
    _ok(at)
    assert any("Vô Cực Kiếm" in m.value for m in at.markdown)


def test_tro_ly_emblem_and_aug_tabs():
    at = _page("views/tro_ly.py").run()
    at.selectbox(key="an_1").set_value("Ấn Đao Phủ")
    at.selectbox(key="an_2").set_value("Ấn Mặt Trăng")
    at.run()
    _ok(at)
    assert any("Đao Phủ Azir" in m.value for m in at.markdown)
    at.selectbox(key="lc_loai").set_value("🧩 Mảnh trang bị").run()
    _ok(at)


def test_trang_bi_combine():
    at = _page("views/trang_bi.py").run()
    at.selectbox(key="td_a").set_value("BFSword")
    at.selectbox(key="td_b").set_value("SparringGloves")
    at.run()
    _ok(at)
    assert any("Vô Cực Kiếm" in m.value for m in at.markdown)


def test_ban_co_place_and_template():
    at = _page("views/ban_co.py").run()
    at.selectbox(key="bc_pick").set_value("Azir").run()
    at.button(key="hex_3,0").click().run()
    _ok(at)
    assert at.session_state["bc_board"] == {"3,0": "Azir"}
    at.button(key="hex_3,0").click().run()
    assert at.session_state["bc_board"] == {}
    at.selectbox(key="bc_tpl").set_value(at.selectbox(key="bc_tpl").options[1]).run()
    tai = [b for b in at.button if b.label == "Tải"][0]
    tai.click().run()
    _ok(at)
    assert len(at.session_state["bc_board"]) >= 7


def test_kinh_te_calculators():
    at = _page("views/kinh_te.py").run()
    at.number_input(key="kt_gold").set_value(50)
    at.number_input(key="kt_streak").set_value(6)
    at.run()
    _ok(at)
    assert any("+14 vàng" in m.value for m in at.markdown)
    at.number_input(key="kt_lv").set_value(4)
    at.number_input(key="kt_cost").set_value(5)
    at.run()
    _ok(at)
    assert at.warning


def test_luyen_tap_submit_and_log():
    at = _page("views/luyen_tap.py").run()
    _ok(at)
    assert len(at.radio) == 10
    at.button[1].click().run()      # Nộp bài (để trống) → 0 điểm nhưng không lỗi
    _ok(at)
    res, _ = at.session_state["lt_result"]
    assert res["tong"] == 10
    assert (config.LOCAL_LOG_DIR / "LuyenTap.csv").exists()


def test_nhat_ky_save_and_stats():
    at = _page("views/nhat_ky.py").run()
    for place in (2, 3, 6):
        at.selectbox[0].set_value(at.selectbox[0].options[0])
        at.selectbox[1].set_value(place)
        at.button[0].click().run()
        _ok(at)
    md = " ".join(m.value for m in at.markdown)
    assert "Đội hợp tay nhất" in md


def test_kien_thuc_search():
    at = _page("views/kien_thuc.py").run()
    at.text_input(key="kt_q").input("Azir").run()
    _ok(at)
