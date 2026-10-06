# ĐTCL Coach v1.0 (2026-10-06) — AI diễn giải lời khuyên (Gemini); phần tính toán đã xong ở engine
"""AI chỉ DIỄN GIẢI kết quả luật đã tính, không tự quyết định. Không có khoá → trả lời soạn sẵn."""
from __future__ import annotations

from core import engine, llm

SYSTEM = (
    "Bạn là huấn luyện viên Đấu Trường Chân Lý (Teamfight Tactics) cấp Thách Đấu, nói tiếng Việt, "
    "dùng đúng tên tướng / trang bị / lõi bản Việt của server VN. Người chơi muốn lời khuyên NGẮN GỌN, "
    "đi thẳng trọng tâm, dùng được ngay. Bạn nhận kết quả mà bộ luật của web đã tính sẵn — KHÔNG được đổi "
    "kết luận (đội hình, hành động, lõi, đồ), chỉ giải thích vì sao và nhắc 2–3 điều cần để ý trong 1–2 vòng tới. "
    "Không bịa số liệu. Tối đa 120 chữ, chia gạch đầu dòng."
)


def summary_text(st: engine.GameState, adv: dict) -> str:
    lines = [f"Vòng {st.stage}-{st.rnd}, cấp {st.level}, {st.gold} vàng, {st.hp} máu, chuỗi {st.streak:+d}."]
    if adv["doi_hinh"]:
        top = adv["doi_hinh"][0]
        lines.append(f"Đội nên đi: {top['comp']['ten']} ({top['comp']['kieu_ten']}). Lý do: {'; '.join(top['ly_do'][:3])}.")
        alt = ", ".join(r["comp"]["ten"] for r in adv["doi_hinh"][1:])
        if alt:
            lines.append(f"Dự phòng: {alt}.")
    r = adv["roll"]
    lines.append(f"Hành động: {r['tieu_de']}. {' '.join(r['ly_do'])}")
    if adv["loi"]:
        lines.append(f"Lõi nên chọn: {adv['loi'][0]['loi']['ten']}.")
    if adv["do"]["uu_tien"]:
        lines.append("Ghép trước: " + ", ".join(f"{x['do']['ten']} cho {x['cho']}" for x in adv["do"]["uu_tien"][:3]) + ".")
    return "\n".join(lines)


def offline_explain(st: engine.GameState, adv: dict) -> str:
    out = []
    if adv["doi_hinh"]:
        c = adv["doi_hinh"][0]["comp"]
        out.append(f"- **{c['ten']}** khớp nhất với tướng và đồ bạn đang có.")
        if c.get("excel", {}).get("khi_nao"):
            out.append(f"- Điều kiện chơi: {c['excel']['khi_nao']}")
    out.append(f"- {adv['roll']['tieu_de']}: {adv['roll']['ly_do'][0] if adv['roll']['ly_do'] else ''}")
    nh = adv.get("nhip") or {}
    if nh.get("mau"):
        out.append(f"- Theo máu: {nh['mau']}")
    return "\n".join(out)


def explain(st: engine.GameState, adv: dict) -> tuple[str, bool]:
    """Trả (lời giải thích, có dùng AI thật không)."""
    if not llm.is_online():
        return offline_explain(st, adv), False
    try:
        txt = llm.chat(SYSTEM, [{"role": "user", "content": summary_text(st, adv)}], temperature=0.4, max_tokens=500)
        return txt, True
    except llm.LLMError as e:
        return offline_explain(st, adv) + f"\n\n_(AI tạm lỗi: {e})_", False
