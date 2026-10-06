# ĐTCL Coach v1.0 (2026-10-06) — trang Bàn cờ & xếp vị trí (bàn 4×7 bấm để đặt tướng)
import streamlit as st

from core import engine, ui

d = engine.data()
kt = d["hd_kien_thuc"]
ui.header("Bàn cờ & xếp vị trí",
          "Chọn tướng rồi bấm vào ô để đặt; bấm lại ô có tướng để bỏ. Có mẫu xếp chuẩn theo đội hình và theo tình huống.")

st.markdown("""<style>
.st-key-hexgrid [data-testid="stHorizontalBlock"]{flex-wrap:nowrap!important;gap:4px!important;}
.st-key-hexgrid [data-testid="stColumn"]{min-width:0!important;width:auto!important;flex:1 1 0!important;}
.st-key-hexgrid button{padding:4px 2px!important;min-height:44px;font-size:.72rem!important;line-height:1.1;
white-space:normal!important;border-radius:12px!important;}
.st-key-hexgrid p{font-size:.72rem!important;}
</style>""", unsafe_allow_html=True)

st.session_state.setdefault("bc_board", {})
board: dict = st.session_state["bc_board"]
champs = sorted(d["tuong"], key=lambda c: (c["gia"], c["ten"]))

tab1, tab2 = st.tabs(["Bàn của bạn", "Mẫu theo tình huống"])

with tab1:
    c1, c2, c3 = st.columns([1.4, 1.4, 1])
    pick = c1.selectbox("Tướng sẽ đặt", [c["id"] for c in champs],
                        format_func=lambda x: f"{engine.champ(x)['ten']} · {engine.champ(x)['gia']} vàng", key="bc_pick")
    comp_names = [c["ten"] for c in engine.comps()]
    tpl = c2.selectbox("Tải mẫu theo đội hình", ["—"] + comp_names, key="bc_tpl")
    with c3:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        b1, b2 = st.columns(2)
        if b1.button("Tải", use_container_width=True, disabled=tpl == "—"):
            comp = engine.comp_by_name(tpl)
            st.session_state["bc_board"] = {f"{r},{c}": u for (r, c), u in engine.template_board(comp).items()}
            st.rerun()
        if b2.button("Xoá", use_container_width=True):
            st.session_state["bc_board"] = {}
            st.rerun()

    st.caption("Hàng trên cùng là hàng gần đối thủ nhất.")
    with st.container(key="hexgrid"):
        for r in range(engine.ROWS):
            spec = [1] * engine.COLS + [0.5] if r % 2 == 0 else [0.5] + [1] * engine.COLS
            cols = st.columns(spec)
            cells = cols[:engine.COLS] if r % 2 == 0 else cols[1:]
            for c, col in enumerate(cells):
                k = f"{r},{c}"
                uid = board.get(k)
                label = engine.champ(uid)["ten"] if uid else "＋"
                if col.button(label, key=f"hex_{k}", use_container_width=True,
                              type="primary" if uid else "secondary"):
                    if uid:
                        board.pop(k, None)
                    else:
                        board[k] = pick
                    st.rerun()

    placed = {tuple(map(int, k.split(","))): v for k, v in board.items()}
    if placed:
        st.markdown(ui.board_html(placed), unsafe_allow_html=True)
        units = list(placed.values())
        st.markdown(f"**{len(units)} tướng** · tổng giá {sum(engine.champ(u)['gia'] for u in units)} vàng")
        st.markdown("<div class='dc-row'>" + "".join(ui.trait_chip(t["id"], t["so"], t["kich_hoat"])
                                                     for t in engine.board_traits(units)) + "</div>", unsafe_allow_html=True)
        tips = []
        for (r, c), u in placed.items():
            ch = engine.champ(u)
            if ch.get("tam_danh", 1) >= 4 and r == 0:
                tips.append(f"{ch['ten']} đánh xa đang đứng hàng đầu — nên lùi về hàng sau.")
            if ch.get("tam_danh", 1) <= 1 and r == 3 and len(placed) >= 4:
                tips.append(f"{ch['ten']} đánh gần đang đứng hàng cuối — nên đưa lên hàng trên.")
        if any(t == "Lunar" for u in units for t in engine.champ(u).get("toc_he", [])):
            tips.append("Có tướng Mặt Trăng: đặt chủ lực sát bên để nhận Tốc Độ Đánh + SMPT.")
        for t in tips:
            st.markdown(f"- {t}")

with tab2:
    tpls = engine.board_templates()
    name = st.selectbox("Kiểu xếp vị trí", [t["ten"] for t in tpls], key="bc_kieu")
    t = next(x for x in tpls if x["ten"] == name)
    st.markdown(ui.board_html({}, labels=t["luoi"]), unsafe_allow_html=True)
    ui.note(t["ghi_chu"])

st.markdown("### 10 nguyên tắc triển khai của cao thủ")
for i, x in enumerate(kt["xep_vi_tri"], 1):
    st.markdown(f"{i}. {x}")
st.markdown("### Đọc bàn đối thủ")
for x in d["meo"]["doc_ban_doi_thu"]:
    st.markdown(f"- {x}")

ui.source_note()
