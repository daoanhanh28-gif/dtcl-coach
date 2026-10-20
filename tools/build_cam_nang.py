# ĐTCL Coach v1.3 (2026-10-20) — dựng data/ban/18.4b/cam_nang.json: tempo Thách Đấu, lõi top 1, cặp lõi, bùa (Tinh Linh) theo giai đoạn
"""
Chạy:  python tools/build_cam_nang.py
Nội dung chữ viết tay ở dưới (nhận định chuyên môn, ghi rõ là nhận định). Số liệu đi kèm (mốc lên cấp, đội hình, bảng lõi)
được trang Cẩm nang tự tính từ data/*.json của bộ đang xem — không bịa số.
Bùa = Tinh Linh bán trong cửa hàng (tên trong game: Tinh Linh). Danh sách + bậc lấy từ MetaTFT “Wisp Tier List”
(chuyên gia Spencer, 20/10/2026), tên và số theo dữ liệu game bản đang chạy (Community Dragon) → tools/raw/tinh_linh_184b.txt.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "tools" / "raw"
DICH_TAM = {"Supercritical", "Truce", "Returning Friend", "Golden Road", "Minor Blood Ritual", "Sinister Deal"}
NHOM = {"Champion": "Tướng", "Combat": "Giao tranh", "GoldXP": "Vàng / XP", "Item": "Trang bị", "Misc": "Vật phẩm",
        "Risky": "Mạo hiểm", "Shop": "Cửa hàng"}

TEMPO = {
    "gioi_thieu": ("“Tempo” là tiêu vàng đúng lúc để đội đủ mạnh ở đúng mốc, thay vì giữ vàng tới cuối. Người chơi Thách Đấu "
                   "không lên cấp theo thói quen: họ nhìn máu, chuỗi, sức mạnh bàn cờ và phòng đấu rồi quyết định mỗi vòng. "
                   "Bảng mốc lên cấp bên dưới tính từ số liệu thật của các đội meta (MetaTFT, Bạch Kim+)."),
    "nguyen_tac": [
        {"k": "1. Mạnh nhất có thể ở giai đoạn 2", "v": "Đặt lên bàn những tướng 2 sao mạnh nhất bạn có, không cần đúng tộc/hệ. Ghép ngay 1–2 món hoàn chỉnh từ vòng đi chợ cho tướng đang gánh. Thắng 3–4 trận đầu = vài chục vàng và nhiều máu."},
        {"k": "2. Chuỗi rõ ràng — thắng hẳn hoặc thua hẳn", "v": "Đang chuỗi thắng: tiêu vàng (mua XP 2-1/2-5, roll nhẹ) để giữ chuỗi. Đang chuỗi thua: đừng nửa vời — giữ vàng, bán tướng lẻ, chỉ đặt đủ để không mất quá nhiều máu. Phá chuỗi giữa chừng là mất cả vàng lẫn máu."},
        {"k": "3. Giữ mốc lãi 50 trước khi roll lớn", "v": "Ngoài các lần all-in, cố đưa vàng về ≥ 50 trước giai đoạn 4. Mỗi 10 vàng = +1 vàng/vòng, tối đa +5. Chỉ tiêu phần trên 50 khi roll chậm (đội reroll)."},
        {"k": "4. Một lần roll lớn đúng mốc", "v": "Lên nhanh 8: lên 8 ở 4-2 rồi roll mạnh tìm chủ lực 2 sao. Reroll: roll chậm từ khi lên đúng cấp (3-1/3-2 cho đội 1–2 vàng, 3-6 cho đội 3 vàng). Lên 9: chỉ lên ở 5-1 khi bàn cờ đã đủ giữ máu."},
        {"k": "5. Ngưỡng máu quyết định roll", "v": "> 70 máu: được tham lãi, chấp nhận thua vài trận. 40–70: roll vừa đủ để thắng 2/3 trận còn lại của giai đoạn. < 40: roll để ổn định ngay, không giữ lãi. < 25: all-in, mọi vàng biến thành sức mạnh trận này."},
        {"k": "6. Đọc phòng 3 lần", "v": "Xem bàn đối thủ ở 2-1 (ai đang chuỗi), trước khi roll ở 3-2, và ở 4-1 (ai đang chơi cùng chủ lực với bạn). Có ≥ 2 người cùng chủ lực → đổi sang đội khác cùng đồ. Bảng “Mạnh mà ít người chơi” giúp chọn đường tránh tranh."},
        {"k": "7. Đồ quyết định đội, không phải ngược lại", "v": "Giữ thành phần linh hoạt tới 3-2. Đồ vật lý (Kiếm, Cung) → chủ lực SMCK; Gậy, Nước Mắt → chủ lực phép. Chốt chủ lực ở 4-1, ghép đủ 3 món cho chủ lực trước, đỡ đòn sau."},
        {"k": "8. Vòng đi chợ", "v": "Máu thấp được chọn trước — ưu tiên thành phần còn thiếu cho chủ lực. Máu cao: lấy tướng/đồ giúp chuỗi thắng tiếp. Đừng lấy Siêu Xẻng / Chảo nếu chưa biết Ấn nào hợp đội (xem trang Trợ lý → Ấn)."},
        {"k": "9. Bùa (Tinh Linh) theo giai đoạn", "v": "Giai đoạn 2: mua bùa ra vàng / XP / tướng 2 sao (rẻ, lời ngay). Giai đoạn 3: bùa trang bị, tướng 3 vàng 2 sao. Giai đoạn 4–5: bùa giao tranh (làm choáng, lá chắn) khi cần thắng trận quyết định. Xem bảng ở thẻ “Bùa theo giai đoạn”."},
        {"k": "10. Xếp bàn mỗi vòng 4-x", "v": "Trước mỗi trận từ 4-1, nhìn đối thủ sắp gặp: đội sát thủ/nhảy sau lưng → chủ lực vào góc có đỡ đòn che; đội phép lan → giãn hàng sau. Đổi 1–2 ô đúng lúc thắng thêm cả trận."},
    ],
    "lich": [
        {"vong": "1-1 → 1-4", "viec": "Lấy đồ quái rừng. Giữ tướng 1–2 vàng cùng tên để lên 2 sao. Chọn hướng đồ chứ chưa chọn đội."},
        {"vong": "2-1", "viec": "Chọn lõi 1. Lên cấp 4 (mua 1 lần XP) nếu bàn đang mạnh. Bùa: ưu tiên ra tướng 2 sao / XP / vàng."},
        {"vong": "2-2 → 2-5", "viec": "Đang thắng: lên 5 ở 2-5, ghép đồ sớm. Đang thua: giữ vàng lên 30+, đặt đủ tướng để mất ít máu."},
        {"vong": "2-6 → 3-1", "viec": "Đội reroll 1 vàng (Sỏi, Yunara…) lên 5 và bắt đầu roll chậm trên 50 vàng. Đội khác giữ lãi."},
        {"vong": "3-2", "viec": "Chọn lõi 2. Lên 6. Đọc phòng lần 2. Đội reroll 2 vàng (Kayle, Teemo, Warwick) roll chậm."},
        {"vong": "3-5 → 3-7", "viec": "Lên 7 (đội 3 vàng: Azir, Kha'Zix, Rengar bắt đầu roll chậm). Đội lên 8 giữ vàng ~50."},
        {"vong": "4-1", "viec": "Đọc phòng lần 3, chốt chủ lực. Đội lên 8 có ≥ 50 vàng và máu cao có thể lên 8 ngay."},
        {"vong": "4-2", "viec": "Chọn lõi 3. Đội lên 8: lên 8 và roll mạnh tìm chủ lực 4 vàng 2 sao. Đội reroll xong 3 sao thì lên 8 lấy tướng 4 vàng."},
        {"vong": "5-1 → 5-2", "viec": "Đội lên 9 (Draven, Maokai, Alune): lên 9 rồi roll tìm tướng 5 vàng. Đội khác củng cố đồ, nâng 2 sao tướng 4 vàng."},
        {"vong": "6-x", "viec": "Máu thấp: mỗi vòng là trận sinh tử — tiêu hết vàng. Máu cao: lên 10 nếu có lõi/XP, thêm tướng 5 vàng."},
    ],
    "loi_thuong_gap": [
        "Roll ở 3-2 khi máu còn 80 và chưa có cặp tướng nào — tiêu hết vàng mà không lên 2 sao.",
        "Giữ chuỗi thua nhưng vẫn đặt bàn mạnh, thắng 1 trận làm đứt chuỗi.",
        "Ôm Ấn / Siêu Xẻng không biết đeo cho ai — dùng trang Trợ lý → Ấn để chọn đội hợp chủ lực.",
        "Đuổi theo đội đông người chơi nhất (Quái Rừng Maokai 6% người chơi VN) khi đã có 2 người khác chơi.",
        "Lên 9 khi bàn cấp 8 còn yếu — tụt máu nhanh hơn số lợi nhận được.",
    ],
}

LOI_TOP1 = [
    {"id": "DA_TheTraitTree", "vi_sao": "Cho nhiều Ấn cùng lúc — trần sức mạnh cao nhất nếu biết dồn Ấn vào tộc/hệ của 1 chủ lực meta.",
     "khi_nao": "2-1 (bản + ở 3-2)",
     "cach": ["Mở trang Trợ lý → Ấn, bấm các Ấn nhận được: web xếp đội meta và người đeo.",
              "Dồn Ấn để mở mốc cao của chủ lực (Đao Phủ 4 cho Azir/Zyra, Thần Rừng 9 cho Aphelios, Thuật Sĩ 5 cho Ahri/Alune).",
              "Đánh tempo: lên 8 ở 4-1/4-2, mốc tộc cao bù cho việc chưa có tướng 2 sao."],
     "tranh": "Chia Ấn ra nhiều tộc nhỏ — mỗi tộc thêm 1 mốc thấp không đáng bằng 1 mốc cao của chủ lực."},
    {"id": "DA_TacticiansKitchen", "vi_sao": "1 Ấn + Áo Choàng Chiến Thuật (thêm 1 ô tướng) sau 3 vòng: cấp 8 có 9 tướng.",
     "khi_nao": "2-1",
     "cach": ["Chơi đội lên nhanh 8/9 — ô tướng thêm có giá trị nhất khi bàn đã có tướng 4–5 vàng.",
              "Ô thêm dùng để mở mốc tộc/hệ (Quái Rừng 7, Thần Rừng 7/9, Tiên Phong 4).",
              "Giữ máu tới 4-2, không cần all-in sớm."],
     "tranh": "Đi reroll 1 vàng — ô thêm ít giá trị khi cả đội là tướng rẻ."},
    {"id": "DA_BaronsLair", "vi_sao": "Đỡ đòn ngẫu nhiên + cả đội tăng dần SMCK/SMPT sau 8 giây — càng đánh lâu càng mạnh.",
     "khi_nao": "3-2 / 4-2",
     "cach": ["Chọn đội có tiền tuyến rất lì để trận kéo dài: Quái Rừng Maokai/Draven, Tiên Phong Alune, Thần Rừng Kha'Zix.",
              "Đồ đỡ đòn nhận được đeo cho tướng đứng trước chịu đòn đầu tiên.",
              "Ưu tiên Giáp Máu Warmog / Thú Tượng cho đỡ đòn để chắc chắn qua mốc 8 giây."],
     "tranh": "Đội sát thương dồn nhanh, mỏng máu — trận kết thúc trước khi lõi kịp mạnh."},
    {"id": "DA_EpicRolldown", "vi_sao": "20 lượt đổi khi đạt cấp 8 = một lần roll lớn miễn phí ~40 vàng.",
     "khi_nao": "3-2",
     "cach": ["Giữ vàng, lên 8 sớm hơn bình thường (4-1, thậm chí 3-6 nếu có Tăng Trưởng Bùng Nổ).",
              "Dùng 20 lượt tìm chủ lực 4 vàng 2 sao: Aphelios, Ahri, Nidalee, Sivir, Soraka, Ezreal.",
              "Vàng giữ lại để lên 9 ở 5-1."],
     "tranh": "Lên 8 muộn ở 5-1 — 20 lượt đổi đến quá trễ để cứu máu."},
    {"id": "DA_ExplosiveGrowth", "vi_sao": "7 XP ngay và 3 vòng tiếp = lên cấp nhanh mà không tốn vàng.",
     "khi_nao": "3-2",
     "cach": ["Đi đội lên nhanh 9: Quái Rừng Maokai / Draven, Thần Rừng Draven, Tiên Phong Alune.",
              "Cấp 7 ở 3-5, cấp 8 ở 4-1 rồi roll; cấp 9 ở 5-1 lấy tướng 5 vàng (Maokai, Draven, Alune, Rồng Ngàn Tuổi).",
              "Vàng tiết kiệm từ XP dùng để roll sớm cho chủ lực."],
     "tranh": "Chọn đội reroll cấp 5/6 — XP thừa vô ích."},
    {"id": "DA_CalculatedLoss", "vi_sao": "Mỗi trận thua: 2 vàng + 1 lượt đổi miễn phí — chuỗi thua có lời hơn hẳn.",
     "khi_nao": "2-1",
     "cach": ["Chủ động chuỗi thua giai đoạn 2–3 (đặt bàn yếu, bán tướng thừa), tích vàng và lượt đổi.",
              "Đội reroll 1–2 vàng: dùng lượt đổi miễn phí để lên 3 sao sớm ở 3-2 (Yunara, Kayle, Teemo, Warwick).",
              "Khi có 3 sao: thắng liên tục là đủ — không cần thua nữa."],
     "tranh": "Vừa thua vừa tiêu vàng roll — mất cả máu lẫn lợi thế của lõi."},
    {"id": "DA_PandorasBench", "vi_sao": "Đầu mỗi vòng 3 ô phải hàng chờ đổi thành tướng ngẫu nhiên cùng giá — máy tìm tướng cho đội reroll.",
     "khi_nao": "2-1 / 3-2",
     "cach": ["Đặt tướng 1–2 vàng thừa ở 3 ô phải hàng chờ để “quay” ra bản sao chủ lực.",
              "Hợp nhất với reroll: Quái Rừng Sỏi (cấp 5), Mặt Trời Yunara, Liên Kích Kayle, Thần Rừng Teemo (cấp 6).",
              "Không đặt tướng đang cần ở 3 ô đó."],
     "tranh": "Đi đội 4 vàng — tướng 4 vàng quay ngẫu nhiên khó trúng."},
    {"id": "DA_StarringUp", "vi_sao": "Đủ số tướng 3 sao thì cấp người chơi được đẩy lên mốc cao + lượt đổi mỗi vòng.",
     "khi_nao": "2-1",
     "cach": ["Đi reroll nhiều tướng rẻ: Mặt Trời Yunara (Karma, LeBlanc, Sejuani, Yunara đều 3 sao), Đao Phủ Azir.",
              "Roll chậm từ 3-1, ưu tiên nâng 3 sao tướng 1–2 vàng trước.",
              "Khi được đẩy cấp: thêm tướng 4–5 vàng hợp tộc."],
     "tranh": "Lên cấp bằng vàng trong khi đang chờ lõi đẩy cấp."},
    {"id": "DA_18_RiftbeastTraitAugment", "vi_sao": "Quái Rừng Omega: thêm 1 Quái Rừng Đầu Đàn + 3 tướng Quái Rừng (18.4: Đầu Đàn thêm 15% Máu, 12% Tốc Độ Đánh).",
     "khi_nao": "2-1 / 3-2 / 4-2",
     "cach": ["Đi Quái Rừng: Sỏi reroll cấp 5 hoặc Quái Rừng Rồng Ngàn Tuổi cấp 8.",
              "Chọn Đầu Đàn là chủ lực (Sỏi, Rồng Ngàn Tuổi) và đỡ đòn chính (Quái Đá).",
              "Quái Rừng 7 tăng ở 18.4 — cố đạt mốc 7 ở cấp 8."],
     "tranh": "Nhận lõi nhưng vẫn ép đội khác — lõi gần như vô dụng ngoài Quái Rừng."},
    {"id": "DA_SpreadingRoots", "vi_sao": "2 Ấn ngẫu nhiên — giống Cây Tộc/Hệ thu nhỏ.",
     "khi_nao": "2-1 (bản + ở 3-2)",
     "cach": ["Bấm 2 Ấn ở trang Trợ lý → Ấn để biết chủ lực nào hợp.",
              "Ấn trùng tộc của chủ lực meta: đeo cho tướng phụ để mở mốc; Ấn tộc tấn công (Đao Phủ, Mặt Trăng, Thợ Săn): đeo cho chủ lực."],
     "tranh": "Ép đội yếu chỉ vì có Ấn — Ấn chỉ là điểm cộng, sức mạnh đội vẫn quan trọng nhất."},
    {"id": "DA_PrismaticTicket", "vi_sao": "Mỗi lần đổi có tỉ lệ được thêm 1 lượt miễn phí — roll nhiều hơn số vàng bỏ ra.",
     "khi_nao": "2-1 / 3-2",
     "cach": ["Hợp mọi đội reroll và đội roll mạnh ở 4-2.", "Roll chậm đều đặn thay vì roll dồn 1 lần."],
     "tranh": "Giữ vàng quá lâu — lõi chỉ có giá trị khi bạn bấm đổi."},
    {"id": "DA_Hustler", "vi_sao": "Không còn lợi tức nhưng mỗi vòng nhận vàng — khuyến khích tiêu vàng liên tục.",
     "khi_nao": "2-1",
     "cach": ["Chơi tempo: tiêu hết vàng mỗi vòng (XP hoặc roll), không giữ mốc 50.",
              "Hợp reroll sớm (Yunara, Kayle, Teemo, Warwick) và lên 8 sớm ở 3-6/4-1."],
     "tranh": "Giữ vàng như bình thường — mất lợi tức mà không dùng được lợi thế."},
]

CAP_LOI = [
    {"loi": ["DA_CalculatedLoss", "DA_PandorasBench"], "doi": "Reroll 1–2 vàng: Mặt Trời Yunara, Liên Kích Kayle, Quái Rừng Sỏi",
     "vi_sao": "Chuỗi thua ra vàng + lượt đổi; Pandora quay hàng chờ ra bản sao → 3 sao ở 3-2 / 3-5."},
    {"loi": ["DA_ExplosiveGrowth", "DA_EpicRolldown"], "doi": "Lên nhanh 8/9: Tiên Phong Alune, Thần Rừng Aphelios / Draven",
     "vi_sao": "XP miễn phí đưa lên 8 ở 4-1, 20 lượt đổi ngay khi lên 8 → chủ lực 4 vàng 2 sao sớm, vàng dư lên 9."},
    {"loi": ["DA_TheTraitTree", "DA_SpreadingRoots"], "doi": "Đội có tộc dọc của chủ lực: Thần Rừng (Aphelios/Kha'Zix), Đao Phủ (Azir), Thuật Sĩ (Ahri/Alune)",
     "vi_sao": "4–5 Ấn → mở mốc cao nhất (Thần Rừng 9, Đao Phủ 4, Thuật Sĩ 5). Dùng trang Ấn để chọn đội."},
    {"loi": ["DA_TacticiansKitchen", "DA_ExplosiveGrowth"], "doi": "Lên 9: Quái Rừng Maokai / Draven",
     "vi_sao": "Cấp 9 + Áo Choàng = 10 tướng: đủ Quái Rừng 7 + tướng 5 vàng."},
    {"loi": ["DA_BaronsLair", "DA_18_RiftbeastTraitAugment"], "doi": "Quái Rừng Rồng Ngàn Tuổi / Maokai",
     "vi_sao": "Quái Rừng lớn dần trong trận + Baron tăng dần sát thương: trận càng dài càng thắng."},
    {"loi": ["DA_Hustler", "DA_StarringUp"], "doi": "Mặt Trời Yunara, Đao Phủ Azir",
     "vi_sao": "Vàng mỗi vòng tiêu hết vào roll → nhiều 3 sao → lõi đẩy cấp."},
    {"loi": ["DA_LatentForge", "DA_18_BranchingOut"], "doi": "Bất kỳ đội meta nào (đồ + Ấn linh hoạt)",
     "vi_sao": "Tạo Tác cho chủ lực + 1 Ấn — cả hai đều hợp mọi đội, giữ được đường chuyển hướng."},
    {"loi": ["DA_PrismaticTicket", "DA_RollingForDays"], "doi": "Reroll 3 vàng: Đao Phủ Azir, Thích Ứng Rengar / Master Yi",
     "vi_sao": "Lượt đổi miễn phí cộng dồn → roll chậm ở cấp 7 mà vẫn giữ lãi."},
]


def doc_tinh_linh() -> list[dict]:
    out = []
    for line in (RAW / "tinh_linh_184b.txt").read_text(encoding="utf-8").splitlines():
        p = [x.strip() for x in line.split("¦")]
        if len(p) < 7:
            continue
        hang, nhom, en, vi, gia, khoang, mo_ta = p[:7]
        tu, den = khoang.split("→")
        out.append({"hang": hang, "nhom": NHOM.get(nhom, nhom), "ten_en": en, "ten": vi, "tam_dich": en in DICH_TAM,
                    "gia": int(gia) if gia else None, "tu": tu, "den": den, "mo_ta": mo_ta})
    return out


def main():
    obj = {
        "phien_ban": "18.4b",
        "nguon": [
            {"ten": "MetaTFT – mốc lên cấp & đội hình (Bạch Kim+, 3 ngày, 18.4b)", "url": "https://www.metatft.com/comps"},
            {"ten": "MetaTFT – bảng lõi (chuyên gia)", "url": "https://www.metatft.com/augments"},
            {"ten": "MetaTFT – Wisp Tier List (bùa / Tinh Linh)", "url": "https://www.metatft.com/wisp-tiers"},
            {"ten": "OP.GG – đội hình máy chủ VN 18.4b", "url": "https://op.gg/tft/meta-trends/comps?region=vn"},
            {"ten": "tactics.tools – thống kê 18.4b (Kim Cương+)", "url": "https://tactics.tools/augments"},
        ],
        "ghi_chu_loi": ("Các trang thống kê (MetaTFT, tactics.tools) hiện không có số liệu thắng/thua theo lõi cho bản 18.4b, "
                        "nên “lõi top 1” lấy từ bảng xếp hạng chuyên gia (MetaTFT, bậc S) và “cặp lõi” là nhận định theo "
                        "cơ chế của lõi — không phải số liệu."),
        "tempo": TEMPO,
        "loi_top1": LOI_TOP1,
        "cap_loi": CAP_LOI,
        "tinh_linh": doc_tinh_linh(),
        "ghi_chu_tinh_linh": ("Bùa = Tinh Linh bán trong cửa hàng. Bậc S/A theo chuyên gia MetaTFT (20/10/2026). "
                              "“Từ → đến” là khoảng vòng Tinh Linh có thể xuất hiện. Tên có dấu * là tên tạm dịch "
                              "(dữ liệu game chưa có tên tiếng Việt)."),
    }
    for d in (ROOT / "data" / "ban" / "18.4b", ROOT / "data"):
        (d / "cam_nang.json").write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(obj["loi_top1"]), "lõi top 1,", len(obj["cap_loi"]), "cặp lõi,", len(obj["tinh_linh"]), "Tinh Linh")


if __name__ == "__main__":
    main()
