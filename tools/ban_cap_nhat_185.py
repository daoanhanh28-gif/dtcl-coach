# ĐTCL Coach v1.4 (2026-10-22) — danh sách thay đổi bản 18.5 theo ghi chú CHÍNH THỨC của Riot → data/ban_cap_nhat.json
"""Chạy: python tools/ban_cap_nhat_185.py  (viết tay từ ghi chú bản vá; muc 0,5 = chỉnh nhỏ, moc = mốc tộc/hệ bị đổi)"""
import json
from pathlib import Path

T = lambda ten, huong, ct, muc=1: {"loai": "tuong", "ten": ten, "huong": huong, "chi_tiet": ct, "muc": muc}
H = lambda ten, huong, ct, moc, muc=1: {"loai": "toc_he", "ten": ten, "huong": huong, "chi_tiet": ct, "moc": moc, "muc": muc}
L = lambda ten, huong, ct: {"loai": "loi", "ten": ten, "huong": huong, "chi_tiet": ct}
B = lambda ten, huong, ct: {"loai": "tinh_linh", "ten": ten, "huong": huong, "chi_tiet": ct}

THAY_DOI = [
    T("Tristana", "tang", "Năng Lượng 0/60 → 0/50 · sát thương mỗi đòn 10/15/25 → 12/18/28"),
    T("Sivir", "tang", "Sát thương kỹ năng 200/300 → 220/330 (sát thương nảy 20% → 18%)"),
    T("Master Yi", "tang", "SMCK dạng AD 60 → 63 · sát thương phép dạng AP 125/190/285 → 135/200/320"),
    T("Morgana", "tang", "Sát thương nguyền ban đầu 60/90 → 70/105 · cộng thêm 22/33 → 25/38"),
    T("Taric", "tang", "Giáp & Kháng Phép 65 → 70 · 2 đòn cường hóa 100/150 → 130/200"),
    T("Alune", "tang", "Mảnh Trăng 55/83 → 58/88 · Tốc Độ Đánh 0.8 → 0.85 (Chống Chịu tộc riêng 7% → 5%)"),
    T("Ashe", "tang", "Sát thương mỗi giây 9/14 → 11/16"),
    T("Sett", "tang", "Hồi máu 225/275 → 250/300"),
    T("Bụi Gai Đỏ", "tang", "Hồi máu dấu Đầu Đàn 4% → 5% · xuyên Giáp 20% → 25%"),
    T("Caitlyn", "tang", "Đòn cường hóa 190/285/470 → 200/300/490", 0.5),
    T("Soraka", "tang", "Sao đầu 225/335 → 235/355 · sao thêm 100/150 → 110/165", 0.5),
    T("Malphite", "tang", "Lá chắn 700/850 → 735/885", 0.5),
    T("Azir", "giam", "Lính Cát 46/69/110 → 43/65/105"),
    T("Kha'Zix", "giam", "Sát thương 255/360/515 → 250/345/500 (khi cô lập 285/410/605 → 280/390/590)", 0.5),
    T("Mama Beak", "giam", "Mỗi đòn 22/33/52 → 20/30/50 · khóa Năng Lượng ngắn hơn ~1 giây", 0.5),
    T("Sentinel", "dieu_chinh", "Choáng 1 → 0,5 giây · lá chắn 350/450 → 375/475"),
    H("Tiên Linh", "tang", "Hồi máu mốc 2/4: 2,5/4% → 3/5% · mốc Pix 4/5/6 cần ít hơn (30k/70k/110k → 25k/60k/100k)", 2),
    H("Liên Kích", "giam", "Tốc Độ Đánh mỗi đòn 3/5/8/12% → 3/5/7/10%", 4),
    H("Quái Rừng", "giam", "Mốc 7: SMCK/SMPT 6% → 5%", 7),
    H("Gai Đen", "giam", "Mốc 6: 60% → 50% · khuếch đại khi hiến tế 12% → 10%", 2, 0.5),
    H("Thần Rừng", "giam", "Mốc 9: Máu cây 140% → 125%", 9),
    H("Thực Vật", "giam", "Hồi Máu tối đa 8% → 7%", 1, 0.5),
    L("Hóa Lớn", "tang", "Chỉ số nhận ngay 10% → 18%"),
    L("Thực Vật Hấp Thụ", "tang", "Hiệu ứng thêm 50% → 70%"),
    L("Ân Huệ Thách Đấu", "tang", "Tốc Độ Đánh 25% → 30%"),
    L("Tự Lập Đội", "tang", "Vàng 6 → 9"),
    L("Dòng Tiền Mờ Ám", "tang", "Vàng 4 → 6"),
    L("Gói Trang Bị Bất Ngờ", "tang", "Vàng 4 → 6"),
    L("Kiên Nhẫn Là Một Đức Tính", "tang", "Lượt đổi 4 → 5"),
    L("Nồi Nấu Ăn", "tang", "Máu mỗi Ấn 60 → 70 (không còn đi kèm Đăng Quang, Cắm Rễ Phân Tán+, Cây Tộc/Hệ+)"),
    L("Hàng Chờ Pandora", "giam", "Vàng 4 → 1"),
    L("Hộp Pandora II", "giam", "Vàng 4 → 1 · thêm bản + (3-2, 4 vàng) và ++ (4-2, 6 vàng)"),
    L("Chiến Thuật Đầu Tư I", "giam", "Vàng ngay 6 → 3"),
    L("Chiến Thuật Đầu Tư II", "giam", "Vàng ngay 10 → 6"),
    L("Vận Mệnh Kim Cương", "giam", "Vàng 4 → 2"),
    L("Quái Rừng Omega", "giam", "Đầu Đàn thêm Máu và Tốc Độ Đánh 10% → 8%"),
    L("Tà Thuật", "giam", "SMPT các mốc đầu 7/12/33/50/100 → 5/10/28/45/85"),
    L("Kỳ Vọng Bất Ngờ", "giam", "Vàng giai đoạn 3/4: 18/20 → 15/18 · giai đoạn 4 còn 2 tướng 5 vàng (+3 vàng)"),
    L("Trượng Đại Thiên Sứ", "giam", "Ngưỡng SMPT 90% → 110%"),
    L("Thệ Ước Bảo Hộ", "giam", "Máu 200 → 175"),
    L("Lệ Lưu Ly", "giam", "Năng Lượng cần tiêu 6.500 → 7.000"),
    L("Giọt Lệ Bi Ai", "giam", "Hồi Năng Lượng 4 → 3"),
    L("Tất Tay Bậc Đồng II", "giam", "Giáp & Kháng Phép mỗi tộc/hệ 3 → 2,5"),
    L("U.R.F.", "dieu_chinh", "Không còn xuất hiện cùng Đăng Quang, Cắm Rễ Phân Tán (+), Cây Tộc/Hệ (+)"),
    L("Chiết Xuất Trang Bị", "dieu_chinh", "Không còn tặng Veigar"),
    L("Trái Tim Sắt Đá", "dieu_chinh", "Lại bị tạm tắt vì lỗi"),
    {"loai": "he_thong", "ten": "Lõi theo hướng đồ", "huong": "moi",
     "chi_tiet": "Lõi dành riêng cho đội vật lý (AD) ít xuất hiện hơn khi bạn đang đi đội phép (AP) và ngược lại"},
    {"loai": "trang_bi", "ten": "Mũ Thích Nghi (Ánh Sáng)", "huong": "giam", "chi_tiet": "Hồi Năng Lượng 7 → 6 · SMCK/SMPT cho tướng không đỡ đòn 40 → 35"},
    {"loai": "trang_bi", "ten": "Bùa Xanh (Ánh Sáng)", "huong": "giam", "chi_tiet": "SMCK/SMPT 30% → 25%"},
    B("Hand of Baron", "dieu_chinh", "Giá 6 → 4 vàng, chỉ số giảm khoảng 1/3"),
    B("Heroic Sacrifice", "giam", "Máu 1.200/1.500 → 1.000/1.250"),
    B("Beggar's Wisp", "giam", "Vàng 3/5 → 2/3"),
    B("Abandon Ship", "giam", "Giá 0 → 2 vàng"),
    B("Blood and Iron", "giam", "Giá 3 → 4 vàng (sửa lỗi)"),
    B("Returning Friend · Grove Armor", "moi", "Có thể xuất hiện từ giai đoạn 3"),
]

