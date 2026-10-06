# ĐTCL Coach v1.1 (2026-10-06) — điểm vào của web
# Chạy local:  streamlit run app.py
import streamlit as st

st.set_page_config(page_title="ĐTCL Coach", page_icon="♜", layout="wide")

from core import auth, config, db, engine, llm, ui  # noqa: E402

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
    st.Page("views/doi_hinh.py", title="Đội hình meta", icon="🏆", default=True),
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
    m = engine.data()["meta"]
    st.markdown(f"**{user['name']}**" + (" · chủ web" if user["admin"] else ""))
    ai = f"{llm.provider()} · {llm.model_name()}" if llm.is_online() else "chưa bật (lời giải thích soạn sẵn)"
    st.caption(f"Mùa {m['mua']} · bản {m['phien_ban']}\n\nAI: {ai}\n\nDữ liệu: {db.backend()}")
    if st.button("Đăng xuất", use_container_width=True):
        auth.logout()
    st.caption(f"{config.APP_NAME} {config.VERSION_LABEL}")

nav.run()
ui.footer()
