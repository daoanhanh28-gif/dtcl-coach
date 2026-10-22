# ĐTCL Coach v1.4 (2026-10-22) — điểm vào của web
# Chạy local:  streamlit run app.py
import streamlit as st

st.set_page_config(page_title="ĐTCL Coach", page_icon="♜", layout="wide")

from core import auth, config, db, engine, llm, ui  # noqa: E402

# Bộ dữ liệu theo bản vá: chọn ở thanh bên, hoặc mở link ?ban=18.3b ở tab khác để xem bản cũ song song.
if "bo" not in st.session_state:
    q = st.query_params.get("ban")
    st.session_state["bo"] = q if q in config.BO_DU_LIEU else config.BO_MAC_DINH
if st.query_params.get("ban") != st.session_state["bo"]:
    st.query_params["ban"] = st.session_state["bo"]

ui.setup_page()
auth.restore_session()     # có vé ghi nhớ hợp lệ → vào thẳng, không cần đăng nhập lại
auth.sync_cookie()

if not auth.current_user():
    left, right = st.columns([1.35, 1], gap="large")
    with left:
        ui.login_panel()
    with right:
        st.markdown("<div style='height:48px'></div>", unsafe_allow_html=True)
        st.markdown("## Đăng nhập")
        st.caption("Nhập tên để nhật ký ván đấu ghi đúng người.")
        auth.login_form()
    ui.footer()
    st.stop()

user = auth.current_user()
pages = [
    st.Page("views/cam_nang.py", title="Cẩm nang Thách Đấu", icon="👑", default=True),
    st.Page("views/doi_hinh.py", title="Đội hình meta", icon="🏆"),
    st.Page("views/tro_ly.py", title="Trợ lý ván đấu", icon="🧭"),
    st.Page("views/phan_tich.py", title="Phân tích bản cập nhật", icon="📈"),
    st.Page("views/loi.py", title="Lõi nâng cấp", icon="✨"),
    st.Page("views/trang_bi.py", title="Trang bị & Ấn", icon="⚔️"),
    st.Page("views/ban_co.py", title="Bàn cờ & xếp vị trí", icon="🗺️"),
    st.Page("views/kinh_te.py", title="Kinh tế & nhịp ván", icon="💰"),
    st.Page("views/luyen_tap.py", title="Luyện tập", icon="🎯"),
    st.Page("views/nhat_ky.py", title="Nhật ký ván đấu", icon="📒"),
    st.Page("views/kien_thuc.py", title="Kiến thức & tra cứu", icon="📚"),
]
nav = st.navigation(pages)

with st.sidebar:
    st.markdown(f"**{user['name']}**" + (" · chủ web" if user["admin"] else ""))
    st.selectbox("Bản dữ liệu", list(config.BO_DU_LIEU), key="bo",
                 format_func=lambda b: config.BO_DU_LIEU[b][1],
                 help="Mỗi tab trình duyệt chọn bản riêng. Muốn vừa đánh vừa so: mở thêm 1 tab bằng link bên dưới.")
    khac = [b for b in config.BO_DU_LIEU if b != st.session_state["bo"]]
    if khac:
        st.markdown(f"<a href='?ban={khac[0]}' target='_blank' style='font-size:.85rem'>↗ Mở bản {khac[0]} ở tab mới</a>",
                    unsafe_allow_html=True)
    if st.session_state["bo"] != config.BO_MAC_DINH:
        st.warning(f"Đang xem {config.BO_DU_LIEU[st.session_state['bo']][1]}. "
                   f"Bản đang chạy trên máy chủ: {config.BO_MAC_DINH}.", icon="🕘")
    m = engine.data()["meta"]
    ai = f"{llm.provider()} · {llm.model_name()}" if llm.is_online() else "chưa bật (lời giải thích soạn sẵn)"
    st.caption(f"Mùa {m['mua']} · số liệu bản {m['phien_ban']}" + (f" · thay đổi {m['ban_moi']}" if m.get("ban_moi") else "")
               + f"\n\nAI: {ai}\n\nNhật ký: {db.backend()}")
    if st.button("Đăng xuất", use_container_width=True):
        auth.logout()
    st.caption(f"{config.APP_NAME} {config.VERSION_LABEL}")

nav.run()
ui.footer()