OBJ = {
    "phien_ban": "18.5",
    "ngay": "21/10/2026",
    "ban_dang_chay": "18.5",
    "nguon": ("Ghi chú bản 18.5 chính thức của Riot (21/10/2026) · thống kê MetaTFT 18.5 (Bạch Kim+, ~1,8 triệu đội hình, 22/10) "
              "· OP.GG máy chủ VN 18.5 (32.640 ván / 24 giờ, 22/10)"),
    "nguon_link": [
        {"ten": "Riot – ghi chú bản 18.5", "url": "https://teamfighttactics.leagueoflegends.com/en-us/news/game-updates/teamfight-tactics-patch-18-5/"},
        {"ten": "esports.gg – 18.5", "url": "https://esports.gg/news/teamfight-tactics/tft-patch-18-5/"},
        {"ten": "MetaTFT – đội hình 18.5", "url": "https://www.metatft.com/comps"},
        {"ten": "OP.GG – máy chủ VN 18.5", "url": "https://op.gg/tft/meta-trends/comps?region=vn"},
    ],
    "ghi_chu": ("Bản 18.5 đã chạy trên máy chủ VN từ 21/10/2026. So với bản xem trước: Sivir, Bụi Gai Đỏ, Alune, Taric được tăng thêm, "
                "Tristana được giảm Năng Lượng; Draven và Nidalee không bị đổi; không có luật giới hạn nhóm lõi mà thay bằng "
                "lõi theo hướng đồ AD/AP. Số liệu 18.5 mới ~1 ngày — VN mới đủ mẫu cho 7 đội, nên dùng thêm số quốc tế MetaTFT."),
    "ban_truoc": [
        {"k": "18.4 (10/10)", "v": "Hoa Linh 4, Mặt Trăng, Quái Rừng 7, Tinh Nghịch 7 tăng · Đao Phủ, Tiên Linh, Dũng Sĩ, Tiên Hắc Ám giảm · Ashe, Kennen, Veigar, Rammus giảm · Draven, Ezreal, Sivir, Tristana, Rengar, Teemo tăng."},
        {"k": "18.4b (07–10/10)", "v": "Trả lại phần lớn số của 18.3 cho Alistar, Gromp, Warwick, Sói Hắc Ám, Varus, Camille · Ân Huệ Thách Đấu, Giữ Vững Hàng Ngũ, Ôm Tập Thể, To Lớn & Mạnh Mẽ tăng."},
    ],
    "thay_doi": THAY_DOI,
}

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    (root / "data" / "ban_cap_nhat.json").write_text(json.dumps(OBJ, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(THAY_DOI), "thay đổi")
